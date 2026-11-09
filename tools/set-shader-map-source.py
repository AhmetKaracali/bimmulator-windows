#!/usr/bin/env python3
"""Point one shader-map entry at a replacement ESSL source.

Usage: set-shader-map-source.py MAP.json ASSET_PATH SOURCE_PATH
Keeps the previous source in previous_source_path and records the LF sha256.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    map_path, asset, source = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    data = json.loads(map_path.read_text(encoding="utf-8"))
    entries = [e for e in data["mappings"] if e["asset_path"] == asset]
    if len(entries) != 1:
        print(f"error: {len(entries)} entries for {asset}", file=sys.stderr)
        return 1
    entry = entries[0]
    if entry["source_path"] != source:
        entry.setdefault("previous_source_path", entry["source_path"])
        entry["source_path"] = source
    entry["source_essl_sha256"] = hashlib.sha256(
        (ROOT / source).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    map_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{asset} -> {source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
