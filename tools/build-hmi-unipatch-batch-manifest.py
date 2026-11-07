#!/usr/bin/env python3
"""Match captured HMI shader uploads to exact staged assets for QNX finalization."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_parser():
    path = Path(__file__).with_name("inspect-sgx-shader.py")
    spec = importlib.util.spec_from_file_location("idrive_inspect_sgx_shader", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load staged .shd parser: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rootfs", type=Path, help="realized X20511I rootfs")
    parser.add_argument("captures", type=Path, help="ANGLE shader capture directory")
    parser.add_argument("output", type=Path, help="new batch-input manifest")
    parser.add_argument("--stage", choices=("vertex", "fragment"), default="fragment")
    args = parser.parse_args()

    data_root = args.rootfs / "opt/hmi/ID5/data/ro"
    if not data_root.is_dir():
        parser.error(f"staged HMI assets are missing: {data_root}")
    if not args.captures.is_dir():
        parser.error(f"shader capture directory is missing: {args.captures}")
    if args.output.exists():
        parser.error(f"output already exists: {args.output}")

    inspector = load_parser()
    staged_by_hash: dict[str, list[Path]] = {}
    for asset in data_root.rglob("*.shd"):
        if asset.is_file():
            staged_by_hash.setdefault(sha256(asset), []).append(asset)

    matches: dict[str, dict] = {}
    for capture in sorted(args.captures.glob("shader-*.bin")):
        try:
            captured = inspector.parse_shader(capture)
        except (OSError, ValueError) as error:
            raise SystemExit(f"cannot parse captured shader {capture}: {error}") from error
        if captured.get("stage") != args.stage:
            continue
        digest = sha256(capture)
        assets = staged_by_hash.get(digest, [])
        if not assets:
            raise SystemExit(f"captured {args.stage} shader has no exact staged .shd match: {capture}")
        for asset in assets:
            staged = inspector.parse_shader(asset)
            if staged.get("stage") != args.stage:
                raise SystemExit(f"matching staged bytes parse as {staged.get('stage')}: {asset}")
        name = digest[:16]
        row = {
            "name": name,
            "stage": args.stage,
            "sha256": digest,
            "path": sorted(p.relative_to(data_root).as_posix() for p in assets)[0],
            "aliases": sorted(p.relative_to(data_root).as_posix() for p in assets),
        }
        previous = matches.get(name)
        if previous and previous["sha256"] != digest:
            raise SystemExit(f"truncated shader identity collision: {name}")
        matches[name] = row

    if not matches:
        parser.error(f"no exact captured {args.stage} shader uploads matched staged assets")
    manifest = {
        "schema": "idrive6-unipatch-batch-inputs-v1",
        "stage": args.stage,
        "inputs": [matches[name] for name in sorted(matches)],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"UNIPATCH_BATCH_INPUTS stage={args.stage} exact_matches={len(matches)} "
          f"manifest={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
