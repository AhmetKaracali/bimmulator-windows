#!/usr/bin/env python3
"""Measure changing native iDrive frames during a repeatable rotary workload."""

import argparse
from itertools import cycle
import json
from math import ceil
from pathlib import Path
import socket
from statistics import median
import time


def qmp_command(stream, name, arguments=None):
    request = {"execute": name}
    if arguments is not None:
        request["arguments"] = arguments
    stream.write(json.dumps(request).encode() + b"\n")
    for line in stream:
        reply = json.loads(line)
        if "error" in reply:
            raise RuntimeError(f"QMP {name}: {reply['error']}")
        if "return" in reply:
            return reply["return"]
    raise RuntimeError(f"QMP closed while executing {name}")


def measure_frames(records, previous_hash):
    changed = []
    pending = None
    posts = 0
    for line in records.splitlines():
        kind, _, fields = line.partition(b" ")
        if kind == b"ANGLE_SCREEN_FRAME":
            pending = dict(item.split(b"=", 1) for item in fields.split())
        elif kind == b"ANGLE_SCREEN_POSTED" and pending is not None:
            posts += 1
            digest = pending[b"fnv1a64"]
            if digest != previous_hash:
                timestamp = dict(item.split(b"=", 1) for item in fields.split())
                changed.append(int(timestamp[b"host_us"]))
            previous_hash = digest
            pending = None
    intervals = [(right - left) / 1000 for left, right in zip(changed, changed[1:])]
    return posts, changed, intervals


def scanout_matches(capture, records, ram_path):
    magic, dimensions, max_channel, rgb = capture.read_bytes().split(b"\n", 3)
    if magic != b"P6" or max_channel != b"255" or not any(rgb):
        return False
    width, height = map(int, dimensions.split())
    offsets = set()
    with ram_path.open("rb") as ram:
        for line in reversed(records.splitlines()):
            if not line.startswith(b"ANGLE_SCREEN_FRAME "):
                continue
            frame = dict(item.split(b"=", 1) for item in line.split()[1:])
            if (width, height) != (int(frame[b"width"]), int(frame[b"height"])):
                continue
            offset = int(frame[b"offset"], 16)
            if offset in offsets:
                continue
            if len(offsets) == 2:
                break
            offsets.add(offset)
            ram.seek(offset)
            bgra = ram.read(int(frame[b"bytes"]))
            stride = int(frame[b"stride"])
            if len(bgra) != stride * height:
                continue
            result = bytearray(len(rgb))
            for y in range(height):
                source = bgra[y * stride:y * stride + width * 4]
                start, end = y * width * 3, (y + 1) * width * 3
                result[start:end:3] = source[2::4]
                result[start + 1:end:3] = source[1::4]
                result[start + 2:end:3] = source[0::4]
            if result == rgb:
                return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path, help="directory from run-hmi-profile.py")
    parser.add_argument("--seconds", type=float, default=20)
    parser.add_argument("--interval", type=float, default=0.18, help="seconds between rotary steps")
    parser.add_argument("--wait", type=float, default=900, help="seconds to wait for the first native post")
    parser.add_argument("--output", type=Path, help="new evidence directory inside or outside the run")
    args = parser.parse_args()
    if args.seconds <= 0 or args.interval <= 0 or args.wait < 0:
        parser.error("duration and input interval must be positive and wait cannot be negative")

    config = json.loads((args.run_dir / "run-manifest.json").read_text())["effective_configuration"]
    log_path = Path(config["IDRIVE_ANGLE_EGL_SERVER_LOG"])
    ram_path = Path(config["IDRIVE_QEMU_SHARED_RAM_FILE"])
    deadline = time.monotonic() + args.wait
    while b"\nANGLE_SCREEN_POSTED " not in log_path.read_bytes():
        if time.monotonic() >= deadline:
            raise SystemExit("No successful native Screen post before timeout")
        time.sleep(0.5)
    time.sleep(2)

    output = (args.output or args.run_dir / "evidence-frame-rate").resolve()
    output.mkdir(parents=True, exist_ok=False)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as qmp:
        qmp.settimeout(15)
        qmp.connect(config["IDRIVE_QEMU_QMP_SOCKET"])
        with qmp.makefile("rwb", buffering=0) as stream, log_path.open("rb") as angle:
            if not stream.readline():
                raise RuntimeError("Missing QMP greeting")
            qmp_command(stream, "qmp_capabilities")
            before = output / "before.ppm"
            qmp_command(stream, "screendump", {"filename": str(before)})
            before_matches = scanout_matches(before, log_path.read_bytes(), ram_path)
            previous_hash = None
            for line in angle:
                if line.startswith(b"ANGLE_SCREEN_FRAME "):
                    previous_hash = dict(item.split(b"=", 1) for item in line.split()[1:])[b"fnv1a64"]
            start_offset = angle.tell()
            started = time.monotonic()
            sent = 0
            for key in cycle(("pgdn", "pgdn", "pgup", "pgup")):
                if time.monotonic() >= started + args.seconds:
                    break
                events = [
                    {"type": "key", "data": {"key": {"type": "qcode", "data": key}, "down": down}}
                    for down in (True, False)
                ]
                qmp_command(stream, "input-send-event", {"events": events})
                sent += 1
                next_step = min(started + sent * args.interval, started + args.seconds)
                time.sleep(max(0, next_step - time.monotonic()))
            elapsed = time.monotonic() - started
            end_offset = log_path.stat().st_size
            time.sleep(1)
            after = output / "after.ppm"
            qmp_command(stream, "screendump", {"filename": str(after)})
            after_matches = scanout_matches(after, log_path.read_bytes(), ram_path)
            angle.seek(start_offset)
            records = angle.read(end_offset - start_offset)

    posts, changed, intervals = measure_frames(records, previous_hash)
    result = {
        "seconds": round(elapsed, 3),
        "rotary_interval_seconds": args.interval,
        "keys_sent": sent,
        "keys_queued": sum(line.startswith(b"ANGLE_HMI_CONTROLLER_QUEUED ")
                           for line in records.splitlines()),
        "scanout_matches_screen_before": before_matches,
        "scanout_matches_screen_after": after_matches,
        "screen_posts": posts,
        "changing_screen_posts": len(changed),
        "changing_fps": round(len(changed) / elapsed, 2),
        "median_frame_ms": round(median(intervals), 3) if intervals else None,
        "p95_frame_ms": sorted(intervals)[ceil(len(intervals) * 0.95) - 1] if intervals else None,
        "frame_intervals_ms": intervals,
    }
    (output / "angle-delta.log").write_bytes(records)
    (output / "benchmark.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "frame_intervals_ms"}, indent=2))
    return 0 if changed and before_matches and after_matches else 1


if __name__ == "__main__":
    raise SystemExit(main())
