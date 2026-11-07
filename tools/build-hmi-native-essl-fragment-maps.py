#!/usr/bin/env python3
"""Generate exact-byte HMI fragment maps from cached QNX finalizer results."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FINALIZER = ROOT / "build/idrive6-cache/evidence/unipatch-hmi-fragment-batch-v32c/manifest.json"
DEFAULT_USSE = ROOT / "build/idrive6-cache/evidence/usse-hmi-fragment-batch-v32c/manifest.json"
DEFAULT_RECOMPILER = ROOT / "build/idrive6-cache/usse-recompiler/idrive-usse-graphics"
DEFAULT_OUTPUT = ROOT / "tools/shaders/native-reconstructions/hmi-fragment"
DEFAULT_MAP = ROOT / "tools/shaders/native-reconstructions/hmi-fragment-map.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rootfs", type=Path,
                        help="realized staged rootfs containing opt/hmi/ID5/data/ro")
    parser.add_argument("--finalizer-manifest", type=Path, default=DEFAULT_FINALIZER)
    parser.add_argument("--usse-manifest", type=Path, default=DEFAULT_USSE)
    parser.add_argument("--recompiler", type=Path, default=DEFAULT_RECOMPILER)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--map-manifest", type=Path, default=DEFAULT_MAP)
    args = parser.parse_args()

    rootfs = args.rootfs.resolve()
    args.output_dir = args.output_dir.resolve()
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
    work_dir = ROOT / "build/idrive6-cache/native-register-hmi-fragment"
    work_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rectangle_path = ro_root / "common/shader/Rectangle_fragment.shd"
    if not rectangle_path.is_file():
        parser.error(f"exact Rectangle fragment source map is missing its .shd: {rectangle_path}")
    rectangle_hash = digest(rectangle_path.read_bytes())

    mappings = []
    failures = []
    translated_count = 0
    for name, translation in usse_rows.items():
        final = finalizer_rows.get(name)
        if not final or final.get("status") != "passed":
            failures.append({"name": name, "reason": "no passed QNX fragment finalizer record"})
            continue
        if translation.get("status") != "translated":
            failures.append({"name": name, "reason": translation.get("stderr") or translation.get("status")})
            continue
        if translation.get("spirv_validation", {}).get("status") != "valid":
            failures.append({"name": name, "reason": "translated SPIR-V did not pass spirv-val"})
            continue
        asset_path = final.get("asset_path")
        if not asset_path:
            failures.append({"name": name, "reason": "finalizer row has no exact staged asset path"})
            continue
        shader_path = ro_root / asset_path
        if not shader_path.is_file():
            failures.append({"name": name, "reason": f"missing staged shader: {asset_path}"})
            continue
        shader_bytes = shader_path.read_bytes()
        shader_hash = digest(shader_bytes)
        if shader_hash != final.get("source_sha256"):
            failures.append({"name": name, "reason": f"staged shader hash mismatch: {asset_path}"})
            continue
        # Rectangle's byte-identical fragment already has a captured, ANGLE-
        # compiled source map. Avoid a same-hash map collision.
        if shader_hash == rectangle_hash:
            continue
        fixture_dir = args.finalizer_manifest.parent / name
        spv_path = work_dir / f"{name}.fragment.graphics.spv"
        candidate_path = work_dir / f"{name}.fragment.cross.glsl"
        source_path = args.output_dir / f"{name}.glsl"
        metadata_path = args.output_dir / f"{name}.json"
        compiled = run([str(args.recompiler.resolve()), str(fixture_dir.resolve()),
                        "fragment", str(spv_path.resolve())])
        if compiled.returncode != 0:
            failures.append({"name": name, "reason": compiled.stderr.strip() or compiled.stdout.strip()})
            continue
        crossed = run([spirv_cross, str(spv_path), "--version", "300", "--es",
                       "--output", str(candidate_path)])
        if crossed.returncode != 0:
            failures.append({"name": name, "reason": crossed.stderr.strip() or crossed.stdout.strip()})
            continue
        adapted = run([sys.executable, str(ROOT / "tools/make-hmi-essl-from-fragment-usse.py"),
                       str(shader_path), str(candidate_path),
                       str(fixture_dir / "fragment.table_44.bin"),
                       str(fixture_dir / "fragment.table_54.bin"), str(source_path),
                       "--metadata", str(metadata_path)])
        if adapted.returncode != 0:
            failures.append({"name": name, "reason": adapted.stderr.strip() or adapted.stdout.strip()})
            continue
        source_bytes = source_path.read_bytes()
        interface = json.loads(metadata_path.read_text())
        translated_count += 1
        mappings.append({
            "asset_path": asset_path,
            "source_path": source_path.relative_to(ROOT).as_posix(),
            "shader_sha256": shader_hash,
            "source_essl_sha256": digest(source_bytes),
            "samplers": interface["samplers"],
            "mapped_sampler_candidate": interface["mapped_sampler_candidate"],
            "unmapped_sampler_symbols": interface["unmapped_sampler_symbols"],
            "sample_pa_register_candidate": interface["sample_pa_register_candidate"],
            "uv_input": interface["uv_input"],
            "sample_result_candidate": interface["sample_result_candidate"],
            "sample_result_native_verified": interface["sample_result_native_verified"],
            "sample_result_adapter": interface.get("sample_result_adapter"),
            "host_interface_adapter": interface.get("host_interface_adapter"),
            "native_uniform_adapters": interface.get("native_uniform_adapters", []),
            "output_byte_order_candidate": interface["output_byte_order_candidate"],
            "output_byte_order_native_verified": interface["output_byte_order_native_verified"],
            "basis": ("exact .shd symbols, native finalizer tables and translated SMP instructions; sampler keys 10/14 are tied to t/t_rse; coordinate, texture format, sample lane and output packing remain candidates"
                      if interface.get("native_smp_interface") else
                      "exact .shd symbols + cached BMW UniPatch input/constant tables + native USSE translation; sample PA is derived from the matching input row and vec2 varying; per-shader sample component adapters are explicit candidates; native output lane packing remains unverified"),
        })

    try:
        rootfs_reference = rootfs.relative_to(ROOT).as_posix()
    except ValueError:
        rootfs_reference = rootfs.name
    manifest = {
        "schema": "idrive6-hmi-exact-fragment-map-v1",
        "realized_rootfs": rootfs_reference,
        "finalizer_manifest_sha256": digest(args.finalizer_manifest.read_bytes()),
        "usse_manifest_sha256": digest(args.usse_manifest.read_bytes()),
        "sample_result_candidate": "full_rgba",
        "sample_result_native_verified": False,
        "output_byte_order_candidate": "packed_lsb_to_rgba",
        "output_byte_order_native_verified": False,
        "mappings": mappings,
        "generation_failures": failures,
        "scope": "native fragment USSE adapted to HMI ESSL; texture results preserve RGBA and native IMG output lane remains unverified",
    }
    args.map_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.map_manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"HMI_FRAGMENT_ESSL_MAPS generated={translated_count} maps={len(mappings)} "
          f"generation_failures={len(failures)} sample=full_rgba "
          f"manifest={args.map_manifest}")
    for failure in failures:
        print(f"HMI_FRAGMENT_ESSL_MAP_FAIL {failure['name']}: {failure['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
