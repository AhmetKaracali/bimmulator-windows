#!/usr/bin/env python3
"""
Builds overlay.tar for the WSL2 iDrive emulator (wsl/overlay.sh calls this).

The guest downloads overlay.tar right before HmiMain3D starts and extracts it onto its root
volume, so everything here replaces or adds files without touching the emulator's staged root
or the pre-starter snapshot. Contents:

  * --plugins DIR (<DIR>/<Name>/) -> opt/hmi/ID5/data/ro/Plugins/<Name>/   (your RA plugins)
  * --car-coding <ncd>            -> opt/hmi/ID5/lib/libhmicoding.so
        The emulator makes HmiMain3D read BMW's built-in default coding pages from
        libhmicoding.so. We write a car's own HU coding pages (IDriveReader NCD backup) into those
        defaults, then re-apply only the bits the emulator needs to run (ID6 Light menu, 1440x540
        CID with touch, en-US text, developer menu, reversing-camera system).
  * --vehicle F30                 -> variantregistry.pbvar + bmw/widgetasset/vehicles/F30/
        Points the 3D vehicle (My Vehicle, camera crane) at the car's own body style.

Run inside WSL (car006 = HU 006.027.001, staged with the F30 body):
  python3 make_overlay.py --language en-us -o ~/idrive/overlay/overlay.tar
  python3 make_overlay.py --car-coding <hu_coding_backup.ncd> --language tr -o ~/idrive/overlay/overlay.tar
  python3 make_overlay.py --firmware x20511i --car-coding <ncd> --vehicle F30 -o ...   (stock 007 build)
"""
from __future__ import annotations

import os
import argparse
import hashlib
import io
import struct
import sys
import tarfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
GUEST_RO = "opt/hmi/ID5/data/ro"
CACHE = Path(os.environ.get("IDRIVE_CACHE", Path.home() / ".cache" / "idrive6"))   # launcher cacheDir
CODING_PATH = "opt/hmi/ID5/lib/libhmicoding.so"
# Firmware builds the emulator can run. "car006" is HU 006.027.001 (
# HMI ID5_1811, PSdZData 4.15.12, bimmulator branch car-006027); "x20511i" is bimmulator's stock
# 007.030.001 build (branch wsl-linux). Offsets: bimmulator archive-idrive-rootfs.py; the 006
# values were ported by ELF symbol (code) and the identical defaults table (data, -0x17E0).
FIRMWARES = {
    "car006": dict(
        root=CACHE / "firmware/car-006_027_001-v1/firmware/rootfs",
        coding_sha256="290a87736622e64593e61da98722b6d8eb8ebb3b5b26c69eab03123f3a51a417",
        defaults_table=0xD9D68,
        code_patches=(
            (0x648A0, bytes.fromhex("16 00 00 0a"), bytes.fromhex("00 00 a0 e1")),
            (0x683D4, bytes.fromhex("f0 45 2d e9 e0 40 9f e5"), bytes.fromhex("01 00 a0 e3 1e ff 2f e1")),
        ),
        variantregistry_sha256="f3c1b503a63225ff4a32b4d825c30e5942e370c83cb7fc6f9cf106f8558a6bdb",
        staged_vehicle="F30",
    ),
    "x20511i": dict(
        root=CACHE / "firmware/x20511i-007_030_001-v1/firmware/rootfs",
        coding_sha256="d1b52567a853d944a2a2ad0a50361c9ab82a0825889d9deed3b9af7739774a4d",
        defaults_table=0xDB548,
        code_patches=(  # force CHmiCodingService to use the built-in defaults (no QNX setpage in QEMU)
            (0x6512C, bytes.fromhex("16 00 00 0a"), bytes.fromhex("00 00 a0 e1")),
            (0x68C78, bytes.fromhex("f0 45 2d e9 e0 40 9f e5"), bytes.fromhex("01 00 a0 e3 1e ff 2f e1")),
        ),
        variantregistry_sha256="e21044c65cfeda08eda0bc42a2ee6a8ea35e3faaa31f721abe8a37a5916517a3",
        staged_vehicle="F32",
    ),
}
FW = FIRMWARES["car006"]  # replaced in main() by --firmware
FW_NAME, LANGUAGE = "car006", "tr"
# Car datagroup -> defaults key. Known keys come from bimmulator's Ghidra notes; the others were
# matched by identical size and 79-96 % byte similarity with the car's own pages.
DATAGROUP_KEYS = {0x3000: 7, 0x3001: 5, 0x3002: 1, 0x3003: 13, 0x3004: 12, 0x3005: 3, 0x3006: 9,
                  0x3007: 8, 0x3008: 16, 0x3009: 4, 0x300A: 10, 0x300B: 15, 0x300D: 17}
