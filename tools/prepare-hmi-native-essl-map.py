#!/usr/bin/env python3
"""Validate an exact HMI shader map and print guest/host path pairs as TSV."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys


FRAGMENT_MAP = "idrive6-hmi-exact-fragment-map-v1"
FRAGMENT_MAP_DELTA = "idrive6-hmi-exact-fragment-map-delta-v1"
VERTEX_MAP = "idrive6-hmi-exact-vertex-map-v1"
VERTEX_MAP_DELTA = "idrive6-hmi-exact-vertex-map-delta-v1"
DELTA_BASE_SCHEMAS = {FRAGMENT_MAP_DELTA: FRAGMENT_MAP, VERTEX_MAP_DELTA: VERTEX_MAP}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_relative(value: str, label: str) -> Path:
    posix = PurePosixPath(value)
    if posix.is_absolute() or ".." in posix.parts or "\t" in value or "\n" in value:
        raise ValueError(f"unsafe {label}: {value!r}")
    return Path(*posix.parts)


def apply_map_delta(delta: dict, repo_root: Path) -> dict:
    base_path = repo_root / safe_relative(delta["base_manifest"], "base manifest path")
    base_bytes = base_path.read_bytes()
    if hashlib.sha256(base_bytes).hexdigest() != delta["base_manifest_sha256"]:
        raise ValueError(f"base shader-map manifest hash changed: {base_path}")
    base = json.loads(base_bytes)
    if base.get("schema") != DELTA_BASE_SCHEMAS[delta["schema"]]:
        raise ValueError("shader-map delta requires a full manifest for the same shader stage")

    def identity(entry: dict) -> tuple[str, str | None]:
        return entry["asset_path"], entry.get("shader_sha256")

    mappings = base["mappings"]
    base_keys = {identity(entry) for entry in mappings}
    replacements = {}
    for entry in delta.get("replacements", []):
        key = identity(entry)
        if not key[1]:
            raise ValueError(f"shader-map replacement is missing its native shader hash: {key[0]}")
        if key not in base_keys or key in replacements:
            raise ValueError(f"invalid or duplicate shader-map replacement: {key}")
        if not entry.get("source_essl_sha256"):
            raise ValueError(f"shader-map replacement is missing its source hash: {key}")
        replacements[key] = entry
    additions = delta.get("additions", [])
    mapped_hashes = {digest for _, digest in base_keys}
    for entry in additions:
        key = identity(entry)
        if not key[1] or not entry.get("source_essl_sha256"):
            raise ValueError(f"shader-map addition is missing a native or source hash: {key}")
        if key[1] in mapped_hashes:
            raise ValueError(f"shader-map addition has a duplicate native payload: {key}")
        mapped_hashes.add(key[1])
    if not replacements and not additions:
        raise ValueError("shader-map delta has no changes")

    return {
        **base,
        "mappings": [replacements.get(identity(entry), entry) for entry in mappings]
        + additions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("rootfs", type=Path,
                        help="realized rootfs containing opt/hmi/ID5/data/ro")
    parser.add_argument("repo_root", type=Path)
    args = parser.parse_args()

    try:
        data = json.loads(args.manifest.read_text())
        if data.get("schema") in DELTA_BASE_SCHEMAS:
            data = apply_map_delta(data, args.repo_root)
    except (OSError, KeyError, TypeError, ValueError) as error:
        parser.error(str(error))
    schema = data.get("schema")
    if schema not in (VERTEX_MAP, FRAGMENT_MAP):
        parser.error("unsupported shader-map manifest schema")
    if data.get("generation_failures") and schema == VERTEX_MAP:
        parser.error("shader-map manifest reports generation failures")
    mappings = data.get("mappings")
    if not isinstance(mappings, list) or not mappings:
        parser.error("shader-map manifest has no mappings")

    ro_root = args.rootfs / "opt/hmi/ID5/data/ro"
    checked: list[tuple[Path, Path]] = []
    try:
        for entry in mappings:
            asset_rel = safe_relative(entry["asset_path"], "asset path")
            source_rel = safe_relative(entry["source_path"], "source path")
            asset = ro_root / asset_rel
            source = args.repo_root / source_rel
            if not asset.is_file():
                raise ValueError(f"staged HMI shader is missing: {asset}")
            if not source.is_file():
                raise ValueError(f"reconstructed shader source is missing: {source}")
            expected_asset = entry.get("shader_sha256")
            if expected_asset and sha256(asset) != expected_asset:
                raise ValueError(f"staged HMI shader hash changed: {asset}")
            expected_source = entry.get("source_essl_sha256")
            if expected_source and sha256(source) != expected_source:
                raise ValueError(f"reconstructed ESSL hash changed: {source}")
            checked.append((asset, source))
    except (KeyError, TypeError, ValueError) as error:
        parser.error(str(error))

    for asset, source in checked:
        print(f"{asset}\t{source}")
    stage = "fragment" if schema == FRAGMENT_MAP else "vertex"
    print(f"validated {len(checked)} exact HMI {stage} shader maps", file=sys.stderr)
    if data.get("generation_failures"):
        print(f"skipping {len(data['generation_failures'])} unsupported {stage} translations",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
