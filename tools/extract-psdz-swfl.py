#!/usr/bin/env python3
"""Extract NBTevo OMAP root/boot files without executing SWFL update commands."""

from __future__ import annotations

import argparse
import hashlib
import json
import mmap
from pathlib import Path, PurePosixPath
import struct
import sys
import xml.etree.ElementTree as ET
import zlib


HEADER = bytes.fromhex("01010001000000010001")
ROOT_PREFIX = "/fs/sda0/repository/istep/"


def relative_path(value: str) -> Path:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(p in {".", ".."} for p in path.parts):
        raise ValueError(f"unsafe container path: {value!r}")
    return Path(*path.parts)


def records(data: mmap.mmap):
    if data[:len(HEADER)] != HEADER:
        raise ValueError("unsupported SWFL header")
    offset = len(HEADER)
    while offset < len(data):
        if offset + 9 > len(data):
            raise ValueError(f"truncated record at {offset:#x}")
        kind = data[offset]
        ident, length, flags = struct.unpack_from("<HIH", data, offset + 1)
        end = offset + 9 + length
        if end > len(data) or kind not in {2, 3, 4} or (kind != 2 and flags == 0):
            raise ValueError(f"unsupported or truncated record at {offset:#x}")
        yield kind, ident, flags, offset + 9, end
        offset = end


def extract(package: Path, output: Path, inventory: dict) -> None:
    pending = {}
    with package.open("rb") as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        inventory["packages"].append({
            "name": package.name,
            "sha256": hashlib.sha256(data).hexdigest(),
            "nbtevo_x20511i": data.find(b"NBTevo_X20511I") >= 0,
        })
        for kind, ident, part, start, end in records(data):
            if kind == 2:
                text = data[start:end].decode("utf-8")
                fields = dict(field.split("=", 1) for field in text.split(";") if "=" in field)
                if ident in pending:
                    raise ValueError(f"metadata {ident} replaces an incomplete payload")
                if part:
                    pending[ident] = {"fields": fields, "count": part, "chunks": []}
                continue
            item = pending.get(ident)
            if item is None:
                raise ValueError(f"payload {ident} has no metadata")
            if part != len(item["chunks"]) + 1 or part > item["count"]:
                raise ValueError(f"payload {ident} has an invalid part number")
            item["chunks"].append((start, end))
            if part != item["count"]:
                continue
            del pending[ident]
            fields = item["fields"]
            if fields.get("Tag") != "FIL" or fields.get("CPU") != "Omap":
                continue
            if kind != 4:
                raise ValueError(f"unsupported FIL payload encoding for {ident}")
            target = fields.get("TargetPath", "")
            name = fields.get("Name", "")
            if "/" in name or not name or "Offset" in fields:
                raise ValueError(f"unsupported file metadata: {fields}")
            if target.startswith(ROOT_PREFIX):
                path = Path("rootfs") / relative_path(target[len(ROOT_PREFIX):] + name)
            elif target == "/fs/sda2/":
                path = Path("sda2") / relative_path(name)
            else:
                inventory["skipped_targets"].append({"target": target, "name": name})
                continue
            destination = output / path
            hasher = hashlib.sha256()
            for lo, hi in item["chunks"]:
                hasher.update(data[lo:hi])
            digest = hasher.hexdigest()
            append = fields.get("Append") == "On" and destination.exists()
            if destination.exists():
                if append:
                    if inventory["files"][path.as_posix()]["package"] != package.name:
                        raise ValueError(f"append crosses package boundary: {path}")
                elif hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
                    raise ValueError(f"conflicting package files: {path}")
                else:
                    continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("ab" if append else "wb") as target_stream:
                for lo, hi in item["chunks"]:
                    target_stream.write(data[lo:hi])
            chunks = inventory["files"][path.as_posix()]["chunks"] + item["chunks"] if append else item["chunks"]
            inventory["files"][path.as_posix()] = {
                "package": package.name, "chunks": chunks,
                "size": destination.stat().st_size,
                "sha256": hashlib.sha256(destination.read_bytes()).hexdigest() if append else digest,
            }
        if pending:
            raise ValueError(f"incomplete payloads in {package.name}")


def verify_manifests(output: Path) -> dict:
    root = output / "rootfs"
    checked = set()
    missing = set()
    logical_hash_sources = {}

    def visit(element, parent):
        for entry in element:
            if entry.tag not in {"dir", "file"}:
                continue
            path = parent / relative_path(entry.attrib["name"])
            if entry.tag == "dir":
                path.mkdir(parents=True, exist_ok=True)
                visit(entry, path)
            elif not path.is_file():
                missing.add(path.relative_to(root).as_posix())
                continue
            else:
                data = path.read_bytes()
                digest = entry.get("md5", "")
                # BMW's manifest calls this attribute md5 even when it holds SHA-1.
                if len(digest) == 40:
                    actual = hashlib.sha1(data).hexdigest()
                elif len(digest) == 32:
                    actual = hashlib.md5(data).hexdigest()
                elif digest:
                    raise ValueError(f"unknown manifest digest for {path}")
                if digest and digest.lower() != actual:
                    # BMW's zipped/HmiMain3D entry uses the unpacked ELF's
                    # SHA-1 and the compressed file's CRC, unlike other files.
                    unpacked = path.parent.parent / path.name
                    if (path.parent.name == "zipped" and data.startswith(b"\x00\xe9LZO\xff")
                            and unpacked.is_file()
                            and hashlib.sha1(unpacked.read_bytes()).hexdigest() == digest.lower()):
                        logical_hash_sources[path.relative_to(root).as_posix()] = unpacked.relative_to(root).as_posix()
                    else:
                        raise ValueError(f"manifest checksum mismatch: {path}")
                crc = entry.get("crc")
                if crc and int(crc, 16) != zlib.crc32(data):
                    raise ValueError(f"manifest CRC mismatch: {path}")
                if digest or crc:
                    checked.add(path.relative_to(root).as_posix())
            path.chmod(int(entry.attrib["mod"], 8))

    for manifest in sorted((root / "info").glob("manifest_*.xml")):
        tree = ET.parse(manifest)
        for link_data in tree.iter("LinkData"):
            if link_data.get("root", "").rstrip("/") != ROOT_PREFIX.rstrip("/"):
                raise ValueError(f"unsupported manifest root in {manifest}")
            visit(link_data, root)
    return {"verified_files": len(checked), "missing_files": sorted(missing - checked),
            "logical_hash_sources": logical_hash_sources}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packages", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True, help="new directory for extracted rootfs and boot images")
    args = parser.parse_args()
    try:
        output = args.output.resolve()
        if output.exists():
            raise ValueError(f"output directory already exists: {output}")
        output.mkdir(parents=True)
        inventory = {"packages": [], "files": {}, "skipped_targets": []}
        for package in args.packages:
            extract(package, output, inventory)
        inventory["manifests"] = verify_manifests(output)
        (output / "extraction.json").write_text(json.dumps(inventory, indent=2) + "\n")
        print(f"Extracted {len(inventory['files'])} OMAP files into {output}")
        print(f"Verified {inventory['manifests']['verified_files']} files against BMW manifest checksums")
        print(f"Manifest entries without payloads: {len(inventory['manifests']['missing_files'])}")
        if any(p["nbtevo_x20511i"] for p in inventory["packages"]):
            print("Found firmware version marker NBTevo_X20511I")
    except (OSError, ValueError, UnicodeError, ET.ParseError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
