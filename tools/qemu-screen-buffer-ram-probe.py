#!/usr/bin/env python3
"""Verify host writes into a live hidden QNX Screen buffer via shared QEMU RAM."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import socket
import time


HOLD_MESSAGE = "Holding the hidden Screen allocation for 15 seconds for host RAM inspection"


def qmp_read_physical(socket_path: Path, address: int, size: int) -> str:
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.settimeout(3)
    connection.connect(str(socket_path))
    stream = connection.makefile("rwb", buffering=0)

    def read_message() -> dict[str, object]:
        while True:
            line = stream.readline()
            if not line:
                raise ConnectionError("QEMU closed its QMP socket")
            message = json.loads(line)
            if "event" not in message:
                return message

    try:
        read_message()  # QMP greeting
        stream.write(b'{"execute":"qmp_capabilities","id":"caps"}\r\n')
        while read_message().get("id") != "caps":
            pass
        command = f"xp/{size}xb 0x{address:x}"
        request = {
            "execute": "human-monitor-command",
            "arguments": {"command-line": command},
            "id": "physical-read",
        }
        stream.write((json.dumps(request) + "\r\n").encode("utf-8"))
        while True:
            response = read_message()
            if response.get("id") == "physical-read":
                if "error" in response:
                    raise RuntimeError(f"QMP physical read failed: {response['error']}")
                return str(response.get("return", ""))
    finally:
        connection.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ram-file", type=Path, required=True)
    parser.add_argument("--serial-log", type=Path, required=True)
    parser.add_argument("--qmp-socket", type=Path, required=True)
    parser.add_argument("--ram-base", type=lambda value: int(value, 0), default=0x80000000)
    parser.add_argument("--wait-seconds", type=int, default=600)
    parser.add_argument("--marker", default="ID6RAM!!")
    args = parser.parse_args()

    marker = args.marker.encode("ascii")
    if not marker or len(marker) > 32:
        parser.error("marker must contain 1 to 32 ASCII bytes")
    if args.wait_seconds < 0:
        parser.error("wait-seconds cannot be negative")

    deadline = time.monotonic() + args.wait_seconds
    address = None
    while time.monotonic() <= deadline:
        if args.serial_log.exists():
            log = args.serial_log.read_bytes().replace(b"\0", b"").decode("utf-8", "replace")
            hold_at = log.find(HOLD_MESSAGE)
            if hold_at >= 0:
                if "HMI Screen contract probe complete; this is not an HMI frame" in log[hold_at:]:
                    raise SystemExit("Screen probe already released its buffers; restart it and run this tool during the hold")
                addresses = re.findall(r"buffer physical address=0x([0-9a-fA-F]+)", log)
                if addresses:
                    address = int(addresses[0], 16)
                    break
        time.sleep(0.05)
    if address is None:
        raise SystemExit("timed out waiting for the hidden Screen allocation hold")
    offset = address - args.ram_base
    if offset < 0 or offset + len(marker) > args.ram_file.stat().st_size:
        raise SystemExit("Screen buffer address is outside the shared RAM file")

    with args.ram_file.open("r+b", buffering=0) as ram:
        ram.seek(offset)
        ram.write(marker)
        ram.flush()

    qemu_output = qmp_read_physical(args.qmp_socket, address, len(marker))
    guest_bytes = bytes(int(value, 16) for value in re.findall(r"0x([0-9a-fA-F]{2})", qemu_output))
    with args.ram_file.open("rb") as ram:
        ram.seek(offset)
        file_bytes = ram.read(len(marker))

    print(f"Screen buffer physical address: 0x{address:x}")
    print(f"Shared RAM file offset: 0x{offset:x}")
    print(f"Host wrote marker: {marker!r}")
    print(f"QEMU physical read: {qemu_output.strip()}")
    print(f"Shared-file readback: {file_bytes!r}")
    if guest_bytes != marker or file_bytes != marker:
        raise SystemExit("host marker was not observed through both QEMU and the shared file")
    print("PASS: host write is visible in QEMU RAM at the live Screen buffer address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
