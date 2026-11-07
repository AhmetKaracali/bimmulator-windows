#!/usr/bin/env python3
"""Inspect the recovered PowerVR SGX shader containers used by NBTevo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


MAGIC = bytes.fromhex("38b4fa10")
HEADER_SIZE = 32
STAGE_INFO_SIZE = 36
PAYLOAD_LENGTH_OFFSET = HEADER_SIZE + STAGE_INFO_SIZE
PAYLOAD_OFFSET = PAYLOAD_LENGTH_OFFSET + 4
SYMBOL_METADATA_SIZE = 18
STAGE_NAMES = {0: "vertex", 1: "fragment"}


class ShaderFormatError(ValueError):
    pass


def read_be(data: bytes, offset: int, width: int, label: str) -> int:
    end = offset + width
    if offset < 0 or end > len(data):
        raise ShaderFormatError(f"truncated {label} at offset {offset}")
    return int.from_bytes(data[offset:end], "big")


def read_le(data: bytes, offset: int, width: int, label: str) -> int:
    end = offset + width
    if offset < 0 or end > len(data):
        raise ShaderFormatError(f"truncated {label} at offset {offset}")
    return int.from_bytes(data[offset:end], "little")


def parse_suffix(data: bytes, offset: int) -> dict[str, Any] | None:
    """Parse the constant and symbol tables, requiring an exact file end."""
    if offset + 2 > len(data) or data[offset] != 0:
        return None

    constant_count = data[offset + 1]
    constants_start = offset + 2
    symbols_count_offset = constants_start + constant_count * 4
    if symbols_count_offset + 2 > len(data):
        return None

    symbol_count = read_be(data, symbols_count_offset, 2, "symbol count")
    cursor = symbols_count_offset + 2
    symbols = []
    for _ in range(symbol_count):
        nul = data.find(b"\0", cursor)
        if nul < cursor or nul + 1 + SYMBOL_METADATA_SIZE > len(data):
            return None
        try:
            name = data[cursor:nul].decode("ascii")
        except UnicodeDecodeError:
            return None
        if not name:
            return None
        metadata_start = nul + 1
        symbols.append(
            {
                "name": name,
                "offset": cursor,
                "metadata_hex": data[
                    metadata_start : metadata_start + SYMBOL_METADATA_SIZE
                ].hex(),
            }
        )
        cursor = metadata_start + SYMBOL_METADATA_SIZE

    if cursor != len(data):
        return None

    return {
        "constant_count": constant_count,
        "constant_data_offset": constants_start,
        "constant_data_hex": data[constants_start:symbols_count_offset].hex(),
        "symbol_count_offset": symbols_count_offset,
        "symbols": symbols,
    }


def parse_shader(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if len(data) < PAYLOAD_OFFSET:
        raise ShaderFormatError("file is shorter than the fixed header")
    if data[:4] != MAGIC:
        raise ShaderFormatError(f"unexpected magic {data[:4].hex()}")

    declared_body_length = read_be(data, 28, 4, "body length")
    if declared_body_length != len(data) - HEADER_SIZE:
        raise ShaderFormatError(
            f"body length says {declared_body_length}, actual {len(data) - HEADER_SIZE}"
        )

    stage_id = read_be(data, HEADER_SIZE, 4, "shader stage")

    first_length = read_be(data, PAYLOAD_LENGTH_OFFSET, 4, "first payload length")
    first_end = PAYLOAD_OFFSET + first_length
    if first_end > len(data):
        raise ShaderFormatError("first payload extends past end of file")

    payloads = [{"offset": PAYLOAD_OFFSET, "length": first_length}]
    suffix = parse_suffix(data, first_end)
    if suffix is None:
        second_length = read_be(data, first_end, 4, "second payload length")
        second_offset = first_end + 4
        second_end = second_offset + second_length
        if second_end > len(data):
            raise ShaderFormatError("second payload extends past end of file")
        suffix = parse_suffix(data, second_end)
        if suffix is None:
            raise ShaderFormatError("could not parse constant/symbol table suffix")
        payloads.append({"offset": second_offset, "length": second_length})

    markers = []
    for payload in payloads:
        start = payload["offset"]
        end = start + payload["length"]
        if end - start < 12 or data[start + 1 : start + 4] != b"PSU":
            raise ShaderFormatError(f"missing PSU record in payload at offset {start}")
        psu_body_length = read_le(data, start + 8, 4, "PSU body length")
        if psu_body_length != payload["length"] - 12:
            raise ShaderFormatError(f"PSU body length mismatch at offset {start}")
        payload["psu_marker_offset"] = start + 1
        payload["psu_format_word"] = read_le(data, start + 4, 4, "PSU format word")
        payload["psu_body_length"] = psu_body_length
        cursor = start
        while True:
            marker = data.find(b"PSU", cursor, end)
            if marker < 0:
                break
            markers.append(marker)
            cursor = marker + 1

    return {
        "path": str(path),
        "size": len(data),
        "hash": data[4:8].hex(),
        "stage_id": stage_id,
        "stage": STAGE_NAMES.get(stage_id, f"unknown-{stage_id}"),
        "stage_info_hex": data[32:68].hex(),
        "payloads": payloads,
        "constant_count": suffix["constant_count"],
        "constant_data_offset": suffix["constant_data_offset"],
        "constant_data_hex": suffix["constant_data_hex"],
        "symbols": suffix["symbols"],
        "psu_marker_offsets": markers,
    }


def collect_files(paths: list[Path]) -> list[Path]:
    files = []
    for path in paths:
        if path.is_dir():
            files.extend(sorted(path.rglob("*.shd")))
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="shader files or directories")
    parser.add_argument("--json", action="store_true", help="emit parsed records as JSON")
    parser.add_argument("--verbose", action="store_true", help="list every parsed file")
    args = parser.parse_args()

    try:
        files = collect_files(args.paths)
        records = [parse_shader(path) for path in files]
    except (OSError, ShaderFormatError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(records, indent=2))
        return 0

    payload_counts: dict[int, int] = {}
    stage_counts: dict[str, int] = {}
    for record in records:
        count = len(record["payloads"])
        payload_counts[count] = payload_counts.get(count, 0) + 1
        stage = record["stage"]
        stage_counts[stage] = stage_counts.get(stage, 0) + 1

    print(f"Parsed {len(records)} shader file(s)")
    print(", ".join(f"{count} payload(s): {n}" for count, n in sorted(payload_counts.items())))
    print(", ".join(f"{stage} stage: {n}" for stage, n in sorted(stage_counts.items())))
    if args.verbose:
        for record in records:
            print(
                f"{record['path']}: payloads="
                f"{','.join(str(p['length']) for p in record['payloads'])}; "
                f"stage={record['stage']}; "
                f"constants={record['constant_count']}; "
                f"symbols={len(record['symbols'])}; "
                f"PSU={','.join(str(pos) for pos in record['psu_marker_offsets'])}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
