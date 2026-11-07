#!/usr/bin/env python3
"""Decode captured SGX firmware words using Vita3K's pinned USSE grammar.

This is an instruction-field decoder, not an emulator. SGX544 differences from
Vita3K's SGX543 grammar can produce unknown or ambiguous instructions.
"""
import argparse
import json
import struct
from pathlib import Path

import yaml


def load_grammar(path):
    instructions = []
    for name, definition in yaml.safe_load(path.read_text()).items():
        cursor, mask, expected = 64, 0, 0
        fields = []
        for member in definition["members"]:
            for field, properties in member.items():
                if isinstance(properties, str):
                    properties = {"size": len(properties), "match": properties}
                elif isinstance(properties, int):
                    properties = {"size": properties}
                size = properties["size"]
                shift = properties.get("offset", cursor - size)
                if shift < 0 or shift + size > cursor:
                    raise ValueError(f"Invalid layout in {name}.{field}")
                cursor = shift
                field_mask = (1 << size) - 1
                if "match" in properties:
                    pattern = properties["match"]
                    if len(pattern) != size or any(c not in "01" for c in pattern):
                        raise ValueError(f"Invalid match in {name}.{field}")
                    mask |= field_mask << shift
                    expected |= int(pattern, 2) << shift
                else:
                    fields.append((field, shift, field_mask))
        instructions.append((name, mask, expected, fields))
    return instructions


def is_sgx543_lapc_return(word):
    """Recognize Vita3K's SGX543 LAPC/return encoding.

    This narrowly matches the return predicate in Vita3K's USSE analyzer; it
    is a reference classification, not proof of SGX544 execution semantics.
    """
    high = (word >> 32) & 0xFFFFFFFF
    op_shift = (high & 0xF8000000) >> 27
    op_mask = (high & 0x00300000) >> 20
    link_bit_clear = not (high & 0x00400000)
    op_check = (high & 0x000001C0) >> 6
    return op_shift == 0b11111 and op_mask == 0 and link_bit_clear and op_check == 2


def decode_usse_table_candidate(word):
    """Return opcode-name candidates from an older public USSE reference table.

    The table's placement on an SGX544 wiki page does not establish its
    dialect. In particular, this function intentionally reports no branch
    width, offset, target, predicate, or link semantics.
    """
    word1 = (word >> 32) & 0xFFFFFFFF
    if (word1 >> 27) != 0x1F:
        return None
    op1 = (word1 >> 24) & 7
    op2 = (word1 >> 20) & 3
    if op1 == 0 and op2 == 0 and ((word1 >> 6) & 7) == 0:
        return "BA"
    if (op1, op2) == (1, 2):
        return "WDF"
    if (op1, op2) == (3, 2):
        return "EMIT"
    if (op1, op2) == (6, 2):
        return "STR" if word1 & (1 << 19) else "LDR"
    return None


def decode(word, grammar):
    if is_sgx543_lapc_return(word):
        return [{"op": "LAPC", "fields": {}, "specificity": 64}]

    matches = []
    for name, mask, expected, fields in grammar:
        if word & mask != expected:
            continue
        decoded_fields = {field: (word >> shift) & bits
                          for field, shift, bits in fields}
        # VLDST is a broad top-three-bit class in Vita3K's grammar, but only
        # op1 values 1 (load) and 2 (store) are defined by its comment.
        if name == "VLDST" and decoded_fields.get("op1") not in (1, 2):
            continue
        matches.append({"op": name, "fields": decoded_fields,
                        "specificity": mask.bit_count()})

    # SPEC and VLDST are fallback classes. Prefer a more-specific opcode
    # pattern when one also matches, while preserving genuine ties for review.
    if matches:
        specificity = max(match["specificity"] for match in matches)
        matches = [match for match in matches
                   if match["specificity"] == specificity]
    return matches