# (datagroup, byte, mask, value-in-place) the emulator needs regardless of the car's coding.
EMULATOR_BITS = (
    (0x3000, 0x1D, 0x1C, 0x0C, "HMI_ID_VERSION = id6_light (menu selector supported by HmiMain3D)"),
    (0x3001, 0x3D, 0x0F, 0x02, "CAMERA_SYSTEM = icam_rvc (emulator camera factory)"),
    (0x3005, 0x45, 0x07, 0x03, "CID_DISPLAY_RES = 1440x540"),
    (0x3005, 0x44, 0x01, 0x01, "CID_TOUCH"),
    (0x3006, 0x1D, 0x3C, 0x0C, "DISPLAY_SIZE_RESOLUTION = 10.25in 1440x540"),
    (0x3006, 0x1C, 0x40, 0x40, "developer menu (va_ENTWICKLER_MENUE)"),
    (0x300B, 0x05, 0x01, 0x01, "CID_HMI_TOUCH"),
)
# Only used with --language en-us: the old emulator default (English US as an extra master language).
ENGLISH_US_MASTER = (0x3007, 0x00, 0x30, 0x10, "master language = English US")

# HMI start language. The emulator has no ManMachineInterface master to tell the HMI its language,
# so bimmulator patches CHmiResourceManager (libhmidb.so, two constructors) from `mvn r0, #0`
# (= no language) to `mov r0, #<index>`. The index is the HMI language enum; its order matches the
# firmware's locale table in HmiMain3D (de_DE, en_GB, en_US, es_ES, it_IT, fr_FR, nl_BE, nl_NL,
# cmn_CN, ko_KR, ja_JP, ru_RU, fr_CA, pt_PT, pl_PL, el_GR, tr_TR, ...): en-US = 2 (bimmulator's
# value), Turkish = 16. text.db carries all 35 language blocks, so no download is needed.
LANGUAGE_INDEX = {"de": 0, "en-gb": 1, "en-us": 2, "es": 3, "it": 4, "fr": 5, "ru": 11, "tr": 16}
RESOURCE_PATH = "opt/hmi/ID5/lib/libhmidb.so"
RESOURCE_LANGUAGE_SITES = {"car006": (0x83F0C, 0x84258), "x20511i": (0x83F0C, 0x84258)}


def resource_library(language: str, report: list[str]) -> bytes:
    data = bytearray((FW["root"] / RESOURCE_PATH).read_bytes())
    index = LANGUAGE_INDEX[language]
    for site in RESOURCE_LANGUAGE_SITES[FW_NAME]:
        insn = bytes(data[site:site + 4])
        # original `mvn r0, #0` or an already patched `mov r0, #n`
        if insn != bytes.fromhex("00 00 e0 e3") and insn[1:] != bytes.fromhex("00 a0 e3"):
            raise SystemExit(f"libhmidb.so: unexpected instruction {insn.hex()} at 0x{site:x}")
        data[site:site + 4] = bytes([index, 0x00, 0xA0, 0xE3])
    report.append(f"  HMI start language = {language} (resource-manager index {index})")
    return bytes(data)

