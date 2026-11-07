#!/usr/bin/env python3
"""Upload a small development helper through an existing QNX ksh console.

Uses acknowledged octal writes and binary readback with SHA-256. A temporary
noninteractive ksh avoids the slow per-character line editor. No guest TCP,
decoder utility, raw input mode or emulator reboot is required.
The QEMU UART socket must have no other connected console client.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import re
import shlex
import socket
import time
import uuid


class Console:
    def __init__(self, connection: socket.socket, timeout: float):
        self.connection = connection
        self.timeout = timeout
        self.buffer = bytearray()

    def send(self, command: str) -> None:
        self.connection.sendall(command.encode("ascii") + b"\n")

    def more(self, deadline: float) -> None:
        if time.monotonic() >= deadline:
            raise TimeoutError("QNX console did not acknowledge the operation")
        try:
            chunk = self.connection.recv(65536)
        except socket.timeout:
            return
        if not chunk:
            raise ConnectionError("QEMU closed its serial socket")
        self.buffer.extend(chunk)
        if len(self.buffer) > 2 * 1024 * 1024:
            raise RuntimeError("console output exceeded the bounded receive buffer")

    def marker(self, marker: str) -> None:
        pattern = re.compile(rb"(?:^|\n)" + re.escape(marker.encode("ascii")) + rb"\r*\n")
        deadline = time.monotonic() + self.timeout
        while True:
            match = pattern.search(self.buffer)
            if match:
                del self.buffer[:match.end()]
                return
            self.more(deadline)

    def exact(self, size: int) -> bytes:
        # Bulk readback can take longer than a short command acknowledgement on
        # an emulated UART. Retain a bounded allowance proportional to payload.
        deadline = time.monotonic() + max(self.timeout, size / 64)
        while len(self.buffer) < size:
            self.more(deadline)
        result = bytes(self.buffer[:size])
        del self.buffer[:size]
        return result

    def acknowledged(self, command: str, token: str) -> None:
        self.send(command + " && echo && echo " + token)
        self.marker(token)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination")
    args = parser.parse_args()
    destination = PurePosixPath(args.destination)
    if not str(destination).startswith("/dev/shmem/") or ".." in destination.parts:
        parser.error("development uploads must target a file below /dev/shmem")
    data = args.source.read_bytes()
    if not data or len(data) > 256 * 1024:
        parser.error("source must contain 1 to 262144 bytes")
    quoted = shlex.quote(str(destination))
    nonce = "ID6" + uuid.uuid4().hex[:12]
    setup = "id6_uart_saved=$(/bin/stty -g) && /bin/stty -echo && : > " + quoted + " && /bin/chmod 600 " + quoted
    data_prefix = "print -n '"
    data_suffix = "' >> " + quoted
    acknowledgement_suffix = " && echo && echo " + nonce + "_99999"
    chunk_size = min(
        48,
        (240 - len(data_prefix) - len(data_suffix) - len(acknowledgement_suffix)) // 5,
    )
    if chunk_size < 1:
        parser.error("destination path leaves no room for an acknowledged data byte")
    sample = data_prefix + "\\0377" * chunk_size + data_suffix + acknowledgement_suffix
    if len(setup) > 240 or len(sample) > 240:
        parser.error("destination path is too long for bounded canonical-console lines")
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.settimeout(0.5)
    connection.connect(str(args.socket))
    console = Console(connection, args.timeout)
    child_started = False
    started = time.monotonic()
    try:
        # The marker is emitted by the child before it starts reading commands;
        # do not race the parent's terminal input/read-ahead with the first write.
        child_marker = nonce + "_SHELL"
        # QNX ksh automatically enables interactive mode when both stdin and
        # stderr are terminals, even with +i. Redirect stderr so its documented
        # startup condition is false; stdout remains the acknowledged channel.
        console.send("\n/boot/bin/ksh -c 'echo; echo " + child_marker + "; exec /boot/bin/ksh' 2>/dev/shmem/id6-upload.err")
        console.marker(child_marker)
        child_started = True
        console.acknowledged("\n" + setup, nonce + "_PREPARED")
        for index, offset in enumerate(range(0, len(data), chunk_size)):
            encoded = "".join(f"\\0{byte:03o}" for byte in data[offset:offset + chunk_size])
            console.acknowledged("print -n '" + encoded + "' >> " + quoted, nonce + "_" + str(index))
            if index % 16 == 0:
                print(f"Uploaded {min(offset + chunk_size, len(data))}/{len(data)} bytes ({time.monotonic()-started:.1f}s)", flush=True)

        # Output processing must be off while reading the exact binary back.
        # Input remains canonical; only ASCII commands are sent throughout.
        begin, end = nonce + "_BEGIN", nonce + "_END"
        console.send("/bin/stty -opost; echo; echo " + begin + "; /bin/cat " + quoted + "; echo; echo " + end + "; /bin/stty $id6_uart_saved")
        console.marker(begin)
        returned = console.exact(len(data))
        console.marker(end)
        if returned != data:
            raise RuntimeError("serial readback differs from the source; the helper was not made executable")
        console.acknowledged("/bin/chmod 755 " + quoted, nonce + "_VERIFIED")
        print(f"Verified {len(data)} bytes at {destination} in {time.monotonic()-started:.1f}s; SHA-256 {hashlib.sha256(returned).hexdigest()}", flush=True)
    finally:
        try:
            if child_started:
                console.send("\n/bin/stty $id6_uart_saved; exit")
        except OSError:
            pass
        connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
