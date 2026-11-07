#!/usr/bin/env python3
"""Stage extracted PSdZData system directories as an emulator root."""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys


ROOT_DIRECTORIES = ("bin", "lib", "etc", "usr", "info")
# The release emulator runs the base system and the graphics/car runtime. It
# does not run Connectivity or Media packages, or the RPM installer payloads;
# they add bulk and competing starter packages to this graphics-only profile.
# Keep the Connectivity and Media mount points empty, as in the verified root.
OPT_DIRECTORIES = ("sys", "core", "car")


def exclude_runtime_payloads(source: Path, directory: str, names: list[str]) -> list[str]:
    """Omit firmware packages/assets that are not used by the iDrive HMI."""
    current = Path(directory).resolve()
    if current == (source / "opt/car/data").resolve() and "eva" in names:
        return ["eva"]
    if current == (source / "opt/sys/rpm").resolve() and "lib" in names:
        return ["lib"]
    return []


def stage(source: Path, destination: Path) -> None:
    source, destination = source.resolve(), destination.resolve()
    if not source.is_dir():
        raise RuntimeError(f"extracted PSdZData root is not a directory: {source}")
    if destination.exists():
        raise RuntimeError(f"destination already exists: {destination}")
    missing = [name for name in ROOT_DIRECTORIES if not (source / name).is_dir()]
    missing.extend(f"opt/{name}" for name in OPT_DIRECTORIES if not (source / "opt" / name).is_dir())
    if missing:
        raise RuntimeError(f"PSdZData root is missing: {', '.join(missing)}")
    destination.mkdir(parents=True)
    for name in ROOT_DIRECTORIES:
        shutil.copytree(source / name, destination / name, symlinks=True)
    for name in OPT_DIRECTORIES:
        target = destination / "opt" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        ignore = None
        if name in {"sys", "car"}:
            ignore = lambda directory, names: exclude_runtime_payloads(
                source, directory, names
            )
        shutil.copytree(source / "opt" / name, target, symlinks=True, ignore=ignore)
    for name in ("conn", "mm"):
        (destination / "opt" / name).mkdir(parents=True, exist_ok=True)
    graphics = destination / "lib/graphics"
    versioned = graphics / "omap5430_ES2_0"
    stable = graphics / "omap5430"
    if not stable.exists() and versioned.is_dir():
        stable.symlink_to(versioned.name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("psdzdata_root", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        stage(args.psdzdata_root, args.destination)
    except (OSError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Staged iDrive root tree at {args.destination.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
