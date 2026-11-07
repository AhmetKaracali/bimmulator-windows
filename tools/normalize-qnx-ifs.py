#!/usr/bin/env python3
"""Expand the LZO-compressed image filesystem in a QNX IFS."""

from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import os
from pathlib import Path
import struct
import sys


STARTUP_SIGNATURE = b"\xeb\x7e\xff\x00"
COMPRESSION_MASK = 0x1C
COMPRESSION_LZO = 0x08
MAX_BLOCK_OUTPUT = 1 << 20


def load_lzo() -> ctypes.CDLL:
    candidates = [os.environ.get("IDRIVE_LZO_LIBRARY"), ctypes.util.find_library("lzo2")]
    candidates.extend(("liblzo2.dylib", "liblzo2.so.2", "liblzo2.so"))
    for candidate in candidates:
        if not candidate:
            continue
        try:
            return ctypes.CDLL(candidate)
        except OSError:
            pass
    raise RuntimeError("liblzo2 not found; set IDRIVE_LZO_LIBRARY or install the LZO runtime library")


def decompress_lzo_block(lzo: ctypes.CDLL, payload: bytes) -> bytes:
    source = ctypes.create_string_buffer(payload, len(payload))
    output = ctypes.create_string_buffer(MAX_BLOCK_OUTPUT)
    output_size = ctypes.c_size_t(MAX_BLOCK_OUTPUT)
    decompress = lzo.lzo1x_decompress_safe
    decompress.argtypes = (
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.c_void_p,
    )
    decompress.restype = ctypes.c_int
    status = decompress(source, len(payload), output, ctypes.byref(output_size), None)
    if status != 0:
        raise RuntimeError(f"LZO block decompression failed with status {status}")
    return output.raw[: output_size.value]


def normalize(source_path: Path, destination_path: Path) -> None:
    image = source_path.read_bytes()
    header_offset = image.find(STARTUP_SIGNATURE)
    if header_offset < 0 or header_offset + 0x40 > len(image):
        raise RuntimeError("QNX startup header signature was not found")

    flags_offset = header_offset + 6
    flags = image[flags_offset]
    compression = flags & COMPRESSION_MASK
    if compression != COMPRESSION_LZO:
        raise RuntimeError(f"expected LZO compression (0x08), found 0x{compression:02x}")

    startup_size = struct.unpack_from("<I", image, header_offset + 0x20)[0]
    stored_size = struct.unpack_from("<I", image, header_offset + 0x24)[0]
    imagefs_size = struct.unpack_from("<I", image, header_offset + 0x2C)[0]
    payload_start = header_offset + startup_size
    stored_end = header_offset + stored_size
    if payload_start > stored_end or stored_end > len(image):
        raise RuntimeError("startup header sizes fall outside the input image")

    lzo = load_lzo()
    position = payload_start
    expanded = bytearray()
    block_count = 0
    while True:
        if position + 2 > stored_end:
            raise RuntimeError("LZO block list ended before its zero-length terminator")
        block_size = int.from_bytes(image[position : position + 2], "big")
        position += 2
        if block_size == 0:
            break
        block_end = position + block_size
        if block_end > stored_end:
            raise RuntimeError("LZO block extends beyond the startup header's stored size")
        expanded.extend(decompress_lzo_block(lzo, image[position:block_end]))
        position = block_end
        block_count += 1

    if len(expanded) != imagefs_size:
        raise RuntimeError(
            f"expanded imagefs has {len(expanded):#x} bytes; header declares {imagefs_size:#x}"
        )

    # The four-byte image checksum follows stored_size. Keep it for this first
    # normalization pass; QNX startup checks the separate startup trailer.
    tail = image[stored_end:]
    normalized = bytearray(image[:payload_start])
    normalized.extend(expanded)
    normalized.extend(tail)
    normalized[flags_offset] = flags & ~COMPRESSION_MASK
    normalized_stored_size = startup_size + imagefs_size
    struct.pack_into("<I", normalized, header_offset + 0x1C, normalized_stored_size)
    struct.pack_into("<I", normalized, header_offset + 0x24, normalized_stored_size)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.write_bytes(normalized)
    print(
        f"Expanded {block_count} LZO blocks: {len(image):#x} -> {len(normalized):#x} bytes; "
        f"flags1 {flags:#04x} -> {normalized[flags_offset]:#04x}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="compressed QNX IFS image")
    parser.add_argument("output", type=Path, help="uncompressed output image")
    arguments = parser.parse_args()
    try:
        normalize(arguments.input, arguments.output)
    except (OSError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
