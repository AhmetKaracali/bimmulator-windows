#!/usr/bin/env python3
"""WSL2 port helper: take the pre-starter snapshot during a running emulator boot.

Run while the emulator boots with IDRIVE_ROOTFS_READY_HOLD_SECONDS and IDRIVE_QEMU_STATE_FILE
set. Waits for the guest's "Rootfs-ready snapshot window" serial line, then saves the VM state
with QMP ``savevm`` so later boots can skip QNX start-up and root extraction.

Usage: wsl-snapshot.py <run_dir> [snapshot_name]
"""
from __future__ import annotations

import json
import socket
import sys
import time
from pathlib import Path

MARKER = b"Rootfs-ready snapshot window"


def qmp_command(sock_path: Path, command: dict) -> dict:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(str(sock_path))
        stream = sock.makefile("rwb")
        stream.readline()
        for message in ({"execute": "qmp_capabilities"}, command):
            stream.write((json.dumps(message) + "\n").encode())
            stream.flush()
            while True:
                reply = json.loads(stream.readline())
                if "return" in reply or "error" in reply:
                    break
        return reply


def main() -> int:
    run_dir = Path(sys.argv[1])
    name = sys.argv[2] if len(sys.argv) > 2 else "prestarter"
    serial = run_dir / "serial.log"
    deadline = time.time() + 1200
    while time.time() < deadline:
        if serial.exists() and MARKER in serial.read_bytes():
            break
        time.sleep(1)
    else:
        print("SNAPSHOT_FAIL marker not seen", flush=True)
        return 1
    started = time.time()
    reply = qmp_command(run_dir / "qmp.sock",
                        {"execute": "human-monitor-command", "arguments": {"command-line": f"savevm {name}"}})
    output = reply.get("return", "") if isinstance(reply.get("return"), str) else ""
    if "error" in reply or "Error" in output:
        print(f"SNAPSHOT_FAIL {reply}", flush=True)
        return 1
    print(f"SNAPSHOT_OK name={name} seconds={time.time() - started:.1f}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
