#!/usr/bin/env python3
"""Extract a compact PDS/USE memory fixture from an opt-in QEMU SGX trace."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path


EVENT_RE = re.compile(
    r"omap5430-sgx: firmware event (?P<event>\d+) "
    r"pd=(?P<pd>\S+) pds=(?P<pds>\S+) "
    r"info=(?P<info>\S+) data=(?P<data>\S+)"
)
ACCESS_RE = re.compile(
    r"omap5430-sgx: write offset=(?P<offset>0x[0-9a-fA-F]+) "
    r"value=(?P<value>(?:0x)?[0-9a-fA-F]+)"
)
MEMORY_RE = re.compile(
    r"omap5430-sgx: (?P<space>PDS-PAGE|PDS|USE-CODE|USE-BRANCH-TARGET|KCCB|KCCB-CTL|"
    r"host-ctl|miscinfo) "
    r"va=(?P<va>0x[0-9a-fA-F]+) pa=(?P<pa>0x[0-9a-fA-F]+) "
    r"word=(?P<word>(?:0x)?[0-9a-fA-F]+)"
)
UNMAPPED_RE = re.compile(
    r"omap5430-sgx: (?P<space>\S+) unmapped va=(?P<va>0x[0-9a-fA-F]+) "
    r"index=(?P<index>\d+)"
)
MAP_RE = re.compile(
    r"omap5430-sgx: capture-map name=(?P<name>\S+) "
    r"va=(?P<va>0x[0-9a-fA-F]+) pd=(?P<pd>0x[0-9a-fA-F]+) "
    r"pde-pa=(?P<pde_pa>0x[0-9a-fA-F]+) pde=(?P<pde>0x[0-9a-fA-F]+) "
    r"pte-pa=(?P<pte_pa>0x[0-9a-fA-F]+) pte=(?P<pte>0x[0-9a-fA-F]+) "
    r"page-shift=(?P<page_shift>\d+) pa=(?P<pa>0x[0-9a-fA-F]+)"
)
USE_BASE_RE = re.compile(
    r"omap5430-sgx: USE-CODE-BASE slot=(?P<slot>\d+) "
    r"value=(?P<value>0x[0-9a-fA-F]+) "
    r"address-field=(?P<address_field>0x[0-9a-fA-F]+) "
    r"dm=(?P<dm>\d+) va=(?P<va>0x[0-9a-fA-F]+)"
)

PDS_PAGE_SIZE = 0x1000
USE_CAPTURE_MAX_SIZE = 0x20000
CONTEXT_REGION_SIZES = {
    "KCCB": 0x2000,
    "KCCB-CTL": 8,
    "host-ctl": 0xEC,
    "miscinfo": 0x60,
}
USE_CODE_BASE_FIRST = 0x0A0C
USE_CODE_BASE_LAST = 0x0A48
USE_CODE_BASE_ADDRESS_MASK = 0x03FFFFFF
USE_CODE_BASE_DATA_MASTER_MASK = 0x0C000000
PDS_DOUTU_ONLY = 0x07000185
PDS_END = 0xAF000000
DOUTU_FLAG_MASK = 0x09000000


def parse_hex(value: str) -> int:
    return int(value.removeprefix("0x"), 16)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collect(trace: Path) -> dict:
    events = []
    accesses = []
    maps = []
    bases = []
    unmapped = []
    memory = {
        name: {}
        for name in (
            "PDS-PAGE", "PDS", "USE-CODE", "USE-BRANCH-TARGET", "KCCB",
            "KCCB-CTL", "host-ctl", "miscinfo",
        )
    }

    for line_number, line in enumerate(trace.read_text(errors="replace").splitlines(), 1):
        if match := EVENT_RE.search(line):
            events.append(
                {
                    "line": line_number,
                    "event": int(match["event"]),
                    "pd": parse_hex(match["pd"]),
                    "pds": parse_hex(match["pds"]),
                    "info": parse_hex(match["info"]),
                    "data": parse_hex(match["data"]),
                }
            )
        if match := ACCESS_RE.search(line):
            accesses.append(
                {
                    "line": line_number,
                    "offset": parse_hex(match["offset"]),
                    "value": parse_hex(match["value"]),
                }
            )
        if match := MAP_RE.search(line):
            maps.append(
                {
                    "line": line_number,
                    "name": match["name"],
                    "va": parse_hex(match["va"]),
                    "pd": parse_hex(match["pd"]),
                    "pde_pa": parse_hex(match["pde_pa"]),
                    "pde": parse_hex(match["pde"]),
                    "pte_pa": parse_hex(match["pte_pa"]),
                    "pte": parse_hex(match["pte"]),
                    "page_shift": int(match["page_shift"]),
                    "pa": parse_hex(match["pa"]),
                }
            )
        if match := USE_BASE_RE.search(line):
            bases.append(
                {
                    "line": line_number,
                    "slot": int(match["slot"]),
                    "value": parse_hex(match["value"]),
                    "address_field": parse_hex(match["address_field"]),
                    "data_master": int(match["dm"]),
                    "va": parse_hex(match["va"]),
                }
            )
        if match := MEMORY_RE.search(line):
            memory[match["space"]][parse_hex(match["va"])] = (
                parse_hex(match["pa"]),
                parse_hex(match["word"]),
            )
        if match := UNMAPPED_RE.search(line):
            unmapped.append(
                {
                    "space": match["space"],
                    "va": parse_hex(match["va"]),
                    "index": int(match["index"]),
                }
            )

    return {
        "source_log": str(trace.resolve()),
        "source_log_sha256": sha256(trace.read_bytes()),
        "events": events,
        "register_writes": accesses,
        "maps": maps,
        "use_code_bases": bases,
        "unmapped_accesses": unmapped,
        "memory": memory,
    }


def reconstruct(
    records: dict[int, tuple[int, int]],
    label: str,
    size: int | None = None,
    allow_short: bool = False,
):
    if not records:
        raise ValueError(f"trace contains no {label} memory records")
    base = min(records)
    end = max(records) + 4
    actual_size = end - base
    if (
        size is not None
        and actual_size != size
        and not (allow_short and actual_size < size)
    ):
        raise ValueError(
            f"{label} capture has {actual_size:#x} bytes; expected {size:#x}"
        )
    expected_addresses = set(range(base, end, 4))
    missing = sorted(expected_addresses - records.keys())
    if missing:
        raise ValueError(
            f"{label} capture is missing {len(missing)} words; "
            f"first {missing[0]:#x}"
        )
    data = bytearray()
    physical_addresses = []
    for va in range(base, end, 4):
        pa, word = records[va]
        physical_addresses.append(pa)
        data.extend(struct.pack("<I", word))
    physical_contiguous = all(
        physical_addresses[i] == physical_addresses[0] + i * 4
        for i in range(len(physical_addresses))
    )
    return {
        "gpu_va": base,
        "physical_start": physical_addresses[0],
        "physical_contiguous": physical_contiguous,
        "size": len(data),
        "sha256": sha256(data),
        "data": bytes(data),
    }


def source_comparison(captured: bytes, firmware_path: Path | None) -> dict | None:
    if firmware_path is None:
        return None
    reference = firmware_path.read_bytes()
    common = min(len(captured), len(reference))
    changed_bytes = [
        index for index in range(common) if captured[index] != reference[index]
    ]
    changed_runs = []
    for offset in changed_bytes:
        if not changed_runs or offset > changed_runs[-1][1] + 1:
            changed_runs.append([offset, offset])
        else:
            changed_runs[-1][1] = offset
    return {
        "reference_path": str(firmware_path.resolve()),
        "reference_size": len(reference),
        "reference_sha256": sha256(reference),
        "captured_size": len(captured),
        "captured_sha256": sha256(captured),
        "identical": captured == reference,
        "compared_bytes": common,
        "changed_bytes": len(changed_bytes),
        "different_length": len(captured) != len(reference),
        "first_changed_offset": changed_bytes[0] if changed_bytes else None,
        "changed_byte_runs": [
            {"start": start, "end": end, "size": end - start + 1}
            for start, end in changed_runs
        ],
    }


def derive_entry(capture: dict, pds: dict, use: dict) -> dict:
    event = capture["events"][0]
    pds_offset = event["pds"] - pds["gpu_va"]
    if pds_offset < 0 or pds_offset + 24 > pds["size"]:
        raise ValueError("first event PDS pointer lies outside the captured PDS page")
    words = struct.unpack_from("<6I", pds["data"], pds_offset)
    result = {
        "status": "unresolved",
        "event_pds_gpu_va": event["pds"],
        "pds_offset": pds_offset,
        "pds_words": [f"0x{word:08x}" for word in words],
        "reason": "event PDS program is not the supported one-row DOUTU-only form",
    }
    if words[4:6] != (PDS_DOUTU_ONLY, PDS_END):
        return result

    doutu_word = words[0]
    address_word = doutu_word & ~DOUTU_FLAG_MASK
    code_base_index = address_word & 0xF
    instruction_index = address_word >> 4
    byte_offset = instruction_index * 8
    base = next(
        (item for item in capture["use_code_bases"] if item["slot"] == code_base_index),
        None,
    )
    if base is None:
        result["reason"] = f"DOUTU selects absent USE code-base slot {code_base_index}"
        return result

    gpu_pc = base["va"] + byte_offset
    pc_offset = gpu_pc - use["gpu_va"]
    physical_pc = None
    entry_word = None
    if 0 <= pc_offset <= use["size"] - 8:
        entry_word = struct.unpack_from("<Q", use["data"], pc_offset)[0]
        pc_record = capture["memory"]["USE-CODE"].get(gpu_pc)
        if pc_record:
            physical_pc = pc_record[0]

    return {
        "status": "derived" if entry_word is not None and physical_pc is not None else "candidate",
        "pds_program_form": "one data row, DOUTU_ONLY, END",
        "doutu_data_row_aux_words": [f"0x{word:08x}" for word in words[1:4]],
        "pds_instruction_words": [f"0x{words[4]:08x}", f"0x{words[5]:08x}"],
        "doutu_data_word": f"0x{doutu_word:08x}",
        "doutu_flag_bits": f"0x{doutu_word & DOUTU_FLAG_MASK:08x}",
        "doutu_address_word": f"0x{address_word:08x}",
        "use_code_base_index": code_base_index,
        "use_code_base_value": f"0x{base['value']:08x}",
        "use_code_base_address_field": f"0x{base['address_field']:08x}",
        "use_data_master": base["data_master"],
        "use_code_base_gpu_va": f"0x{base['va']:08x}",
        "instruction_index": instruction_index,
        "instruction_size": 8,
        "byte_offset": byte_offset,
        "gpu_pc": f"0x{gpu_pc:08x}",
        "physical_pc": f"0x{physical_pc:08x}" if physical_pc is not None else None,
        "captured_entry_word": f"0x{entry_word:016x}" if entry_word is not None else None,
        "derivation": (
            "The SGX543 PDS DOUTU encoding treats the low nibble as the USE code-base "
            "index and the remaining address field as an 8-byte instruction index; "
            "the SGX code-base register field reconstructs a GPU VA by shifting left 6. "
            "The local capture supplies the matching SGX page-table translation and "
            "runtime bytes. SGX544 execution semantics still need validation."
        ),
    }


def context_memory_ranges(memory: dict) -> list[dict]:
    ranges = []
    for name, declared_size in CONTEXT_REGION_SIZES.items():
        records = memory[name]
        if not records:
            continue
        addresses = sorted(records)
        base = addresses[0]
        physical = [records[va][0] for va in addresses]
        ranges.append(
            {
                "name": name,
                "gpu_va_start": base,
                "gpu_va_end_exclusive": base + declared_size,
                "declared_size": declared_size,
                "captured_sample_size": addresses[-1] - base + 4,
                "sample_physical_start": physical[0],
                "sample_physical_contiguous": all(
                    physical[index] == physical[0] + index * 4
                    for index in range(len(physical))
                ),
                "sample_words": len(records),
            }
        )
    return ranges


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, help="QEMU debug log from IDRIVE_SGX_CAPTURE=1")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--firmware", type=Path, help="recovered USE firmware reference")
    args = parser.parse_args()
    if not args.trace.is_file():
        parser.error(f"trace is not a regular file: {args.trace}")
    if args.firmware is not None and not args.firmware.is_file():
        parser.error(f"firmware is not a regular file: {args.firmware}")

    try:
        capture = collect(args.trace)
        if not capture["events"]:
            raise ValueError("trace contains no SGX firmware event")
        pds = reconstruct(capture["memory"]["PDS-PAGE"], "PDS page", PDS_PAGE_SIZE)
        use = reconstruct(
            capture["memory"]["USE-CODE"],
            "USE firmware",
            USE_CAPTURE_MAX_SIZE,
            allow_short=True,
        )
        use["requested_size"] = USE_CAPTURE_MAX_SIZE
        use["complete"] = use["size"] == USE_CAPTURE_MAX_SIZE
        branch_target = None
        if capture["memory"]["USE-BRANCH-TARGET"]:
            branch_target = reconstruct(
                capture["memory"]["USE-BRANCH-TARGET"], "USE branch target"
            )
        entry = derive_entry(capture, pds, use)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "pds-page.bin").write_bytes(pds["data"])
        (args.output_dir / "use-image.bin").write_bytes(use["data"])
        if branch_target:
            (args.output_dir / "use-branch-target.bin").write_bytes(
                branch_target["data"]
            )

        reference = source_comparison(use["data"], args.firmware)
        manifest = {
            "format_version": 1,
            "source_log": capture["source_log"],
            "source_log_sha256": capture["source_log_sha256"],
            "event": capture["events"][0],
            "sgx_register_writes": capture["register_writes"],
            "page_table_mappings": capture["maps"],
            "unmapped_accesses": capture["unmapped_accesses"],
            "use_code_bases": capture["use_code_bases"],
            "context_memory_ranges": context_memory_ranges(capture["memory"]),
            "pds_page": {key: value for key, value in pds.items() if key != "data"},
            "use_image": {key: value for key, value in use.items() if key != "data"},
            "use_branch_target": (
                {
                    key: value
                    for key, value in branch_target.items()
                    if key != "data"
                }
                if branch_target
                else None
            ),
            "source_firmware_comparison": reference,
            "derived_initial_entry": entry,
        }
        (args.output_dir / "fixture.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )
    except (OSError, ValueError, struct.error) as exc:
        print(f"cannot extract SGX capture: {exc}")
        return 1

    print(f"PDS page: {args.output_dir / 'pds-page.bin'} ({pds['size']} bytes)")
    print(
        f"USE image: {args.output_dir / 'use-image.bin'} "
        f"({use['size']} of {use['requested_size']} requested bytes; "
        f"complete={use['complete']})"
    )
    if branch_target:
        print(
            f"USE branch target: {args.output_dir / 'use-branch-target.bin'} "
            f"({branch_target['size']} bytes)"
        )
    print(f"Fixture: {args.output_dir / 'fixture.json'}")
    print(f"PDS/USE candidate entry: {entry.get('gpu_pc', 'unresolved')} ({entry['status']})")
    if reference:
        print(
            "Firmware reference: "
            f"{reference['changed_bytes']} differing bytes, "
            f"first at {reference['first_changed_offset']:#x}"
            if reference["first_changed_offset"] is not None
            else "Firmware reference: byte-for-byte match"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