def format_match(match):
    fields = match["fields"]
    if match["op"] == "LIMM":
        immediate = (fields.get("imm_value_first_21bits", 0) |
                     fields.get("imm_value_bits21to25", 0) << 21 |
                     fields.get("imm_value_bits26to31", 0) << 26)
        fields = {**fields, "immediate": immediate}
    formatted = ", ".join(f"{name}={value:#x}"
                           for name, value in fields.items() if value)

    if match["op"] == "I32MAD":
        # These bank tables follow Vita3K's SGX543 decoder. They are labels for
        # inspection, not a claim that SGX544 executes every field identically.
        dest_banks = ["TEMP", "OUTPUT", "PRIMATTR", "INDEXED1"]
        extended_dest_banks = ["SECATTR", "SPECIAL", "INDEX", "INDEXED2"]
        src0_banks = ["TEMP", "PRIMATTR"]
        src12_banks = ["TEMP", "OUTPUT", "PRIMATTR", "SECATTR"]
        extended_src12_banks = ["INDEXED1", "SPECIAL", "IMMEDIATE", "INDEXED2"]

        dest_table = (extended_dest_banks if fields.get("dest_bank_ext")
                      else dest_banks)
        src1_table = (extended_src12_banks if fields.get("src1_bank_ext")
                      else src12_banks)
        src2_table = (extended_src12_banks if fields.get("src2_bank_ext")
                      else src12_banks)
        banked_registers = (
            ("dest", dest_table, "dest_bank", "dest_n"),
            ("src0", src0_banks, "src0_bank", "src0_n"),
            ("src1", src1_table, "src1_bank", "src1_n"),
            ("src2", src2_table, "src2_bank", "src2_n"),
        )
        operands = []
        for operand, table, bank_field, number_field in banked_registers:
            bank = fields.get(bank_field, 0)
            number = fields.get(number_field, 0)
            if bank < len(table):
                operands.append(f"{operand}:{table[bank]}[{number}/0x{number:x}]")
        formatted += (" " if formatted else "") + "SGX543-banks(" + ",".join(operands) + ")"

    if match["op"] == "VLDST":
        formatted += (
            (" " if formatted else "") +
            "SGX543-field-candidates(" +
            f"dest-bank-primattr={fields.get('dest_bank_primattr', 0)}," +
            f"dest-n={fields.get('dest_n', 0)}," +
            f"mode={fields.get('mode', 0)}," +
            f"addr-mode={fields.get('addr_mode', 0)})"
        )

    if match["op"] == "BR":
        formatted += (
            (" " if formatted else "") +
            "SGX543-field-candidates(" +
            f"br-type={fields.get('br_type', 0)}," +
            f"save-link={fields.get('save_link', 0)}," +
            f"br-off={fields.get('br_off', 0):#x})"
        )

    if match["op"] == "PHAS":
        # Project Cascadia's SGX543 analysis treats a nonzero low-20-bit
        # address as the next phase's instruction index. Keep this explicitly
        # labeled as an SGX543 reference candidate for the SGX544-class target.
        next_phase = (
            fields.get("exe_addr_high", 0) << 14 |
            fields.get("src1_n_or_exe_addr_mid", 0) << 7 |
            fields.get("src2_n_or_exe_addr_low", 0)
        )
        phase_note = (
            "SGX543-phase(next-index-candidate="
            f"{next_phase:#x},wait-cond={fields.get('wait_cond', 0)},"
            f"temp-count={fields.get('temp_count', 0)})"
        )
        formatted += (" " if formatted else "") + phase_note

    return formatted


def number(value):
    return int(value, 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("--offset", type=number, default=0)
    parser.add_argument("--count", type=number, default=32)
    parser.add_argument("--base", type=number, default=0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.offset < 0 or args.offset % 8 or args.count < 0:
        parser.error("offset must be nonnegative and 8-byte aligned; count must be nonnegative")
    data = args.binary.read_bytes()
    grammar = load_grammar(Path(__file__).resolve().parent.parent /
                           "third_party/vita3k/usse-grammar.yaml")
    records = []
    for offset in range(args.offset, min(len(data) - 7, args.offset + args.count * 8), 8):
        word = struct.unpack_from("<Q", data, offset)[0]
        matches = decode(word, grammar)
        usse_table_candidate = decode_usse_table_candidate(word)
        records.append({"address": args.base + offset, "word": word,
                        "matches": matches,
                        "usse_table_candidate": usse_table_candidate})
        if not args.json:
            if matches:
                result = matches[0]
                fields = format_match(result)
                other = " [ambiguous: " + ",".join(m["op"] for m in matches[1:]) + "]" if len(matches) > 1 else ""
                decoded = f"{result['op']} {fields}{other}"
            else:
                decoded = "UNKNOWN"
            if usse_table_candidate:
                decoded += f" USSE-table-candidate({usse_table_candidate})"
            print(f"{args.base + offset:08x}: {word:016x}  {decoded}")
    if args.json:
        print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
