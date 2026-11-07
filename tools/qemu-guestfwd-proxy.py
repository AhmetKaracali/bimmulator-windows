#!/usr/bin/env python3
"""Bridge one QEMU guestfwd TCP stream to a fresh host TCP connection."""

from __future__ import annotations

import os
import socket
import sys
import threading
import time

TRACE_PATH = ""


def trace(event: str) -> None:
    path = TRACE_PATH or os.environ.get("IDRIVE_QEMU_GUESTFWD_LOG")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as stream:
            stream.write(f"{time.time():.6f} pid={os.getpid()} {event}\n")
    except OSError:
        pass


def copy_guest_to_host(host: socket.socket) -> None:
    try:
        while True:
            data = os.read(0, 64 * 1024)
            if not data:
                break
            host.sendall(data)
    except (BrokenPipeError, ConnectionError, OSError):
        pass
    finally:
        try:
            host.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def copy_host_to_guest(host: socket.socket) -> None:
    try:
        while True:
            data = host.recv(64 * 1024)
            if not data:
                break
            view = memoryview(data)
            while view:
                written = os.write(1, view)
                view = view[written:]
    except (BrokenPipeError, ConnectionError, OSError):
        pass


def main() -> int:
    global TRACE_PATH
    if len(sys.argv) not in (3, 4):
        print("usage: qemu-guestfwd-proxy.py HOST PORT [TRACE_LOG]", file=sys.stderr)
        return 2
    if len(sys.argv) == 4:
        TRACE_PATH = sys.argv[3]
    host_name = sys.argv[1]
    try:
        port = int(sys.argv[2], 10)
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        print(f"invalid TCP port: {sys.argv[2]}", file=sys.stderr)
        return 2

    trace(f"GUESTFWD_START destination={host_name}:{port}")
    try:
        upstream = socket.create_connection((host_name, port), timeout=10)
    except OSError as error:
        trace(f"GUESTFWD_UPSTREAM_FAIL destination={host_name}:{port} error={error}")
        print(f"guestfwd upstream connect failed: {error}", file=sys.stderr)
        return 1

    trace(f"GUESTFWD_UPSTREAM_CONNECTED destination={host_name}:{port}")
    upstream.settimeout(None)
    output = threading.Thread(target=copy_host_to_guest, args=(upstream,), daemon=True)
    output.start()
    copy_guest_to_host(upstream)
    output.join(timeout=10)
    upstream.close()
    trace(f"GUESTFWD_CLOSED destination={host_name}:{port}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
