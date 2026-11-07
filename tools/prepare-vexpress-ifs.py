#!/usr/bin/env python3
"""Prepare a temporary QNX IFS copy for the selected emulator board."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import struct
import subprocess
import sys


def movw(rd: int, immediate: int) -> int:
    return 0xE3000000 | ((immediate & 0xF000) << 4) | (rd << 12) | (immediate & 0x0FFF)


def movt(rd: int, immediate: int) -> int:
    return 0xE3400000 | ((immediate & 0xF000) << 4) | (rd << 12) | (immediate & 0x0FFF)


def find_ifs_file(image: bytearray, imagefs_start: int, imagefs_size: int, target: str) -> tuple[int, int]:
    imagefs = image[imagefs_start : imagefs_start + imagefs_size]
    directory_offset = struct.unpack_from("<I", imagefs, 16)[0]
    position = directory_offset
    while position + 24 <= len(imagefs):
        record_size, _extattr, _inode, mode, _gid, _uid, _mtime = struct.unpack_from(
            "<HHLLLLL", imagefs, position
        )
        if record_size == 0:
            break
        end = position + record_size
        if record_size < 24 or end > len(imagefs):
            raise RuntimeError(f"invalid IFS directory record at {position:#x}")
        if mode & 0xF000 == 0x8000:
            data_offset, data_size = struct.unpack_from("<II", imagefs, position + 24)
            name_start = position + 32
            name_end = imagefs.find(b"\0", name_start, end)
            if name_end < 0:
                raise RuntimeError(f"unterminated IFS filename at {position:#x}")
            name = imagefs[name_start:name_end].decode("utf-8")
            if name == target:
                return imagefs_start + data_offset, data_size
        position = end
    raise RuntimeError(f"IFS file was not found: {target}")


def prepare(source: Path, output: Path, secondary_stub: Path, profile: str) -> None:
    if profile not in {"vexpress", "omap5"}:
        raise RuntimeError(f"unsupported IFS profile: {profile}")

    normalizer = Path(__file__).with_name("normalize-qnx-ifs.py")
    subprocess.run([sys.executable, str(normalizer), str(source), str(output)], check=True)
    image = bytearray(output.read_bytes())

    # The repository's historical .patched image inverted these counted loops
    # in startup's callout patchers. They are not hardware polling loops: they
    # copy/patch all four address bytes into the generated kernel callouts.
    # Leaving them inverted produces partially patched pointers (for example
    # 0xffffff00 instead of the mapped SDMA address). Accept the original image
    # as well, and repair only the exact known historical branch inversions.
    callout_loops = {
        0x068C: 0x1AFFFFF7,
        0x06CC: 0x1AFFFFFB,
        0x0938: 0x1AFFFFF7,
        0x0978: 0x1AFFFFFB,
        0x0DB4: 0x1AFFFFF7,
        0x0DF0: 0x1AFFFFF7,
        0x0E48: 0x1AFFFFF7,
        0x0F9C: 0x1AFFFFF7,
        0x10F0: 0x1AFFFFF7,
        0x1248: 0x1AFFFFF7,
    }
    repaired = 0
    for offset, original in callout_loops.items():
        actual = struct.unpack_from("<I", image, offset)[0]
        inverted = original & 0x0FFFFFFF
        if actual == inverted:
            struct.pack_into("<I", image, offset, original)
            repaired += 1
        elif actual != original:
            raise RuntimeError(
                f"unexpected callout patcher branch at {offset:#x}: {actual:#010x}"
            )
    if repaired:
        print(f"Restored {repaired} startup callout address/copy loops")

    # These edits replace only the temporary, decompressed copy. OMAP5's
    # startup code otherwise waits on unavailable clock, UART, and PHY blocks.
    patches = {
        0x0584: (0xE3443828, movt(3, 0xBFFE)),  # secondary-core mailbox base
        0x1EF8: (0x1AFFFFFC, 0xE1A00000),  # skip DPLL status polling
        0x1880: (0xE3443AE0, movt(3, 0xBFFE)),  # CM_SYS_CLKSEL/clock module
        0x18A8: (0xE3443AE0, movt(3, 0xBFFE)),
        0x18C8: (0xE3443A00, movt(3, 0xBFFE)),
        0x1998: (0xE3442A00, movt(2, 0xBFFE)),
        0x19D4: (0xE3442A00, movt(2, 0xBFFE)),
        0x1A38: (0xE3443A00, movt(3, 0xBFFE)),
        0x1AFC: (0xE3443A00, movt(3, 0xBFFE)),
        0x375C: (0xE3443A09, movt(3, 0xBFFE)),  # OCP2SCP3 status block
        0x37E8: (0xE3063000, movw(3, 0x8000)),  # SATA PHY synthetic block
        0x37F0: (0xE3443A09, movt(3, 0xBFFE)),
        0x3854: (0xE3064000, movw(4, 0x8000)),
        0x3858: (0xE3444A09, movt(4, 0xBFFE)),
        0x3890: (0xE3064000, movw(4, 0x8000)),
        0x3894: (0xE3444A09, movt(4, 0xBFFE)),
        0x486C: (0xE1600070, 0xE1A00000),  # QEMU cannot execute OMAP SMC
    }
    if profile == "vexpress":
        patches.update(
            {
                0x4D14: (0xE3A04000, 0xE1A00000),  # keep vexpress GIC mapping
                0x4D18: (0xE5804000, 0xE3A04000),  # avoid clearing the GIC
                0x7220: (0x0AFFFFFB, 0xE1A00000),  # PL011 has a different LSR
            }
        )

    for offset, (expected, replacement) in patches.items():
        actual = int.from_bytes(image[offset : offset + 4], "little")
        if actual != expected:
            raise RuntimeError(
                f"unexpected ARM word at image offset {offset:#x}: "
                f"expected {expected:#010x}, found {actual:#010x}"
            )
        image[offset : offset + 4] = replacement.to_bytes(4, "little")

    # Route startup's byte output callback to vexpress's first PL011. The
    # OMAP5 machine keeps the guest's native UART code and address.
    uart_original = [
        0xE59F3020,
        0xE8931004,
        0xE35C0000,
        0xE1A02210,
        0x06EF1071,
        0x15933008,
        0x05933008,
        0x17C31002,
    ]
    uart_writer = [
        movw(3, 0),
        movt(3, 0x1C09),
        movw(2, 0x70),
        0xE583202C,
        movw(2, 0x101),
        0xE5832030,
        0xE5C31000,
        0xE12FFF1E,
    ]
    if profile == "vexpress":
        for index, (expected, replacement) in enumerate(zip(uart_original, uart_writer)):
            offset = 0xF05C + index * 4
            actual = int.from_bytes(image[offset : offset + 4], "little")
            if actual != expected:
                raise RuntimeError(
                    f"unexpected UART writer word at image offset {offset:#x}: "
                    f"expected {expected:#010x}, found {actual:#010x}"
                )
            image[offset : offset + 4] = replacement.to_bytes(4, "little")

    # Keep the BMW boot console on UART3 for OMAP5; remap it for vexpress.
    header_offset = image.find(b"\xeb\x7e\xff\x00")
    if header_offset < 0:
        raise RuntimeError("QNX startup header signature was not found after normalization")
    startup_size = struct.unpack_from("<I", image, header_offset + 0x20)[0]
    imagefs_size = struct.unpack_from("<I", image, header_offset + 0x2C)[0]
    imagefs_start = header_offset + startup_size
    serial_map = b"0x48020000^2,106"
    serial_map_offset = image.find(serial_map, imagefs_start)
    if serial_map_offset < 0:
        raise RuntimeError("expected OMAP serial port setting was not found in the boot script")
    if profile == "vexpress":
        # QEMU's vexpress-a15 UART0 is wired to GIC interrupt 37 (SPI 5).
        image[serial_map_offset : serial_map_offset + len(serial_map)] = b"0x1c090000^2,037"
    if os.environ.get("IDRIVE_SERIAL_DIAGNOSTICS") == "1":
        unit_option = b"-u1\0"
        unit_offset = image.find(unit_option, imagefs_start)
        if unit_offset < 0 or image.find(unit_option, unit_offset + 1) >= 0:
            raise RuntimeError("expected one serial unit option in the boot script")
        # The generic devc-ser* default is unit 1; replace the explicit -u1
        # with two verbose flags without changing the boot-script record size.
        image[unit_offset : unit_offset + len(unit_option)] = b"-vv\0"

    if profile == "vexpress":
        serial_driver_offset, serial_driver_size = find_ifs_file(
            image, imagefs_start, imagefs_size, "boot/bin/devc-seromap"
        )
        if serial_driver_size <= 0x2194:
            raise RuntimeError("devc-seromap is shorter than the expected OMAP UART checks")
        for offset, expected, replacement in (
            (0x218C, 0xE5D23000, 0xE5D23004),  # PL011 flags register at +0x18 vs OMAP LSR at +0x14
            (0x2190, 0xE3130020, 0xE3130080),  # PL011 TXFF bit vs OMAP THRE bit
        ):
            absolute = serial_driver_offset + offset
            actual = int.from_bytes(image[absolute : absolute + 4], "little")
            if actual != expected:
                raise RuntimeError(
                    f"unexpected devc-seromap ARM word at file offset {offset:#x}: "
                    f"expected {expected:#010x}, found {actual:#010x}"
                )
            image[absolute : absolute + 4] = replacement.to_bytes(4, "little")

    output.write_bytes(image)
    output.chmod(0o600)
    secondary_stub.write_bytes(
        bytes.fromhex("0c309fe5002093e5000052e3fbffff0a12ff2fe10418febf")
    )
    secondary_stub.chmod(0o600)
    print(
        f"Prepared {profile} probe image ({len(image):#x} bytes) at {output}; "
        f"secondary wait stub at {secondary_stub}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="compressed QNX IFS source")
    parser.add_argument("output", type=Path, help="temporary prepared IFS output")
    parser.add_argument("secondary_stub", type=Path, help="CPU1 mailbox wait stub output")
    parser.add_argument(
        "--profile", choices=("vexpress", "omap5"), default="vexpress"
    )
    arguments = parser.parse_args()
    try:
        prepare(
            arguments.input,
            arguments.output,
            arguments.secondary_stub,
            arguments.profile,
        )
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
