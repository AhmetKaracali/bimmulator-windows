#!/usr/bin/env python3
"""Extract bounded native UniPatch output from qnx-shader-finalizer-probe logs.

This preserves genuine finalized instructions and opaque binding tables. It
does not translate instructions or establish rendering correctness. The
descriptor ABI is tied to the driver hash in build-qnx-shader-parser-probe.sh.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_stage(text: str, stage: str) -> tuple[bytes, dict, dict[str, bytes]]:
    starts = list(re.finditer(r"^BMW-UNIPATCH-BEGIN " + stage + r"$", text, re.M))
    if len(starts) != 1:
        raise ValueError(f"expected exactly one {stage} capture, found {len(starts)}")
    section = text[starts[0].end():]
    next_stage = section.find("BMW-UNIPATCH-BEGIN ")
    if next_stage >= 0:
        section = section[:next_stage]
    if not re.search(r"^BMW-UNIPATCH-PASS " + stage + r"$", section, re.M):
        raise ValueError(f"{stage}: native probe did not pass")

    def scalar(name: str) -> int:
        values = re.findall(r"^" + re.escape(name) + r"=0x([0-9a-f]{8})$", section, re.M)
        if len(values) != 1:
            raise ValueError(f"{stage}: missing/duplicate {name}")
        return int(values[0], 16)

    def stream(name: str) -> bytes:
        data = bytearray()
        for offset, raw in re.findall(r"^" + name + r"\+0x([0-9a-f]{8})=([0-9a-f]+)$", section, re.M):
            if int(offset, 16) != len(data):
                raise ValueError(f"{stage}: noncontiguous {name} capture")
            chunk = bytes.fromhex(raw)
            if not chunk or len(chunk) > 64:
                raise ValueError(f"{stage}: invalid {name} chunk")
            data.extend(chunk)
        return bytes(data)

    data = stream("final")
    base, size = scalar("final-pointer"), scalar("final-size")
    if len(data) != size or not 0xa4 <= size <= 2 * 1024 * 1024:
        raise ValueError(f"{stage}: incomplete/oversized native allocation")
    if scalar("parse-result"):
        raise ValueError(f"{stage}: parser failed")

    def u16(offset: int) -> int:
        return struct.unpack_from("<H", data, offset)[0]

    def u32(offset: int) -> int:
        return struct.unpack_from("<I", data, offset)[0]

    def bounded(pointer: int, count: int, stride: int, label: str) -> tuple[int | None, bytes]:
        if count == 0:
            return None, b""
        offset = pointer - base
        length = count * stride
        if offset < 0xa4 or offset > size or length > size - offset:
            raise ValueError(f"{stage}: {label} points outside the captured data region")
        return offset, data[offset:offset + length]

    files = {}
    ranges = {}
    occupied = []
    for name, count, pointer in (
        ("primary", u16(0x0c), u32(0x10)),
        ("secondary", u16(0x1c), u32(0x20)),
    ):
        if name == "primary" and not 1 <= count <= 4096:
            raise ValueError(f"{stage}: invalid primary instruction count")
        offset, payload = bounded(pointer, count, 8, name)
        files[name + ".usse.bin"] = payload
        ranges[name] = {"offset": offset, "instruction_count": count,
                        "bytes": len(payload), "sha256": digest(payload)}
        if payload:
            occupied.append((offset, offset + len(payload), name))
    if u32(0x10) != scalar("instruction-pointer") or u16(0x0c) != scalar("instruction-count"):
        raise ValueError(f"{stage}: logged primary fields disagree with descriptor")
    if stream("code") != files["primary.usse.bin"]:
        raise ValueError(f"{stage}: independent primary-code capture disagrees")

    # Count/pointer/stride fields recovered from the native output constructor.
    # Keep unknown semantic names explicit; these are not GXP binding records.
    for count_offset, pointer_offset, stride, count in (
        (0x44, 0x48, 28, u16(0x44)),
        (0x4c, 0x50, 20, u32(0x4c)),
        (0x54, 0x58, 20, u16(0x54)),
        (0x5c, 0x60, 12, u16(0x5c)),
        (0x64, 0x68, 12, u32(0x64)),
        (0x94, 0x98, 36, u32(0x94)),
        (0x9c, 0xa0, 4, (u32(0x9c) + 31) // 32),
    ):
        name = f"table_{count_offset:02x}"
        offset, payload = bounded(u32(pointer_offset), count, stride, name)
        ranges[name] = {"offset": offset, "count": count, "stride": stride,
                        "bytes": len(payload), "sha256": digest(payload)}
        files[name + ".bin"] = payload
        if payload:
            occupied.append((offset, offset + len(payload), name))
    occupied.sort()
    for previous, current in zip(occupied, occupied[1:]):
        if previous[1] > current[0]:
            raise ValueError(f"{stage}: overlapping {previous[2]} and {current[2]}")
    report = {"stage": stage, "allocation_bytes": size,
              "allocation_sha256": digest(data), "ranges": ranges,
              "interpretation": "native finalized code/table bytes; no portable execution proved"}
    return data, report, files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("output", type=Path, help="new output directory")
    args = parser.parse_args()
    raw = args.log.read_bytes()
    text = raw.decode("ascii", errors="replace").replace("\r", "")
    # Validate both stages before writing anything.
    captures = {stage: extract_stage(text, stage) for stage in ("vertex", "fragment")}
    args.output.mkdir(parents=True, exist_ok=False)
    reports = []
    for stage, (data, report, files) in captures.items():
        (args.output / f"{stage}.final.bin").write_bytes(data)
        for name, payload in files.items():
            (args.output / f"{stage}.{name}").write_bytes(payload)
        reports.append(report)
    manifest = {"capture": str(args.log), "capture_sha256": digest(raw), "stages": reports}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
