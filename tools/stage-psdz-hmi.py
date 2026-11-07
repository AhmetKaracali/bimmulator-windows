#!/usr/bin/env python3
"""Stage a bounded NBTevo HMI runtime from an extracted PSdZData root."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys


def copy_entry(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        if destination.exists() or destination.is_symlink():
            if destination.is_dir() and not destination.is_symlink():
                shutil.rmtree(destination)
            else:
                destination.unlink()
        destination.symlink_to(source.readlink())
    elif source.is_dir():
        shutil.copytree(source, destination, symlinks=True, dirs_exist_ok=True)
    else:
        shutil.copy2(source, destination, follow_symlinks=False)


def ensure_alias(path: Path, target: str) -> None:
    if path.is_symlink():
        if path.readlink() == Path(target):
            return
        path.unlink()
    elif path.exists():
        raise RuntimeError(f"cannot create HMI alias over existing path: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to(target)


def copy_filtered_tree(
    source_root: Path,
    destination_root: Path,
    excluded_roots: set[Path],
) -> int:
    destination_root.mkdir(parents=True, exist_ok=True)
    copied = 0

    def visit(source: Path, relative: Path) -> None:
        nonlocal copied
        for entry in source.iterdir():
            child_relative = relative / entry.name
            if any(
                child_relative == excluded
                or excluded in child_relative.parents
                for excluded in excluded_roots
            ):
                continue
            destination = destination_root / child_relative
            if entry.is_symlink():
                copy_entry(entry, destination)
                copied += 1
            elif entry.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                visit(entry, child_relative)
            else:
                copy_entry(entry, destination)
                copied += 1

    visit(source_root, Path())
    return copied


def stage(source_root: Path, destination_root: Path, vehicle: str, theme: str) -> int:
    source_root = source_root.resolve()
    destination_root = destination_root.resolve()
    if not source_root.is_dir():
        raise RuntimeError(f"PSdZData runtime root is not a directory: {source_root}")
    if not destination_root.is_dir():
        raise RuntimeError(f"staged emulator root is not a directory: {destination_root}")

    hmi_source = source_root / "opt/hmi"
    id5_source = hmi_source / "ID5"
    data_root = id5_source / "data/ro"
    required = (
        id5_source / "bin/HmiMain3D",
        id5_source / "lib",
        data_root / "app",
        data_root / "common",
        data_root / "hmiplugins",
        data_root / "bmw" / theme,
        data_root / "bmw/widgetasset/vehicles" / vehicle,
        hmi_source / "otf",
    )
    missing = [path for path in required if not path.exists()]
    if missing:
        raise RuntimeError(
            "PSdZData HMI runtime is incomplete: "
            + ", ".join(str(path.relative_to(source_root)) for path in missing)
        )

    destination_hmi = destination_root / "opt/hmi"
    destination_id5 = destination_hmi / "ID5"
    copied = 0
    for directory in ("bin", "lib"):
        source = id5_source / directory
        target = destination_id5 / directory
        shutil.copytree(source, target, symlinks=True, dirs_exist_ok=True)
        copied += sum(1 for path in source.rglob("*") if path.is_file())

    target_data = destination_id5 / "data/ro"
    if target_data.exists():
        shutil.rmtree(target_data)
    excluded = {
        Path("common/assetDB/Domains"),
        Path("common/ego_model"),
        Path("common/widgetasset/active_seating_animations"),
        Path("bmw") / theme / "assetDB/Domains/Vehicle",
        Path("bmw") / theme / "assetDB/Domains/MyVehicle",
        Path("bmw/widgetasset/vehicles"),
    }
    for entry in data_root.iterdir():
        if entry.is_dir() and entry.name not in {"app", "common", "hmiplugins", "bmw"}:
            excluded.add(Path(entry.name))
    for entry in (data_root / "bmw").iterdir():
        if entry.is_dir() and entry.name not in {theme, "db", "widgetasset"}:
            excluded.add(Path("bmw") / entry.name)
    copied += copy_filtered_tree(
        data_root,
        target_data,
        excluded,
    )
    f32_assets = data_root / "bmw/widgetasset/vehicles" / vehicle
    f32_target = target_data / "bmw/widgetasset/vehicles" / vehicle
    shutil.copytree(f32_assets, f32_target, symlinks=True, dirs_exist_ok=True)
    copied += sum(1 for path in f32_assets.rglob("*") if path.is_file())

    for relative in (Path("otf"), Path("scripts")):
        source = hmi_source / relative
        if source.exists():
            shutil.copytree(
                source,
                destination_hmi / relative,
                symlinks=True,
                dirs_exist_ok=True,
            )
            copied += sum(1 for path in source.rglob("*") if path.is_file())

    ensure_alias(destination_hmi / "lib", "ID5/lib")
    ensure_alias(destination_hmi / "data", "ID5/data")
    ensure_alias(destination_hmi / "bin", "ID5/bin")
    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("psdzdata_root", type=Path, help="extracted NBTevo PSdZData root")
    parser.add_argument("staged_root", type=Path, help="existing emulator rootfs staging directory")
    parser.add_argument("--vehicle", default="F32", help="BMW vehicle asset code (default: F32)")
    parser.add_argument("--theme", default="id6l", help="BMW HMI resource theme (default: id6l)")
    args = parser.parse_args()
    try:
        count = stage(args.psdzdata_root, args.staged_root, args.vehicle, args.theme)
    except (OSError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(
        f"Staged NBTevo HMI resources ({args.theme}, {args.vehicle}) into "
        f"{args.staged_root.resolve()} ({count} files checked/copied)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
