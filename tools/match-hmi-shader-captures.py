#!/usr/bin/env python3
"""Match runtime IMG shader uploads against staged BMW .shd assets."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_shader_parser():
    path = Path(__file__).with_name("inspect-sgx-shader.py")
    spec = importlib.util.spec_from_file_location("inspect_sgx_shader", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load shader parser: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_capture_metadata(host_log: Path | None) -> dict[str, dict]:
    if host_log is None:
        return {}
    metadata = {}
    pattern = re.compile(
        r"ANGLE_SHADER_BINARY_CAPTURE index=(\d+) client=(\d+) "
        r"count=(\d+) shaders=([^ ]+) format=0x([0-9a-fA-F]+) "
        r"length=(\d+) fnv1a64=([0-9a-fA-F]+) path=(.*?) outcome=([^ ]+)"
    )
    for line in host_log.read_text(errors="replace").splitlines():
        match = pattern.search(line)
        if not match:
            continue
        index, client, count, shaders, binary_format, length, fnv, path, outcome = match.groups()
        metadata[Path(path).name] = {
            "index": int(index),
            "client": int(client),
            "count": int(count),
            "shader_ids": [int(value) for value in shaders.split(",") if value],
            "format": int(binary_format, 16),
            "length": int(length),
            "fnv1a64": fnv.lower(),
            "provider_outcome": outcome,
        }
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_dir", type=Path)
    parser.add_argument("staged_root", type=Path,
                        help="staged X20511I root containing the .shd files")
    parser.add_argument("--host-log", type=Path)
    parser.add_argument("--output", type=Path,
                        help="write the report JSON here as well as stdout")
    args = parser.parse_args()

    shader_parser = load_shader_parser()
    assets_by_hash: dict[str, list[Path]] = {}
    for path in sorted(args.staged_root.rglob("*.shd")):
        digest = sha256(path.read_bytes())
        assets_by_hash.setdefault(digest, []).append(path)

    host_metadata = read_capture_metadata(args.host_log)
    captures = []
    for path in sorted(args.capture_dir.glob("*.bin")):
        data = path.read_bytes()
        digest = sha256(data)
        matches = assets_by_hash.get(digest, [])
        candidates = []
        for asset in matches:
            parsed = shader_parser.parse_shader(asset)
            candidates.append({
                "path": str(asset),
                "stage": parsed["stage"],
                "stage_id": parsed["stage_id"],
            })
        record = {
            "capture": path.name,
            "bytes": len(data),
            "sha256": digest,
            "exact_full_asset_match": bool(candidates),
            "asset_candidates": candidates,
        }
        record.update(host_metadata.get(path.name, {}))
        captures.append(record)

    sources = []
    for path in sorted(args.capture_dir.glob("*.glsl")):
        data = path.read_bytes()
        sources.append({"capture": path.name, "bytes": len(data), "sha256": sha256(data)})

    report = {
        "capture_dir": str(args.capture_dir),
        "staged_root": str(args.staged_root),
        "staged_shader_asset_count": sum(len(paths) for paths in assets_by_hash.values()),
        "binary_capture_count": len(captures),
        "exact_full_asset_match_count": sum(
            1 for capture in captures if capture["exact_full_asset_match"]
        ),
        "captures": captures,
        "source_captures": sources,
    }
    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
