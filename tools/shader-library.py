#!/usr/bin/env python3
"""Versioned, build-independent shader library + per-build pins.

The GLSL reconstructions of BMW's native SGX shaders do not depend on the firmware build: the same
shader *program* appears in many PSdZData releases, only its container hash and a compiler/version
field change (tools/buildinfo.py PROGRAM_MASK). So:

  tools/shaders/native-reconstructions/hmi-{vertex,fragment}-library.json
      one entry per (asset_path, program_sha256): GLSL source, basis, provenance.  Versioned by
      "library_version" (bump it when entries change meaning) and git history.
  builds/<id>/shader-pins.json
      {"vertex"|"fragment": {asset_path: {"shader_sha256": native file hash in this build,
                                           "program_sha256": its program fingerprint}}}
  composed map (runtime)  =  library entries whose (asset_path, program) is pinned by the build,
                             with shader_sha256 set to the build's native hash.

Commands
  pin     --build ID --rootfs ROOTFS [--write]   pin library programs found in a staged rootfs
  compose --build ID --out DIR [--rootfs R]      write hmi-vertex-map.json / hmi-fragment-map.json
  sync    --build ID --rootfs ROOTFS             move entries that generators appended with a
                                                 native shader_sha256 into library + pins
  init    --build ID --rootfs ROOTFS --vertex MAP --fragment MAP   create the library (migration)
ROOTFS is a staged tree that contains opt/hmi/ID5/data/ro (e.g. ~/.cache/idrive6/firmware/<release>/rootfs).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import buildinfo  # noqa: E402

MAPS = buildinfo.REPO / "tools/shaders/native-reconstructions"
STAGES = ("vertex", "fragment")
LIBRARY_SCHEMA = "bimmulator-shader-library-v1"


def library_path(stage: str) -> Path:
    return MAPS / f"hmi-{stage}-library.json"


def load_library(stage: str) -> dict:
    return json.loads(library_path(stage).read_text())


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def data_ro(rootfs: Path) -> Path:
    ro = rootfs / "opt/hmi/ID5/data/ro"
    if not ro.is_dir():
        raise SystemExit(f"{rootfs} does not contain opt/hmi/ID5/data/ro")
    return ro


def fingerprint(ro: Path, asset: str) -> tuple[str, str] | None:
    path = ro / asset
    if not path.is_file():
        return None
    data = path.read_bytes()
    return buildinfo.hashlib.sha256(data).hexdigest(), buildinfo.program_sha256(data)


def cmd_init(args) -> None:
    build = buildinfo.get(args.build)
    ro = data_ro(args.rootfs)
    pins = {stage: {} for stage in STAGES}
    for stage, source in (("vertex", args.vertex), ("fragment", args.fragment)):
        manifest = json.loads(Path(source).read_text())
        entries = []
        for entry in manifest.pop("mappings"):
            found = fingerprint(ro, entry["asset_path"])
            if found is None or found[0] != entry.get("shader_sha256", found[0]):
                raise SystemExit(f"{entry['asset_path']}: not the pinned file in {ro}")
            native, program = found
            # Entries without a native hash (generated host shaders) apply by asset path at runtime;
            # the program fingerprint still decides whether another build may use them.
            hash_pinned = "shader_sha256" in entry
            entry = {k: v for k, v in entry.items() if k not in ("shader_sha256", "x20511i_shader_sha256")}
            entry["program_sha256"] = program
            entry["native_hash_pinned"] = hash_pinned
            entry["first_build"] = build.id
            entries.append(entry)
            pins[stage][entry["asset_path"]] = {"shader_sha256": native, "program_sha256": program}
        for key in ("derived_from", "purpose", "realized_rootfs"):
            manifest.pop(key, None)
        library = {"library_schema": LIBRARY_SCHEMA, "library_version": 1,
                   "program_fingerprint": buildinfo.PROGRAM_FINGERPRINT_VERSION,
                   "manifest_header": manifest, "mappings": entries}
        save_json(library_path(stage), library)
        print(f"{library_path(stage).name}: {len(entries)} entries")
    save_pins(build, pins)


def save_pins(build, pins: dict) -> None:
    data = {"schema": "bimmulator-shader-pins-v1", "build": build.id,
            "library_version": {stage: load_library(stage)["library_version"] for stage in STAGES}}
    for stage in STAGES:
        data[stage] = dict(sorted(pins[stage].items()))
    save_json(build.dir / "shader-pins.json", data)
    print(f"{build.dir / 'shader-pins.json'}: " + ", ".join(f"{s} {len(pins[s])}" for s in STAGES))


def compute_pins(ro: Path) -> tuple[dict, dict]:
    """Pins for every library entry whose program is present in this rootfs + a report."""
    pins = {stage: {} for stage in STAGES}
    report = {"pinned_same_file": 0, "pinned_new_container": 0, "program_changed": [], "asset_missing": []}
    for stage in STAGES:
        for entry in load_library(stage)["mappings"]:
            asset = entry["asset_path"]
            found = fingerprint(ro, asset)
            if found is None:
                report["asset_missing"].append(f"{stage}:{asset}")
                continue
            native, program = found
            if program != entry["program_sha256"]:
                report["program_changed"].append(f"{stage}:{asset}")
                continue
            pins[stage][asset] = {"shader_sha256": native, "program_sha256": program}
    # Same container hash as an existing build's pin vs. a re-pinned container (informational).
    known = {p["shader_sha256"] for b in buildinfo.all_builds() for s in STAGES
             for p in b.shader_pins().get(s, {}).values()}
    for stage in STAGES:
        for pin in pins[stage].values():
            key = "pinned_same_file" if pin["shader_sha256"] in known else "pinned_new_container"
            report[key] += 1
    # A program that changed for an asset may still be another library entry for the same asset.
    report["program_changed"] = [a for a in report["program_changed"]
                                 if a.split(":", 1)[1] not in pins[a.split(":", 1)[0]]]
    return pins, report


def cmd_pin(args) -> None:
    build = buildinfo.get(args.build)
    pins, report = compute_pins(data_ro(args.rootfs))
    print(json.dumps({k: (v if isinstance(v, int) else len(v)) for k, v in report.items()}))
    for item in report["program_changed"]:
        print("  program changed (needs a new library entry):", item)
    if args.write:
        save_pins(build, pins)


def cmd_compose(args) -> None:
    build = buildinfo.get(args.build)
    pins = build.shader_pins()
    args.out.mkdir(parents=True, exist_ok=True)
    for stage in STAGES:
        library = load_library(stage)
        manifest = dict(library["manifest_header"])
        mappings = []
        for entry in library["mappings"]:
            pin = pins.get(stage, {}).get(entry["asset_path"])
            if args.rootfs and not (data_ro(args.rootfs) / entry["asset_path"]).is_file():
                continue   # asset not staged for this profile/vehicle
            if pin and pin["program_sha256"] == entry["program_sha256"]:
                mapped = {k: v for k, v in entry.items()
                          if k not in ("program_sha256", "first_build", "native_hash_pinned")}
                if entry.get("native_hash_pinned", True):
                    mapped["shader_sha256"] = pin["shader_sha256"]
                mappings.append(mapped)
        manifest["mappings"] = mappings
        manifest["purpose"] = f"composed for build {build.id} from library v{library['library_version']}"
        save_json(args.out / f"hmi-{stage}-map.json", manifest)
        print(f"{args.out / f'hmi-{stage}-map.json'}: {len(mappings)} mappings")


def cmd_sync(args) -> None:
    """Generators append entries carrying a native shader_sha256; turn them into library entries."""
    build = buildinfo.get(args.build)
    ro = data_ro(args.rootfs)
    pins = build.shader_pins()
    for stage in STAGES:
        pins.setdefault(stage, {})
        library = load_library(stage)
        moved = 0
        seen = {(e["asset_path"], e.get("program_sha256")) for e in library["mappings"] if "program_sha256" in e}
        kept = []
        for entry in library["mappings"]:
            if "program_sha256" in entry:
                kept.append(entry)
                continue
            found = fingerprint(ro, entry["asset_path"])
            if found is None or found[0] != entry.get("shader_sha256", found[0]):
                raise SystemExit(f"{entry['asset_path']}: generator entry does not match {ro}")
            native, program = found
            hash_pinned = "shader_sha256" in entry
            entry = {k: v for k, v in entry.items() if k != "shader_sha256"}
            entry["program_sha256"], entry["first_build"] = program, build.id
            entry["native_hash_pinned"] = hash_pinned
            if (entry["asset_path"], program) in seen:   # regenerated: replace the old entry
                kept = [e for e in kept if (e["asset_path"], e.get("program_sha256")) != (entry["asset_path"], program)]
            kept.append(entry)
            pins[stage][entry["asset_path"]] = {"shader_sha256": native, "program_sha256": program}
            moved += 1
        library["mappings"] = kept
        save_json(library_path(stage), library)
        print(f"{stage}: {moved} generator entries moved into the library")
    save_pins(build, {s: pins[s] for s in STAGES})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init"); p.add_argument("--build", required=True); p.add_argument("--rootfs", type=Path, required=True)
    p.add_argument("--vertex", required=True); p.add_argument("--fragment", required=True); p.set_defaults(func=cmd_init)
    p = sub.add_parser("pin"); p.add_argument("--build", required=True); p.add_argument("--rootfs", type=Path, required=True)
    p.add_argument("--write", action="store_true"); p.set_defaults(func=cmd_pin)
    p = sub.add_parser("compose"); p.add_argument("--build", required=True); p.add_argument("--out", type=Path, required=True)
    p.add_argument("--rootfs", type=Path, help="staged rootfs: drop entries whose asset is not staged")
    p.set_defaults(func=cmd_compose)
    p = sub.add_parser("sync"); p.add_argument("--build", required=True); p.add_argument("--rootfs", type=Path, required=True)
    p.set_defaults(func=cmd_sync)
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