VARIANTREGISTRY_PATH = "opt/hmi/ID5/data/ro/common/widget/variantregistry.pbvar"


def read_ncd(path: Path) -> dict[int, bytearray]:
    pages: dict[int, bytearray] = {}
    for line in path.read_text(encoding="ascii", errors="replace").splitlines():
        line = line.strip()
        if not line.startswith("S3"):
            continue
        count = int(line[2:4], 16)
        address = int(line[4:12], 16)
        data = bytes.fromhex(line[12:12 + (count - 5) * 2])
        page = pages.setdefault(address >> 8, bytearray())
        offset = address & 0xFF
        if len(page) < offset + len(data):
            page.extend(b"\x00" * (offset + len(data) - len(page)))
        page[offset:offset + len(data)] = data
    return pages


def car_coding_library(ncd: Path, report: list[str]) -> bytes:
    data = bytearray((FW["root"] / CODING_PATH).read_bytes())
    if hashlib.sha256(data).hexdigest() != FW["coding_sha256"]:
        raise SystemExit("libhmicoding.so is not the expected build for --firmware")
    for offset, expected, replacement in FW["code_patches"]:
        if data[offset:offset + len(expected)] != expected:
            raise SystemExit(f"unexpected code at 0x{offset:x}")
        data[offset:offset + len(expected)] = replacement

    pages = read_ncd(ncd)
    locations: dict[int, tuple[int, int]] = {}
    for datagroup, key in DATAGROUP_KEYS.items():
        entry_key, packed, offset = struct.unpack_from("<III", data, FW["defaults_table"] + (key - 1) * 12)
        size = packed & 0xFFFF
        page = pages.get(datagroup)
        if entry_key != key or page is None or len(page) != size:
            report.append(f"  skip dg {datagroup:04X}: defaults key {key} size mismatch / missing")
            continue
        changed = sum(1 for a, b in zip(data[offset:offset + size], page) if a != b)
        data[offset:offset + size] = page
        locations[datagroup] = (offset, size)
        report.append(f"  dg {datagroup:04X} -> key {key:2d}: car page applied ({changed} bytes differ from BMW default)")

    for datagroup, byte, mask, value, why in EMULATOR_BITS + ((ENGLISH_US_MASTER,) if LANGUAGE == "en-us" else ()):
        offset, _ = locations[datagroup]
        before = data[offset + byte]
        data[offset + byte] = (before & ~mask & 0xFF) | value
        report.append(f"  emulator bit dg {datagroup:04X}[0x{byte:02X}] {before:02X}->{data[offset + byte]:02X}  {why}")
    series = locations.get(0x3004)
    if series:
        report.append(f"  car BAUREIHE byte (dg 3004[4]) = 0x{data[series[0] + 4]:02X}")
    return bytes(data)


def vehicle_files(vehicle: str, report: list[str]) -> list[tuple[str, bytes]]:
    if vehicle == FW["staged_vehicle"]:
        report.append(f"  3D vehicle {vehicle} is already staged by the emulator")
        return []
    registry = (FW["root"] / VARIANTREGISTRY_PATH).read_bytes()
    if hashlib.sha256(registry).hexdigest() != FW["variantregistry_sha256"]:
        raise SystemExit("variantregistry.pbvar is not the expected build")
    for item in ("vehicle", "camera_crane"):
        old = b"vehicles/G11/" + (b"vehicle_G11" if item == "vehicle" else b"camera_crane")
        new = f"vehicles/{vehicle}/".encode() + (f"vehicle_{vehicle}".encode() if item == "vehicle" else b"camera_crane")
        if len(old) != len(new) or registry.count(old) != 2:
            raise SystemExit(f"cannot retarget {old!r} to {new!r}")
        registry = registry.replace(old, new)
    files = [(VARIANTREGISTRY_PATH, registry)]
    # The emulator's RAM-backed root volume has only ~8 MB free after extraction. The F32 body
    # it stages is no longer referenced once the registry points at our vehicle, so its files are
    # truncated first (same paths, zero bytes) to make room for the car's own model.
    staged = FW["staged_vehicle"]
    staged_f32 = FW["root"] / GUEST_RO / f"bmw/widgetasset/vehicles/{staged}"
    if vehicle != staged:
        freed = 0
        for path in sorted(staged_f32.rglob("*")):
            if path.is_file():
                freed += path.stat().st_size
                files.append((f"{GUEST_RO}/bmw/widgetasset/vehicles/{staged}/{path.relative_to(staged_f32).as_posix()}", b""))
        report.append(f"  {staged} model files truncated to free {freed // 1024} KiB on the guest root")
    asset_root = FW["root"] / GUEST_RO / "bmw/widgetasset/vehicles" / vehicle
    for path in sorted(asset_root.rglob("*")):
        if path.is_file():
            files.append((f"{GUEST_RO}/bmw/widgetasset/vehicles/{vehicle}/{path.relative_to(asset_root).as_posix()}",
                          path.read_bytes()))
    report.append(f"  3D vehicle -> {vehicle}")
    return files




