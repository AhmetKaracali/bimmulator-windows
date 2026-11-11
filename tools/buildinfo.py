#!/usr/bin/env python3
"""Firmware build registry: everything that differs between head-unit software builds.

Every supported PSdZData/head-unit build has a folder builds/<id>/ with
  build.json          packages, binary hashes, patch sites, controller hook addresses, vehicle
  profiles/*.json     emulator profiles (variants) for this build
  shader-pins.json    which native shader file of this build carries which library program

Code that needs a build-specific value calls current_build() (selected by $IDRIVE_BUILD, an id
or a path to build.json; the launcher sets it) instead of hard-coding offsets.

    python3 tools/buildinfo.py list                 # registered builds
    python3 tools/buildinfo.py detect /psdzdata     # which build matches these packages
    python3 tools/buildinfo.py show [id]            # resolved build.json
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

SCHEMA = "bimmulator-build-v1"
REPO = Path(__file__).resolve().parent.parent
BUILDS = REPO / "builds"
DEFAULT_BUILD = "hu-006.027.001"

# Bytes of an SGX shader container that change between firmware builds although the shader
# program is the same: 4..7 (container hash) and 59..67 (compiler/version field in the stage
# information). Verified on all 99 shaders that differ between HU 006.027.001 and 007.030.001.
PROGRAM_MASK = ((4, 8), (59, 68))
PROGRAM_FINGERPRINT_VERSION = 1


def program_sha256(data: bytes) -> str:
    """Build-independent fingerprint of a native SGX shader program (see PROGRAM_MASK)."""
    if data[:4] != bytes.fromhex("38b4fa10") or len(data) < 72:
        return hashlib.sha256(data).hexdigest()
    masked = bytearray(data)
    for start, end in PROGRAM_MASK:
        masked[start:end] = b"\0" * (end - start)
    return hashlib.sha256(masked).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(4 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def hexint(value) -> int:
    return value if isinstance(value, int) else int(str(value), 16)


def hexbytes(value) -> bytes:
    return bytes.fromhex(str(value))


def patch_triple(item) -> tuple[int, bytes, bytes]:
    """["0x648A0", "16 00 00 0a", "00 00 a0 e1"] -> (offset, expected, replacement)."""
    offset, expected, replacement = item
    return hexint(offset), hexbytes(expected), hexbytes(replacement)


class Build(dict):
    """A loaded build.json with its folder."""

    @property
    def dir(self) -> Path:
        return Path(self["_dir"])

    @property
    def id(self) -> str:
        return self["id"]

    def profile(self, name: str | None = None) -> Path:
        name = name or self["default_profile"]
        path = self.dir / "profiles" / f"{name}.json"
        if not path.is_file():
            available = sorted(p.stem for p in (self.dir / "profiles").glob("*.json"))
            raise ValueError(f"build {self.id} has no profile {name!r}; available: {', '.join(available)}")
        return path

    def shader_pins(self) -> dict:
        path = self.dir / "shader-pins.json"
        return json.loads(path.read_text()) if path.is_file() else {"vertex": {}, "fragment": {}}


def load(path: Path) -> Build:
    data = json.loads(path.read_text())
    if data.get("schema") != SCHEMA:
        raise ValueError(f"{path}: schema must be {SCHEMA}")
    if data.get("id") != path.parent.name:
        raise ValueError(f"{path}: id {data.get('id')!r} must equal its folder name {path.parent.name!r}")
    build = Build(data)
    build["_dir"] = str(path.parent)
    return build


def all_builds() -> list[Build]:
    return [load(p) for p in sorted(BUILDS.glob("*/build.json"))]


def get(build_id_or_path: str) -> Build:
    candidate = Path(build_id_or_path)
    if candidate.suffix == ".json" and candidate.is_file():
        return load(candidate)
    if candidate.is_dir() and (candidate / "build.json").is_file():
        return load(candidate / "build.json")
    path = BUILDS / build_id_or_path / "build.json"
    if not path.is_file():
        known = ", ".join(b.id for b in all_builds())
        raise ValueError(f"unknown build {build_id_or_path!r}; registered builds: {known}")
    return load(path)


def current_build() -> Build:
    return get(os.environ.get("IDRIVE_BUILD") or DEFAULT_BUILD)


def detect(psdzdata: Path, verify: bool = True) -> tuple[Build, dict[str, Path], dict[str, str]]:
    """Find the registered build whose head-unit packages are present (and hash-identical)."""
    root = psdzdata / "swe/swfl"
    reasons = []
    for build in all_builds():
        names = build["packages"]
        if not all((root / name).is_file() for name in names):
            reasons.append(f"{build.id}: packages not present")
            continue
        paths = {name: root / name for name in names}
        digests = {}
        mismatch = None
        for name, expected in names.items():
            actual = sha256_file(paths[name]) if verify else expected
            if actual != expected:
                mismatch = f"{build.id}: {name} SHA-256 {actual} != {expected}"
                break
            digests[name] = actual
        if mismatch:
            reasons.append(mismatch)
            continue
        return build, paths, digests
    raise ValueError(
        f"No registered build matches the head-unit packages in {root}.\n  "
        + "\n  ".join(reasons)
        + "\nSee builds/README.md to add your firmware build (tools/port-build.py does most of the work)."
    )


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "list"
    if command == "list":
        for build in all_builds():
            print(f"{build.id:22} {build['status']:9} {build['title']}")
        return 0
    if command == "detect" and len(sys.argv) == 3:
        build, _, _ = detect(Path(sys.argv[2]))
        print(build.id)
        return 0
    if command == "show":
        build = get(sys.argv[2]) if len(sys.argv) > 2 else current_build()
        print(json.dumps({k: v for k, v in build.items() if k != "_dir"}, indent=2))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
