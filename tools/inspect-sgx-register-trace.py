#!/usr/bin/env python3
"""Summarize SGX MMIO writes and firmware events from a QEMU debug log."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ACCESS_RE = re.compile(
    r"omap5430-sgx: (?P<operation>read|write) "
    r"offset=(?P<offset>0x[0-9a-fA-F]+) "
    r"value=(?P<value>(?:0x)?[0-9a-fA-F]+)"
)
EVENT_RE = re.compile(
    r"omap5430-sgx: firmware event (?P<event>\d+) "
    r"pd=(?P<pd>\S+) pds=(?P<pds>\S+) "
    r"info=(?P<info>\S+) data=(?P<data>\S+)"
)
MEMORY_RE = re.compile(
    r"omap5430-sgx: (?P<space>PDS-PAGE|PDS|USE-CODE|USE-CANDIDATE|"
    r"KCCB|KCCB-CTL|host-ctl|miscinfo) "
    r"va=(?P<va>0x[0-9a-fA-F]+) pa=(?P<pa>0x[0-9a-fA-F]+) "
    r"word=(?P<word>(?:0x)?[0-9a-fA-F]+)"
)
CAPTURE_MAP_RE = re.compile(
    r"omap5430-sgx: capture-map name=(?P<name>\S+) "
    r"va=(?P<va>0x[0-9a-fA-F]+) pd=(?P<pd>0x[0-9a-fA-F]+) "
    r"pde-pa=(?P<pde_pa>0x[0-9a-fA-F]+) pde=(?P<pde>0x[0-9a-fA-F]+) "
    r"pte-pa=(?P<pte_pa>0x[0-9a-fA-F]+) pte=(?P<pte>0x[0-9a-fA-F]+) "
    r"page-shift=(?P<page_shift>\d+) pa=(?P<pa>0x[0-9a-fA-F]+)"
)
UNHANDLED_RE = re.compile(
    r"omap5430-sgx: unhandled KCCB entry=(?P<entry>\d+) "
    r"va=(?P<va>0x[0-9a-fA-F]+) service=(?P<service>0x[0-9a-fA-F]+)"
)

CORE_ID_OFFSET = 0x8020
CORE_REVISION_OFFSET = 0x8024
USE_CODE_BASE_FIRST = 0x0A0C
USE_CODE_BASE_LAST = 0x0A48
USE_CODE_BASE_ADDRESS_MASK = 0x03FFFFFF
USE_CODE_BASE_DATA_MASTER_MASK = 0x0C000000


def parse_hex(value: str) -> int:
    return int(value.removeprefix("0x"), 16)


def load_trace(path: Path) -> dict:
    accesses = []
    events = []
    memory = []
    use_code_bases = []
    capture_maps = []
    unhandled = []

    for line_number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
        if match := ACCESS_RE.search(line):
            accesses.append(
                {
                    "line": line_number,
                    "operation": match["operation"],
                    "offset": parse_hex(match["offset"]),
                    "value": parse_hex(match["value"]),
                }
            )
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
        if match := MEMORY_RE.search(line):
            memory.append(
                {
                    "line": line_number,
                    "space": match["space"],
                    "va": parse_hex(match["va"]),
                    "pa": parse_hex(match["pa"]),
                    "word": parse_hex(match["word"]),
                }
            )
        if match := CAPTURE_MAP_RE.search(line):
            capture_maps.append(
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
        if match := UNHANDLED_RE.search(line):
            unhandled.append(
                {
                    "line": line_number,
                    "entry": int(match["entry"]),
                    "va": parse_hex(match["va"]),
                    "service": parse_hex(match["service"]),
                }
            )

    use_code_bases = []
    for access in accesses:
        offset = access["offset"]
        if (
            access["operation"] == "write"
            and USE_CODE_BASE_FIRST <= offset <= USE_CODE_BASE_LAST
            and (offset - USE_CODE_BASE_FIRST) % 4 == 0
        ):
            value = access["value"]
            use_code_bases.append(
                {
                    "slot": (offset - USE_CODE_BASE_FIRST) // 4,
                    "offset": offset,
                    "value": value,
                    "address": value & USE_CODE_BASE_ADDRESS_MASK,
                    "gpu_va_candidate": (value & USE_CODE_BASE_ADDRESS_MASK) << 6,
                    "data_master": (value & USE_CODE_BASE_DATA_MASTER_MASK) >> 26,
                }
            )

    core_reads = [
        access
        for access in accesses
        if access["operation"] == "read"
        and access["offset"] in (CORE_ID_OFFSET, CORE_REVISION_OFFSET)
    ]

    return {
        "source_log": str(path.resolve()),
        "access_count": len(accesses),
        "accesses": accesses,
        "core_id_revision_mmio_reads": core_reads,
        "events": events,
        "memory_words": memory,
        "use_code_bases": use_code_bases,
        "capture_maps": capture_maps,
        "unhandled_kccb": unhandled,
    }


def format_text(result: dict) -> str:
    lines = [
        f"Trace: {result['source_log']}",
        f"SGX MMIO accesses: {result['access_count']}",
        "Direct CPU MMIO reads of CORE_ID/CORE_REVISION: "
        f"{len(result['core_id_revision_mmio_reads'])}",
    ]
    for access in result["core_id_revision_mmio_reads"]:
        name = "CORE_ID" if access["offset"] == CORE_ID_OFFSET else "CORE_REVISION"
        lines.append(
            f"  {name} offset={access['offset']:#06x} value={access['value']:#010x}"
        )

    lines.append(f"USE code-base writes: {len(result['use_code_bases'])}")
    for entry in result["use_code_bases"]:
        lines.append(
            f"  slot={entry['slot']:2} offset={entry['offset']:#06x} "
            f"value={entry['value']:#010x} address={entry['address']:#010x} "
            f"dm={entry['data_master']} va-candidate={entry['gpu_va_candidate']:#010x}"
        )

    lines.append(f"Firmware events: {len(result['events'])}")
    for event in result["events"]:
        lines.append(
            f"  #{event['event']} pd={event['pd']:#010x} "
            f"pds={event['pds']:#010x} info={event['info']:#x} "
            f"data={event['data']:#x}"
        )

    pds_page_words = [
        word for word in result["memory_words"] if word["space"] == "PDS-PAGE"
    ]
    pds_event_words = [
        word for word in result["memory_words"] if word["space"] == "PDS"
    ]
    use_code_words = [word for word in result["memory_words"] if word["space"] == "USE-CODE"]
    use_candidate_words = [
        word for word in result["memory_words"] if word["space"] == "USE-CANDIDATE"
    ]
    lines.append(f"Captured PDS page words: {len(pds_page_words)}")
    lines.append(f"Captured PDS event sample words: {len(pds_event_words)}")
    lines.append(f"Captured USE code words: {len(use_code_words)}")
    lines.append(f"Captured USE candidate words: {len(use_candidate_words)}")
    for base in result["use_code_bases"]:
        lines.append(
            f"  USE base slot={base['slot']} value={base['value']:#010x} "
            f"field={base['address']:#010x} dm={base['data_master']} "
            f"va-candidate={base['gpu_va_candidate']:#010x}"
        )
    for mapping in result["capture_maps"]:
        lines.append(
            f"  mapping {mapping['name']} va={mapping['va']:#010x} "
            f"pa={mapping['pa']:#010x} page-shift={mapping['page_shift']} "
            f"pde={mapping['pde']:#010x} pte={mapping['pte']:#010x}"
        )
    for word in pds_page_words[:16]:
        lines.append(
            f"  {word['space']} va={word['va']:#010x} "
            f"pa={word['pa']:#010x} word={word['word']:#010x}"
        )
    for word in pds_event_words:
        lines.append(
            f"  PDS event va={word['va']:#010x} "
            f"pa={word['pa']:#010x} word={word['word']:#010x}"
        )
    if len(pds_page_words) > 16:
        lines.append(
            f"  ... {len(pds_page_words) - 16} additional page words; use --json for all"
        )
    for word in (use_code_words + use_candidate_words)[:32]:
        lines.append(
            f"  {word['space']} va={word['va']:#010x} "
            f"pa={word['pa']:#010x} word={word['word']:#010x}"
        )
    if len(use_code_words) + len(use_candidate_words) > 32:
        lines.append(
            f"  ... {len(use_code_words) + len(use_candidate_words) - 32} additional "
            "USE words; "
            "use --json for all"
        )

    lines.append(f"Unhandled KCCB requests: {len(result['unhandled_kccb'])}")
    for request in result["unhandled_kccb"]:
        lines.append(
            f"  entry={request['entry']} va={request['va']:#010x} "
            f"service={request['service']:#x}"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, help="QEMU debug log from an OMAP5 SGX run")
    parser.add_argument("--json", action="store_true", help="emit the complete summary as JSON")
    args = parser.parse_args()

    if not args.trace.is_file():
        parser.error(f"trace is not a regular file: {args.trace}")

    try:
        result = load_trace(args.trace)
    except OSError as exc:
        print(f"cannot read trace: {exc}", file=sys.stderr)
        return 1

    if (
        not result["access_count"]
        and not result["events"]
        and not result["memory_words"]
        and not result["use_code_bases"]
    ):
        parser.error("no OMAP5 SGX trace records were found")

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
