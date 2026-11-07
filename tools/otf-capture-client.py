#!/usr/bin/env python3
"""Connect to the forwarded BMW OTF viewer socket and save received bytes."""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import time
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--duration", type=float, default=86400.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--retry-interval", type=float, default=1.0)
    parser.add_argument("--wait-for-log", type=Path)
    parser.add_argument("--wait-for-marker")
    parser.add_argument(
        "--hello-frame",
        default="0900",
        help="hex bytes sent after connect; 0900 is BMW OTF viewer-connect with no payload",
    )
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    if args.duration <= 0 or args.retry_interval <= 0:
        parser.error("--duration and --retry-interval must be positive")
    if bool(args.wait_for_log) != bool(args.wait_for_marker):
        parser.error("--wait-for-log and --wait-for-marker must be used together")
    try:
        hello_frame = bytes.fromhex(args.hello_frame)
    except ValueError as exc:
        parser.error(f"--hello-frame must be hexadecimal bytes: {exc}")
    if len(hello_frame) < 2:
        parser.error("--hello-frame must contain at least the two-byte OTF header")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    metadata_path = args.output.with_suffix(args.output.suffix + ".json")
    deadline = time.monotonic() + args.duration
    stop_requested = False
    received_signal = None

    def request_stop(signum: int, _frame: object) -> None:
        nonlocal stop_requested, received_signal
        stop_requested = True
        received_signal = signal.Signals(signum).name

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    metadata = {
        "run_id": os.environ.get("IDRIVE_HMI_RUN_ID"),
        "connect_host": args.host,
        "connect_port": args.port,
        "started_utc": utc_now(),
        "duration_seconds": args.duration,
        "output": str(args.output.resolve()),
        "hello_frame_hex": hello_frame.hex(),
        "wait_for_log": str(args.wait_for_log) if args.wait_for_log else None,
        "wait_for_marker": args.wait_for_marker,
        "connections": 0,
        "bytes_received": 0,
    }
    print(json.dumps({"event": "run_context", "run_id": metadata["run_id"]}), flush=True)
    if args.wait_for_log:
        print(json.dumps({"event": "waiting_for_guest_marker",
                          "log": str(args.wait_for_log),
                          "marker": args.wait_for_marker}), flush=True)
        marker_seen = False
        while time.monotonic() < deadline and not stop_requested:
            try:
                marker_seen = args.wait_for_marker in args.wait_for_log.read_text(
                    errors="replace"
                )
            except FileNotFoundError:
                pass
            if marker_seen:
                break
            time.sleep(min(args.retry_interval,
                           max(0, deadline - time.monotonic())))
        if not marker_seen:
            raise TimeoutError(
                f"did not see {args.wait_for_marker!r} in {args.wait_for_log}"
            )
        print(json.dumps({"event": "guest_marker_seen",
                          "marker": args.wait_for_marker}), flush=True)
    print(json.dumps({"event": "connecting", "host": args.host,
                      "port": args.port, "output": str(args.output)}), flush=True)

    try:
        with args.output.open("wb") as output:
            while time.monotonic() < deadline and not stop_requested:
                try:
                    conn = socket.create_connection(
                        (args.host, args.port), timeout=min(1.0, args.retry_interval)
                    )
                except OSError:
                    time.sleep(min(args.retry_interval, max(0, deadline-time.monotonic())))
                    continue
                metadata["connections"] += 1
                print(json.dumps({"event": "connected", "connection": metadata["connections"],
                                  "opened_utc": utc_now()}), flush=True)
                with conn:
                    conn.sendall(hello_frame)
                    print(json.dumps({"event": "sent_viewer_frame",
                                      "connection": metadata["connections"],
                                      "hex": hello_frame.hex()}), flush=True)
                    conn.settimeout(0.5)
                    while time.monotonic() < deadline and not stop_requested:
                        try:
                            chunk = conn.recv(65536)
                        except TimeoutError:
                            continue
                        except OSError as exc:
                            print(json.dumps({"event": "read_error", "error": str(exc)}),
                                  flush=True)
                            break
                        if not chunk:
                            break
                        output.write(chunk)
                        output.flush()
                        metadata["bytes_received"] += len(chunk)
                print(json.dumps({"event": "closed", "bytes_received": metadata["bytes_received"]}),
                      flush=True)
                if time.monotonic() < deadline and not stop_requested:
                    time.sleep(min(args.retry_interval,
                                   max(0, deadline-time.monotonic())))
    finally:
        if received_signal:
            metadata["stopped_by_signal"] = received_signal
        metadata["finished_utc"] = utc_now()
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
        print(json.dumps({"event": "finished", "connections": metadata["connections"],
                          "bytes_received": metadata["bytes_received"],
                          "metadata": str(metadata_path)}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
