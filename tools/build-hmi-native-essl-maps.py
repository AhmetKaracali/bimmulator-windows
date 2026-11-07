#!/usr/bin/env python3
"""Generate exact-byte HMI vertex shader maps from cached QNX finalizer output.

Run in `nix develop path:.#shader`. This consumes the already-realized rootfs,
BMW finalizer manifest, and translated-shader manifest; it does not re-extract
PSdZData or call the QNX finalizer again.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FINALIZER_MANIFEST = ROOT / "build/idrive6-cache/evidence/unipatch-hmi-vertex-batch-2026-11-02-v3/manifest.json"
DEFAULT_USSE_MANIFEST = ROOT / "build/idrive6-cache/evidence/usse-hmi-vertex-batch-2026-11-02-v3/manifest.json"
DEFAULT_RECOMPILER = ROOT / "build/idrive6-cache/usse-recompiler/idrive-usse-graphics"
DEFAULT_OUTPUT = ROOT / "tools/shaders/native-reconstructions/hmi-vertex"
DEFAULT_MAP = ROOT / "tools/shaders/native-reconstructions/hmi-vertex-map.json"
RECTANGLE_NAME = "79531e019d6b4098"
STATUSBAR_NAME = "ddc68e69ebab4e84"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rootfs", type=Path,
                        help="realized staged rootfs containing opt/hmi/ID5/data/ro")
    parser.add_argument("--finalizer-manifest", type=Path,
                        default=DEFAULT_FINALIZER_MANIFEST)
    parser.add_argument("--usse-manifest", type=Path,
                        default=DEFAULT_USSE_MANIFEST)
    parser.add_argument("--recompiler", type=Path, default=DEFAULT_RECOMPILER)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--map-manifest", type=Path, default=DEFAULT_MAP)
    args = parser.parse_args()

    rootfs = args.rootfs.resolve()
    args.output_dir = args.output_dir.resolve()
    args.map_manifest = args.map_manifest.resolve()
    ro_root = rootfs / "opt/hmi/ID5/data/ro"
    if not ro_root.is_dir():
        parser.error(f"realized BMW data directory is missing: {ro_root}")
    if not args.recompiler.is_file():
        parser.error(f"native-register USSE recompiler is missing: {args.recompiler}")
    spirv_cross = shutil.which("spirv-cross")
    if not spirv_cross:
        parser.error("spirv-cross is missing; enter the pinned Nix shader shell")

    finalizer = json.loads(args.finalizer_manifest.read_text())
    usse = json.loads(args.usse_manifest.read_text())
    finalizer_rows = {row["name"]: row for row in finalizer["results"]}
    usse_rows = {row["name"]: row for row in usse["results"]}
    work_dir = ROOT / "build/idrive6-cache/native-register-hmi-vertex"
    work_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    mappings = [{
        "asset_path": "common/shader/Rectangle_vertex.shd",
        "source_path": "tools/shaders/native-reconstructions/Rectangle_vertex.glsl",
        "basis": "previously ANGLE-compiled exact Rectangle reconstruction",
    }]
    failures = []
    translated_count = 0
    for name, translation in usse_rows.items():
        if translation.get("status") != "translated":
            continue
        final = finalizer_rows.get(name)
        if not final or final.get("status") != "passed":
            failures.append({"name": name, "reason": "no passed QNX finalizer record"})
            continue
        asset_path = final.get("asset_path")
        shader_path = ro_root / asset_path
        if not shader_path.is_file():
            failures.append({"name": name, "reason": f"missing staged shader: {asset_path}"})
            continue
        shader_bytes = shader_path.read_bytes()
        if digest(shader_bytes) != final.get("source_sha256"):
            failures.append({"name": name, "reason": f"staged shader hash mismatch: {asset_path}"})
            continue
        if name == RECTANGLE_NAME:
            continue

        fixture_dir = args.finalizer_manifest.parent / name
        spv_path = work_dir / f"{name}.spv"
        cross_path = work_dir / f"{name}.essl.cross.glsl"
        metadata_path = args.output_dir / f"{name}.json"
        if name == STATUSBAR_NAME:
            source_path = ROOT / "tools/shaders/native-reconstructions/mat_statusbar.vert.glsl"
        else:
            source_path = args.output_dir / f"{name}.glsl"
        metadata_path = source_path.with_suffix(".json")

        compiled = run([str(args.recompiler), str(fixture_dir), "vertex",
                        str(spv_path), "--native-register-interface"])
        if compiled.returncode != 0:
            failures.append({"name": name, "reason": compiled.stderr.strip() or compiled.stdout.strip()})
            continue
        crossed = run([spirv_cross, str(spv_path), "--version", "300", "--es",
                       "--output", str(cross_path)])
        if crossed.returncode != 0:
            failures.append({"name": name, "reason": crossed.stderr.strip() or crossed.stdout.strip()})
            continue
        adapted = run([sys.executable, str(ROOT / "tools/make-hmi-essl-from-usse.py"),
                       str(shader_path), str(cross_path),
                       str(fixture_dir / "vertex.table_54.bin"),
                       str(source_path), "--metadata", str(metadata_path)])
        if adapted.returncode != 0:
            failures.append({"name": name, "reason": adapted.stderr.strip() or adapted.stdout.strip()})
            continue
        translated_count += 1
        mappings.append({
            "asset_path": asset_path,
            "source_path": source_path.relative_to(ROOT).as_posix(),
            "shader_sha256": digest(shader_bytes),
            "source_essl_sha256": digest(source_path.read_bytes()),
            "basis": "exact .shd symbols + cached QNX finalizer constants + native-register USSE translation",
        })

    try:
        rootfs_reference = rootfs.relative_to(ROOT).as_posix()
    except ValueError:
        rootfs_reference = rootfs.name
    manifest = {
        "schema": "idrive6-hmi-exact-vertex-map-v1",
        "realized_rootfs": rootfs_reference,
        "finalizer_manifest_sha256": digest(args.finalizer_manifest.read_bytes()),
        "usse_manifest_sha256": digest(args.usse_manifest.read_bytes()),
        "mappings": mappings,
        "generation_failures": failures,
    }
    args.map_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.map_manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"HMI_NATIVE_ESSL_MAPS generated={translated_count} total_maps={len(mappings)} "
          f"generation_failures={len(failures)} manifest={args.map_manifest}")
    for failure in failures:
        print(f"HMI_NATIVE_ESSL_MAP_FAIL {failure['name']}: {failure['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
