#!/usr/bin/env python3
"""Passively capture the BMW OTF viewer stream from the QNX guest."""

from __future__ import annotations

import argparse
import json
import signal
import socket
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1000)
    parser.add_argument("--duration", type=float, default=86400.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.port < 1 or args.port > 65535:
        parser.error("--port must be between 1 and 65535")
    if args.duration <= 0:
        parser.error("--duration must be positive")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    metadata_path = args.output.with_suffix(args.output.suffix + ".json")
    deadline = time.monotonic() + args.duration
    stop_requested = threading.Event()
    received_signal: list[str] = []

    def request_stop(signum: int, _frame: object) -> None:
        if not received_signal:
            received_signal.append(signal.Signals(signum).name)
        stop_requested.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    metadata = {
        "listen_host": args.host,
        "listen_port": args.port,
        "started_utc": utc_now(),
        "duration_seconds": args.duration,
        "output": str(args.output.resolve()),
        "connections": [],
        "bytes_received": 0,
    }

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((args.host, args.port))
            server.listen(4)
            server.settimeout(min(1.0, args.duration))
            print(json.dumps({"event": "listening", "host": args.host,
                              "port": args.port, "output": str(args.output)}),
                  flush=True)
            with args.output.open("wb") as output:
                while time.monotonic() < deadline and not stop_requested.is_set():
                    try:
                        conn, peer = server.accept()
                    except TimeoutError:
                        continue
                    record = {"peer": f"{peer[0]}:{peer[1]}", "opened_utc": utc_now(),
                              "offset": metadata["bytes_received"], "bytes": 0}
                    metadata["connections"].append(record)
                    print(json.dumps({"event": "connected", **record}), flush=True)
                    with conn:
                        conn.settimeout(max(0.1, min(2.0, deadline - time.monotonic())))
                        while time.monotonic() < deadline and not stop_requested.is_set():
                            try:
                                chunk = conn.recv(65536)
                            except TimeoutError:
                                continue
                            if not chunk:
                                break
                            output.write(chunk)
                            output.flush()
                            record["bytes"] += len(chunk)
                            metadata["bytes_received"] += len(chunk)
                    record["closed_utc"] = utc_now()
                    print(json.dumps({"event": "closed", **record}), flush=True)
    finally:
        if received_signal:
            metadata["stopped_by_signal"] = received_signal[0]
        metadata["finished_utc"] = utc_now()
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
        print(json.dumps({"event": "finished", "bytes_received": metadata["bytes_received"],
                          "connections": len(metadata["connections"]),
                          "output": str(args.output), "metadata": str(metadata_path)}),
              flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
