#!/usr/bin/env python3
"""Host-side stand-in for the NBT EVO's V850 IOC on the MOST SIPC link.

The guest's native MOST daemon (/opt/sys/bin/most --devmode=client) talks to the IOC over SIPC.
bimmulator forwards that TCP stream to the host (IDRIVE_MOST_SIPC_HOST_PORT). This server accepts
it, logs every telegram as JSON lines, and answers with the rules in rules.py (hot-reloaded, so
replies can be developed while the emulator keeps running).

Wire format (bimmulator tools/kombi_sipc.py): u32 length, then header
  <IIIHHBBHB3xI = transmission, variant, info, dst, src, fblock, instance, function, operation, tag
followed by the payload, padded to 4 bytes.

usage: ioc_sim.py [--port 8766] [--log $IDRIVE_HOME/ioc.jsonl]
"""
import os
import argparse
import importlib
import json
import socket
import struct
import sys
import threading
import time
from pathlib import Path

LENGTH = struct.Struct("<I")
HEADER = struct.Struct("<IIIHHBBHB3xI")
FIELDS = ("transmission", "variant", "info", "dst", "src", "fblock", "instance", "function",
          "operation", "tag")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def read_exact(conn, size):
    data = b""
    while len(data) < size:
        chunk = conn.recv(size - len(data))
        if not chunk:
            return None
        data += chunk
    return data


def encode(msg):
    body = HEADER.pack(*(msg[f] for f in FIELDS)) + msg["payload"]
    return LENGTH.pack(len(body)) + body + bytes(-len(body) % 4)


class Session:
    def __init__(self, conn, log):
        self.conn = conn
        self.log = log
        self.lock = threading.Lock()
        self.state = {}
        self.t0 = time.time()

    def record(self, direction, msg):
        entry = {"t": round(time.time() - self.t0, 3), "dir": direction,
                 **{f: msg[f] for f in FIELDS}, "payload": msg["payload"].hex()}
        self.log.write(json.dumps(entry) + "\n")
        self.log.flush()

    def send(self, **msg):
        base = {"transmission": 0, "variant": 0, "info": 0, "dst": 0, "src": 0, "fblock": 0,
                "instance": 0, "function": 0, "operation": 0, "tag": 0, "payload": b""}
        base.update(msg)
        with self.lock:
            self.conn.sendall(encode(base))
        self.record("ioc", base)


def load_rules():
    try:
        import rules
        return importlib.reload(rules)
    except Exception as error:  # keep serving with logging only
        print(f"rules.py not loaded: {error}", flush=True)
        return None


def serve(conn, log):
    session = Session(conn, log)
    rules = load_rules()
    mtime = (HERE / "rules.py").stat().st_mtime if (HERE / "rules.py").exists() else 0
    if rules and hasattr(rules, "on_connect"):
        rules.on_connect(session)
    while True:
        raw = read_exact(conn, LENGTH.size)
        if raw is None:
            break
        size, = LENGTH.unpack(raw)
        frame = read_exact(conn, size + (-size % 4))
        if frame is None:
            break
        msg = dict(zip(FIELDS, HEADER.unpack_from(frame)))
        msg["payload"] = frame[HEADER.size:size]
        session.record("hu", msg)
        new_mtime = (HERE / "rules.py").stat().st_mtime if (HERE / "rules.py").exists() else 0
        if new_mtime != mtime:
            rules, mtime = load_rules(), new_mtime
        if rules and hasattr(rules, "on_message"):
            try:
                rules.on_message(session, msg)
            except Exception as error:
                print(f"rule error: {error!r}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--log", default=str(Path(os.environ.get("IDRIVE_HOME", Path.home() / "idrive")) / "ioc.jsonl"))
    args = parser.parse_args()
    server = socket.create_server(("127.0.0.1", args.port), reuse_port=True)
    print(f"IOC sim listening on 127.0.0.1:{args.port}", flush=True)
    with open(args.log, "a") as log:
        while True:
            conn, _ = server.accept()
            print("HU connected", flush=True)
            log.write(json.dumps({"event": "connect", "time": time.time()}) + "\n")
            try:
                serve(conn, log)
            except OSError as error:
                print(f"link error: {error}", flush=True)
            finally:
                conn.close()
                print("HU disconnected", flush=True)


if __name__ == "__main__":
    main()
