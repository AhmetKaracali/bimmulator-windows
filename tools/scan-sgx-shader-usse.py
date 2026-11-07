#!/usr/bin/env python3
"""Find candidate USSE instruction runs inside BMW `.shd` PSU payloads.

This is a structural aid, not a complete shader disassembler. It reports
aligned qwords that match Vita3K's pinned SGX543 grammar and keeps broad
fallback classes separate. A matching run is not by itself proof of an
executable program boundary or SGX544 semantics.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
FALLBACK_OPS = {"VMAD2", "SOP2", "SOP2WM", "SPEC", "VLDST"}


def load_tool(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load helper {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shader_parser = load_tool("inspect_sgx_shader", ROOT / "tools/inspect-sgx-shader.py")
decoder = load_tool("decode_sgx_usse", ROOT / "tools/decode-sgx-usse.py")
GRAMMAR = decoder.load_grammar(ROOT / "third_party/vita3k/usse-grammar.yaml")


def collect_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(sorted(path.rglob("*.shd")))
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(path)
    return files


def inspect_payload(data: bytes, payload: dict[str, Any], payload_index: int,
                    min_run: int) -> dict[str, Any]:
    start = payload["offset"]
    end = start + payload["length"]
    strong: list[dict[str, Any]] = []
    weak: list[dict[str, Any]] = []
    for offset in range((start + 7) & ~7, end - 7, 8):
        word = struct.unpack_from("<Q", data, offset)[0]
        matches = decoder.decode(word, GRAMMAR)
        names = [match["op"] for match in matches]
        if not names:
            continue
        record = {"offset": offset, "word": f"{word:016x}", "opcodes": names}
        if all(name in FALLBACK_OPS for name in names):
            weak.append(record)
        else:
            strong.append(record)

    by_offset = {item["offset"]: item for item in strong}
    runs: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for offset in sorted(by_offset):
        if current and offset != current[-1]["offset"] + 8:
            if len(current) >= min_run:
                runs.append(current)
            current = []
        current.append(by_offset[offset])
    if len(current) >= min_run:
        runs.append(current)

    output_runs = []
    for run in runs:
        last_end = run[-1]["offset"] + 8
        trailing_fallbacks = [item for item in weak
                              if last_end <= item["offset"] < min(end, last_end + 16)]
        output_runs.append({
            "offset": run[0]["offset"],
            "end_offset": last_end,
            "qword_count": len(run),
            "distance_to_payload_end": end - last_end,
            "words": run,
            "following_fallback_words": trailing_fallbacks,
        })

    return {
        "payload_index": payload_index,
        "payload_offset": start,
        "payload_end": end,
        "payload_length": payload["length"],
        "candidate_runs": output_runs,
    }


def inspect_file(path: Path, min_run: int) -> dict[str, Any]:
    record = shader_parser.parse_shader(path)
    data = path.read_bytes()
    return {
        "path": str(path),
        "sha256": hashlib.sha256(data).hexdigest(),
        "stage": record["stage"],
        "payloads": [inspect_payload(data, payload, index, min_run)
                     for index, payload in enumerate(record["payloads"])],
        "grammar_reference": "Vita3K SGX543 grammar pinned in third_party/vita3k/",
        "interpretation": "candidate instruction runs only; not a verified program extractor",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="shader files or directories")
    parser.add_argument("--min-run", type=int, default=2,
                        help="minimum consecutive non-fallback qwords to report (default: 2)")
    parser.add_argument("--json", action="store_true", help="emit detailed JSON")
    args = parser.parse_args()
    if args.min_run < 1:
        parser.error("--min-run must be positive")

    try:
        reports = [inspect_file(path, args.min_run) for path in collect_files(args.paths)]
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(reports, indent=2))
        return 0

    for report in reports:
        print(f"{report['path']} stage={report['stage']} sha256={report['sha256']}")
        for payload in report["payloads"]:
            for run in payload["candidate_runs"]:
                opcodes = " ".join(word["opcodes"][0] for word in run["words"])
                print(
                    f"  PSU[{payload['payload_index']}] "
                    f"{run['offset']:#x}..{run['end_offset']:#x} "
                    f"({run['qword_count']} qwords, "
                    f"{run['distance_to_payload_end']} bytes before payload end): "
                    f"{opcodes}"
                )
                for item in run["following_fallback_words"]:
                    print(f"    following fallback {item['offset']:#x}: "
                          f"{item['word']} {'/'.join(item['opcodes'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
