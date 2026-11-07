#!/usr/bin/env python3
"""Extract and validate a batch of native BMW UniPatch finalizer results."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def scalar(section: str, name: str) -> int:
    values = re.findall(r"^" + re.escape(name) + r"=0x([0-9a-f]{8})$", section, re.M)
    if len(values) != 1:
        raise ValueError(f"missing or duplicate {name}")
    return int(values[0], 16)


def stream(section: str, name: str) -> bytes:
    output = bytearray()
    for offset, raw in re.findall(
            r"^" + re.escape(name) + r"\+0x([0-9a-f]{8})=([0-9a-f]+)$", section, re.M):
        if int(offset, 16) != len(output):
            raise ValueError(f"noncontiguous {name} stream")
        chunk = bytes.fromhex(raw)
        if not chunk or len(chunk) > 64:
            raise ValueError(f"invalid {name} chunk")
        output.extend(chunk)
    return bytes(output)


def extract(section: str, name: str, directory: Path, stage: str) -> dict:
    if not re.search(r"^BMW-UNIPATCH-BATCH-PASS$", section, re.M):
        failures = re.findall(r"^BMW-UNIPATCH-BATCH-FAIL (.+)$", section, re.M)
        return {"name": name, "stage": stage, "status": "failed",
                "failure": failures[-1] if failures else "unknown"}
    final = stream(section, "final")
    base, size = scalar(section, "final-pointer"), scalar(section, "final-size")
    if len(final) != size or not 0xa4 <= size <= 2 * 1024 * 1024:
        raise ValueError(f"{name}: incomplete or invalid finalized allocation")

    def u16(offset: int) -> int:
        return struct.unpack_from("<H", final, offset)[0]

    def u32(offset: int) -> int:
        return struct.unpack_from("<I", final, offset)[0]

    def bounded(pointer: int, count: int, stride: int, label: str) -> tuple[int | None, bytes]:
        if count == 0:
            return None, b""
        offset = pointer - base
        length = count * stride
        if offset < 0xa4 or offset > size or length > size - offset:
            raise ValueError(f"{name}: {label} points outside the captured allocation")
        return offset, final[offset:offset + length]

    files = {f"{stage}.final.bin": final}
    ranges = {}
    occupied = []
    for file_name, count, pointer in (
            (f"{stage}.primary.usse.bin", u16(0x0c), u32(0x10)),
            (f"{stage}.secondary.usse.bin", u16(0x1c), u32(0x20))):
        if file_name.endswith("primary.usse.bin") and not 1 <= count <= 4096:
            raise ValueError(f"{name}: invalid primary instruction count")
        offset, payload = bounded(pointer, count, 8, file_name)
        files[file_name] = payload
        ranges[file_name] = {"offset": offset, "instruction_count": count,
                             "bytes": len(payload), "sha256": digest(payload)}
        if payload:
            occupied.append((offset, offset + len(payload), file_name))

    if stream(section, "code") != files[f"{stage}.primary.usse.bin"]:
        raise ValueError(f"{name}: independent primary-code stream disagrees")
    for count_offset, pointer_offset, stride, count in (
            (0x44, 0x48, 28, u16(0x44)),
            (0x4c, 0x50, 20, u32(0x4c)),
            (0x54, 0x58, 20, u16(0x54)),
            (0x5c, 0x60, 12, u16(0x5c)),
            (0x64, 0x68, 12, u32(0x64)),
            (0x94, 0x98, 36, u32(0x94)),
            (0x9c, 0xa0, 4, (u32(0x9c) + 31) // 32)):
        table = f"{stage}.table_{count_offset:02x}.bin"
        offset, payload = bounded(u32(pointer_offset), count, stride, table)
        files[table] = payload
        ranges[table] = {"offset": offset, "count": count, "stride": stride,
                         "bytes": len(payload), "sha256": digest(payload)}
        if payload:
            occupied.append((offset, offset + len(payload), table))
    occupied.sort()
    for previous, current in zip(occupied, occupied[1:]):
        if previous[1] > current[0]:
            raise ValueError(f"{name}: overlapping {previous[2]} and {current[2]}")

    directory.mkdir(parents=True, exist_ok=False)
    for file_name, payload in files.items():
        (directory / file_name).write_bytes(payload)
    result = {"name": name, "stage": stage, "status": "passed", "final_size": size,
              "final_sha256": digest(final), "instruction_count": u16(0x0c),
              "ranges": ranges,
              "interpretation": "native finalized code and tables; portable execution not established"}
    (directory / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("output", type=Path, help="new output directory")
    parser.add_argument("--input-manifest", type=Path)
    parser.add_argument("--stage", choices=("vertex", "fragment"), default="vertex",
                        help="stage for legacy manifests that do not record it")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output directory already exists: {args.output}")
    raw = args.log.read_bytes()
    text = raw.decode("ascii", errors="replace").replace("\r", "")
    starts = list(re.finditer(r"^BMW-UNIPATCH-BATCH-BEGIN$", text, re.M))
    if not starts:
        raise SystemExit("no batch shader results found")
    manifest_entries = {}
    if args.input_manifest:
        manifest_entries = {entry["name"]: entry for entry in
                            json.loads(args.input_manifest.read_text()).get("inputs", [])}
    args.output.mkdir(parents=True)
    results = []
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        section = text[match.end():end]
        lines = [line.strip() for line in section.splitlines() if line.strip()]
        if not lines or not re.fullmatch(r"[0-9a-f]{16}", lines[0]):
            raise ValueError(f"batch result {index}: malformed shader identity")
        name = lines[0]
        stage = manifest_entries.get(name, {}).get("stage", args.stage)
        if stage not in ("vertex", "fragment"):
            raise ValueError(f"{name}: unsupported shader stage {stage!r}")
        results.append(extract(section, name, args.output / name, stage))
        if name in manifest_entries:
            results[-1]["source_sha256"] = manifest_entries[name]["sha256"]
            results[-1]["asset_path"] = manifest_entries[name]["path"]
            results[-1]["aliases"] = manifest_entries[name].get("aliases", [])
    if args.input_manifest and len(starts) != len(manifest_entries):
        raise ValueError(f"batch result count {len(starts)} does not match manifest count {len(manifest_entries)}")
    report = {"capture": str(args.log), "capture_sha256": digest(raw),
              "results": results,
              "passed": sum(result["status"] == "passed" for result in results),
              "failed": sum(result["status"] != "passed" for result in results)}
    (args.output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "passed": report["passed"],
                      "failed": report["failed"],
                      "shaders": [{"name": r["name"], "stage": r.get("stage"), "status": r["status"],
                                   "instructions": r.get("instruction_count"),
                                   "asset": r.get("asset_path"),
                                   "failure": r.get("failure")} for r in results]}, indent=2))
    return 0 if not report["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
