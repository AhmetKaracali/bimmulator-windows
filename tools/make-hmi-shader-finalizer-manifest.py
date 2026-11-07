#!/usr/bin/env python3
"""Build a deduplicated list of captured BMW shader assets for native finalization."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset_map", type=Path)
    parser.add_argument("staged_root", type=Path,
                        help="realized QNX root, containing opt/hmi/ID5/data/ro")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    mapping = json.loads(args.asset_map.read_text())
    data_root = args.staged_root / "opt/hmi/ID5/data/ro"
    if not data_root.is_dir():
        raise SystemExit(f"staged HMI data directory is missing: {data_root}")

    by_hash: dict[str, dict] = {}
    for capture in mapping.get("captures", []):
        digest = capture.get("sha256")
        matches = capture.get("exact_staged_asset_matches", [])
        if not digest or not matches:
            continue
        entry = by_hash.setdefault(digest, {"sha256": digest, "aliases": set()})
        for match in matches:
            relative = Path(match["path"])
            asset = data_root / relative
            if not asset.is_file() or sha256(asset) != digest:
                raise SystemExit(f"asset does not verify against capture {digest}: {asset}")
            entry["aliases"].add(relative.as_posix())

    entries = []
    for digest, item in sorted(by_hash.items()):
        aliases = sorted(item["aliases"])
        if not aliases:
            continue
        entries.append({"name": digest[:16], "sha256": digest,
                        "path": aliases[0], "aliases": aliases})
    if not entries:
        raise SystemExit("asset map did not contain any exact staged shader matches")
    result = {
        "source_asset_map": str(args.asset_map),
        "data_root_relative_to_staged_root": "opt/hmi/ID5/data/ro",
        "unique_shader_count": len(entries),
        "inputs": entries,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "unique_shader_count": len(entries),
                      "sha256": [entry["sha256"] for entry in entries],
                      "aliases": [entry["aliases"] for entry in entries]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
