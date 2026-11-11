#!/usr/bin/env python3
"""Materialize eight firmware-matched HMI widgets from the PSdZData inventory."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


PSDZ_HMI_DATA = Path("rootfs/opt/hmi/ID5/data/ro")
PSDZ_HMI_BINARY = Path("rootfs/opt/hmi/ID5/bin/HmiMain3D")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import buildinfo  # noqa: E402

# Firmware-matched widget domains and their package come from builds/<id>/build.json.
_BUILD = buildinfo.current_build()
PSDZ_ASSET_PACKAGE = _BUILD["asset_package"]
ASSET_DOMAINS = dict(_BUILD["assetdb_domains"])


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize(source: Path, destination: Path, manifest_path: Path) -> dict:
    if source.is_symlink() or destination.is_symlink():
        raise RuntimeError("the source and destination roots must be ordinary directories")
    extraction = manifest_path.parent.resolve()
    if source.resolve() != extraction / PSDZ_HMI_DATA:
        raise RuntimeError("the HMI source must be the data/ro tree beside extraction.json")
    inventory = json.loads(manifest_path.read_text())["files"]
    binary = inventory.get(PSDZ_HMI_BINARY.as_posix())
    if binary is None or binary["package"] != PSDZ_ASSET_PACKAGE:
        raise RuntimeError(f"the PSdZData inventory does not identify the HmiMain3D of build {_BUILD.id}")
    for path in (extraction / PSDZ_HMI_BINARY, destination.parents[1] / "bin/HmiMain3D"):
        if digest(path) != binary["sha256"]:
            raise RuntimeError(f"HmiMain3D does not match the PSdZData inventory: {path}")

    copied, existing = [], []
    for relative, widget_hash in ASSET_DOMAINS.items():
        domain = source / relative
        widget = domain / "widget.pbw"
        record = inventory.get((PSDZ_HMI_DATA / relative / "widget.pbw").as_posix())
        if record is None or record["package"] != PSDZ_ASSET_PACKAGE or record["sha256"] != widget_hash:
            raise RuntimeError(f"widget identity does not match X20511I: {widget}")
        if digest(widget) != widget_hash:
            raise RuntimeError(f"widget file does not match the PSdZData inventory: {widget}")

        for item in sorted(domain.rglob("*")):
            if item.is_symlink():
                raise RuntimeError(f"unexpected symlink in assetDB domain: {item}")
            target = destination / item.relative_to(source)
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            data = item.read_bytes()
            item_record = inventory.get((PSDZ_HMI_DATA / item.relative_to(source)).as_posix())
            if item_record is None or item_record["package"] != PSDZ_ASSET_PACKAGE:
                raise RuntimeError(f"asset is absent from the matched PSdZData package: {item}")
            content_hash = hashlib.sha256(data).hexdigest()
            if content_hash != item_record["sha256"] or len(data) != item_record["size"]:
                raise RuntimeError(f"asset does not match the PSdZData inventory: {item}")
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                if digest(target) != content_hash:
                    raise RuntimeError(f"refusing to replace different asset: {target}")
                existing.append(item.relative_to(source).as_posix())
            else:
                target.write_bytes(data)
                copied.append(item.relative_to(source).as_posix())
    return {"asset_domains": list(ASSET_DOMAINS), "copied_files": copied, "already_present": existing}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("destination_root", type=Path)
    parser.add_argument("--psdz-extraction-manifest", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    if not args.source_root.is_dir() or not args.destination_root.is_dir():
        parser.error("source_root and destination_root must be existing directories")
    try:
        result = materialize(args.source_root, args.destination_root, args.psdz_extraction_manifest)
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    if args.manifest:
        args.manifest.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"asset_domains": len(result["asset_domains"]), "copied_files": len(result["copied_files"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
