#!/usr/bin/env python3
"""WSL2 port helper for the pre-starter snapshot.

  wsl-snapshot.py save   <run_dir> [name]   wait for the guest's rootfs-ready hold, unplug the
                                            non-migratable usb-net, savevm, plug it back
  wsl-snapshot.py resume <run_dir>          after a ``-loadvm`` start, plug usb-net back in

The snapshot is taken after root extraction and before starter, when the guest has not started
its network stack yet, so unplugging and re-plugging the USB network adapter is invisible to it.
"""
from __future__ import annotations

import json
import socket
import sys
import time
from pathlib import Path

MARKER = b"Rootfs-ready snapshot window"
USBNET = {"driver": "usb-net", "id": "idrive-usbnet", "bus": "usb-bus.0", "netdev": "idrive-net"}


class Qmp:
    def __init__(self, path: Path):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(str(path))
        self.stream = self.sock.makefile("rwb")
        self.stream.readline()
        self.events: list = []
        self.call("qmp_capabilities")

    def call(self, command: str, **arguments) -> dict:
        message = {"execute": command}
        if arguments:
            message["arguments"] = arguments
        self.stream.write((json.dumps(message) + "\n").encode())
        self.stream.flush()
        while True:
            reply = json.loads(self.stream.readline())
            if "event" in reply:
                self.events.append(reply)
                continue
            if "error" in reply:
                raise RuntimeError(f"{command}: {reply['error']}")
            return reply

    def wait_event(self, name: str, timeout: float) -> None:
        deadline = time.time() + timeout
        if any(e.get("event") == name for e in self.events):
            return
        self.sock.settimeout(timeout)
        while time.time() < deadline:
            reply = json.loads(self.stream.readline())
            if reply.get("event") == name:
                return
        raise TimeoutError(name)

    def hmp(self, line: str) -> str:
        output = self.call("human-monitor-command", **{"command-line": line}).get("return", "")
        if "Error" in output:
            raise RuntimeError(output.strip())
        return output


def wait_for(path: Path, predicate, timeout: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate(path):
            return True
        time.sleep(0.5)
    return False


def save(run_dir: Path, name: str) -> int:
    serial = run_dir / "serial.log"
    if not wait_for(serial, lambda p: p.exists() and MARKER in p.read_bytes(), 1200):
        print("SNAPSHOT_FAIL hold marker not seen", flush=True)
        return 1
    qmp = Qmp(run_dir / "qmp.sock")
    started = time.time()
    qmp.call("device_del", id="idrive-usbnet")
    qmp.wait_event("DEVICE_DELETED", 10)
    qmp.hmp(f"savevm {name}")
    qmp.call("device_add", **USBNET)
    print(f"SNAPSHOT_OK name={name} seconds={time.time() - started:.1f}", flush=True)
    return 0


def resume(run_dir: Path) -> int:
    sock = run_dir / "qmp.sock"
    if not wait_for(sock, lambda p: p.exists(), 120):
        print("RESUME_FAIL no QMP socket", flush=True)
        return 1
    for _ in range(60):
        try:
            qmp = Qmp(sock)
            break
        except OSError:
            time.sleep(0.5)
    else:
        print("RESUME_FAIL QMP not answering", flush=True)
        return 1
    qmp.call("device_add", **USBNET)
    print("RESUME_OK usb-net plugged", flush=True)
    return 0


def main() -> int:
    mode, run_dir = sys.argv[1], Path(sys.argv[2])
    if mode == "save":
        return save(run_dir, sys.argv[3] if len(sys.argv) > 3 else "prestarter")
    if mode == "resume":
        return resume(run_dir)
    print("usage: wsl-snapshot.py save|resume <run_dir> [name]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
