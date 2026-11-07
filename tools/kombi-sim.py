#!/usr/bin/env python3
"""Host-side vehicle state and modeled 6WB displays."""

import argparse
import json
import math
import threading
from contextlib import ExitStack
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from kombi_rpm import open_rpm_mailbox, write_rpm, write_speed
from kombi_sipc import MAX_PAYLOAD, Message, SIPCServer


INITIAL = {
    "ignition": True,
    "speed_kph": 0,
    "engine_rpm": 800,
    "gear": "P",
    "mode": "comfort",
    "fuel_pct": 76,
    "temperature_c": 90,
    "speed_limit_kph": None,
    "guidance": None,
    "media_title": "",
}
LIMITS = {
    "speed_kph": (0, 400),
    "engine_rpm": (0, 12000),
    "fuel_pct": (0, 100),
    "temperature_c": (-40, 180),
    "speed_limit_kph": (5, 250),
    "distance_m": (0, 1000000),
}
CHOICES = {
    "gear": {"P", "R", "N", "D", "M", *map(str, range(1, 10))},
    "mode": {"comfort", "sport", "eco"},
    "turn": {"left", "right", "straight", "uturn"},
}
MAX_BODY = 8192


def validate(name, value):
    if name in LIMITS:
        minimum, maximum = LIMITS[name]
        if type(value) not in (int, float) or not minimum <= value <= maximum:
            raise ValueError(f"{name} must be between {minimum} and {maximum}")
    elif name in CHOICES:
        if not isinstance(value, str) or value not in CHOICES[name]:
            raise ValueError(f"invalid {name}")
    elif name == "ignition" and type(value) is not bool:
        raise ValueError("ignition must be a boolean")
    elif name in {"road", "media_title"}:
        if not isinstance(value, str) or len(value) > 120:
            raise ValueError(f"{name} must be a string of at most 120 characters")
    return value


def vehicle_patch(patch):
    if not isinstance(patch, dict) or not patch or patch.keys() - INITIAL.keys():
        raise ValueError("send a nonempty object containing known vehicle fields")
    values = {}
    for name, value in patch.items():
        if name in {"guidance", "speed_limit_kph"} and value is None:
            values[name] = None
        elif name == "guidance":
            if not isinstance(value, dict) or value.keys() != {"turn", "distance_m", "road"}:
                raise ValueError("guidance requires turn, distance_m, and road")
            values[name] = {key: validate(key, item) for key, item in value.items()}
        else:
            values[name] = validate(name, value)
    return values


class Vehicle:
    def __init__(self, mailbox=None):
        self._lock = threading.Lock()
        self._state = INITIAL.copy()
        self._revision = 0
        self._mailbox = mailbox
        if mailbox is not None:
            write_rpm(mailbox, self._state["engine_rpm"])
            write_speed(mailbox, self._state["speed_kph"])

    def snapshot(self):
        with self._lock:
            return {"revision": self._revision, **self._state}

    def detach_mailbox(self):
        with self._lock:
            self._mailbox = None

    def update(self, patch):
        values = vehicle_patch(patch)
        with self._lock:
            if self._mailbox is not None:
                if "engine_rpm" in values:
                    write_rpm(self._mailbox, values["engine_rpm"])
                if "speed_kph" in values:
                    write_speed(self._mailbox, values["speed_kph"])
            self._state.update(values)
            self._revision += 1
            return {"revision": self._revision, **self._state}


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, data, content_type="application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def json(self, status, value):
        self.respond(status, json.dumps(value, ensure_ascii=True).encode())

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == "/api/v1/vehicle":
            self.json(HTTPStatus.OK, self.server.vehicle.snapshot())
        elif url.path == "/api/v1/most" and self.server.sipc:
            try:
                after = int(parse_qs(url.query).get("after", ["0"])[0])
            except ValueError:
                self.json(HTTPStatus.BAD_REQUEST, {"error": "after must be a sequence number"})
                return
            self.json(HTTPStatus.OK, self.server.sipc.status(after))
        elif url.path in {"/", "/cluster", "/hud"}:
            self.respond(HTTPStatus.OK, self.server.display, "text/html; charset=utf-8")
        else:
            self.json(HTTPStatus.NOT_FOUND, {"error": "unknown route"})

    def do_POST(self):
        most = self.path == "/api/v1/most" and self.server.sipc
        if self.path != "/api/v1/vehicle" and not most:
            self.json(HTTPStatus.NOT_FOUND, {"error": "unknown route"})
            return
        if self.headers.get_content_type() != "application/json":
            self.json(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"error": "use application/json"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            maximum = 2 * MAX_PAYLOAD + MAX_BODY if most else MAX_BODY
            if not 0 < size <= maximum:
                raise ValueError(f"body must contain 1 to {maximum} bytes")
            self.connection.settimeout(3)
            body = self.rfile.read(size)
            if len(body) != size:
                raise ValueError("incomplete request body")
            data = json.loads(body)
            if most:
                most.send(Message.from_json(data))
                snapshot = {"sent": True}
            else:
                snapshot = self.server.vehicle.update(data)
        except (ValueError, TimeoutError, RecursionError) as error:
            self.json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return
        except OSError as error:
            self.json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": str(error)})
            return
        self.json(HTTPStatus.OK, snapshot)

    def log_message(self, _format, *args):
        if len(args) >= 2 and str(args[1]) == "200":
            return
        super().log_message(_format, *args)


def demo(vehicle, stopped):
    vehicle.update({"gear": "D", "speed_limit_kph": 80,
                    "guidance": {"turn": "right", "distance_m": 650, "road": "Park Avenue"}})
    tick = 0
    while not stopped.wait(0.1):
        speed = 65 + 26 * math.sin(tick * 0.03)
        vehicle.update({"speed_kph": round(speed, 1), "engine_rpm": round(850 + speed * 38),
                        "guidance": {"turn": "right", "distance_m": 650 - tick % 300 * 2,
                                     "road": "Park Avenue"}})
        tick += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--demo", action="store_true", help="generate a looping vehicle feed")
    parser.add_argument("--sipc-port", type=int, help="accept the native MOST daemon on this loopback port")
    parser.add_argument("--vehicle-ram", "--rpm-ram", type=Path,
                        help="send speed and RPM to the GSS probe's shared RAM file")
    args = parser.parse_args()
    stopped = threading.Event()
    with ExitStack() as cleanup:
        server = cleanup.enter_context(ThreadingHTTPServer(("127.0.0.1", args.port), Handler))
        mailbox = cleanup.enter_context(open_rpm_mailbox(args.vehicle_ram)) if args.vehicle_ram else None
        server.vehicle = Vehicle(mailbox)
        cleanup.callback(server.vehicle.detach_mailbox)
        server.sipc = None
        server.display = Path(__file__).with_name("kombi-sim.html").read_bytes()
        if args.sipc_port is not None:
            sipc = cleanup.enter_context(SIPCServer(args.sipc_port))
            server.sipc = sipc.link
            threading.Thread(target=sipc.serve_forever, daemon=True).start()
            cleanup.callback(sipc.shutdown)
            cleanup.callback(sipc.link.close)
            print(f"MOST SIPC listening on 127.0.0.1:{sipc.server_address[1]}", flush=True)
        print(f"6WB simulator at http://127.0.0.1:{server.server_port}/", flush=True)
        if args.demo:
            demo_thread = threading.Thread(target=demo, args=(server.vehicle, stopped), daemon=True)
            demo_thread.start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            stopped.set()
            if args.demo:
                demo_thread.join()


if __name__ == "__main__":
    main()