def plugin_files(plugin_dirs: list[Path], report: list[str]) -> list[tuple[str, bytes]]:
    files = []
    roots = [p for d in plugin_dirs if d.is_dir() for p in d.iterdir() if p.is_dir()]
    for plugin in sorted(roots):
        for path in sorted(plugin.rglob("*")):
            if path.is_file():
                data = path.read_bytes()
                if path.suffix in (".xml", ".manifest"):
                    data = data.replace(b"\r\n", b"\n")
                files.append((f"{GUEST_RO}/Plugins/{plugin.name}/{path.relative_to(plugin).as_posix()}", data))
        report.append(f"  plugin {plugin.name}")
    return files


def write_tar(files: list[tuple[str, bytes]], target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    with tarfile.open(target, "w", format=tarfile.USTAR_FORMAT) as archive:
        for name, data in files:
            info = tarfile.TarInfo(name)
            info.size, info.mtime, info.uid, info.gid = len(data), now, 0, 0
            info.mode = 0o755 if name.endswith((".so", "-worker")) else 0o644
            archive.addfile(info, io.BytesIO(data))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--car-coding", type=Path, help="IDriveReader headunit/hu_coding_backup.ncd")
    parser.add_argument("--vehicle", help="body style for the 3D vehicle, e.g. F30")
    parser.add_argument("--plugins", type=Path, action="append", default=[],
                        help="folder whose sub-folders are RA plugins (repeatable)")
    parser.add_argument("--firmware", choices=sorted(FIRMWARES), default="car006",
                        help="emulated head-unit build (default: car006 = HU 006.027.001)")
    parser.add_argument("--language", choices=sorted(LANGUAGE_INDEX), default="en-us",
                        help="HMI text language (default: en-us)")
    parser.add_argument("-o", "--output", type=Path,
                        default=Path(os.environ.get("IDRIVE_HOME", Path.home() / "idrive")) / "overlay" / "overlay.tar")
    args = parser.parse_args()
    global FW, FW_NAME, LANGUAGE
    FW, FW_NAME, LANGUAGE = FIRMWARES[args.firmware], args.firmware, args.language

    report: list[str] = []
    files: list[tuple[str, bytes]] = []
    # Order matters: bsdtar applies entries sequentially, so space-freeing truncations (inside
    # vehicle_files) come before anything that grows the guest root.
    if args.vehicle:
        files += vehicle_files(args.vehicle, report)
    if args.car_coding:
        files.append((CODING_PATH, car_coding_library(args.car_coding, report)))
    files.append((RESOURCE_PATH, resource_library(args.language, report)))
    files += plugin_files(args.plugins, report)
    write_tar(files, args.output)
    print("\n".join(report))
    print(f"-> {args.output} ({len(files)} files, {args.output.stat().st_size // 1024} KiB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
