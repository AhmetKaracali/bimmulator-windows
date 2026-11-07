#!/usr/bin/env python3
"""Find ARM/Thumb call sites for imported GLES symbols in a QNX ELF.

The staged BMW executables are stripped and one contains section indices that
the host disassembler rejects. This small reader uses the ELF dynamic symbol
table and ARM unwind index to find callsites without rewriting the firmware.
Run from the Nix analysis shell, which provides Capstone:

    python3 tools/trace-qnx-gles-callers.py HmiMain3D glShaderBinary glShaderSource
"""

from __future__ import annotations

import argparse
import bisect
import re
import struct
import sys
from pathlib import Path


ELF_HEADER = struct.Struct("<16sHHIIIIIHHHHHH")
SECTION_HEADER = struct.Struct("<IIIIIIIIII")
SYMBOL = struct.Struct("<IIIBBH")
BRANCH_TARGET = re.compile(r"#?(0x[0-9a-fA-F]+|-?[0-9]+)")


class ElfError(ValueError):
    pass


def c_string(data: bytes, offset: int) -> str:
    if offset < 0 or offset >= len(data):
        return ""
    end = data.find(b"\0", offset)
    if end < 0:
        return ""
    return data[offset:end].decode("utf-8", "replace")


def prel31(word: int, place: int) -> int:
    displacement = word & 0x7FFFFFFF
    if displacement & 0x40000000:
        displacement -= 0x80000000
    return (place + displacement) & 0xFFFFFFFF


class Elf32:
    def __init__(self, path: Path):
        self.path = path
        self.data = path.read_bytes()
        if len(self.data) < ELF_HEADER.size:
            raise ElfError("file is shorter than the ELF header")
        header = ELF_HEADER.unpack_from(self.data)
        ident = header[0]
        if ident[:4] != b"\x7fELF" or ident[4] != 1 or ident[5] != 1:
            raise ElfError("expected a little-endian ELF32 file")
        self.machine = header[2]
        self.sh_offset = header[6]
        self.sh_entry_size = header[11]
        self.sh_count = header[12]
        self.sh_name_index = header[13]
        self.ph_offset = header[5]
        self.ph_entry_size = header[9]
        self.ph_count = header[10]
        if self.sh_entry_size < SECTION_HEADER.size:
            raise ElfError("section header entry is too small")

        raw_sections = []
        for index in range(self.sh_count):
            offset = self.sh_offset + index * self.sh_entry_size
            if offset + SECTION_HEADER.size > len(self.data):
                raise ElfError("truncated section header table")
            raw_sections.append(SECTION_HEADER.unpack_from(self.data, offset))
        if self.sh_name_index >= len(raw_sections):
            raise ElfError("invalid section-name table index")
        name_section = raw_sections[self.sh_name_index]
        names = self.data[name_section[4] : name_section[4] + name_section[5]]
        self.sections = {}
        for section in raw_sections:
            name = c_string(names, section[0])
            if name:
                self.sections[name] = section
        self.load_segments = []
        for index in range(self.ph_count):
            offset = self.ph_offset + index * self.ph_entry_size
            if offset + 32 > len(self.data):
                raise ElfError("truncated program header table")
            p_type, p_offset, p_vaddr, _p_paddr, p_filesz, _p_memsz, _flags, _align = (
                struct.unpack_from("<IIIIIIII", self.data, offset)
            )
            if p_type == 1:  # PT_LOAD
                self.load_segments.append((p_vaddr, p_offset, p_filesz))

    def section_bytes(self, name: str) -> bytes:
        section = self.sections.get(name)
        if section is None:
            return b""
        return self.data[section[4] : section[4] + section[5]]

    def read_vaddr_u32(self, address: int) -> int | None:
        for vaddr, offset, size in self.load_segments:
            if vaddr <= address and address + 4 <= vaddr + size:
                file_offset = offset + address - vaddr
                return struct.unpack_from("<I", self.data, file_offset)[0]
        return None

    def dynamic_symbols(self) -> dict[str, tuple[int, int, int]]:
        section = self.sections.get(".dynsym")
        if section is None:
            return {}
        if section[6] >= self.sh_count:
            raise ElfError(".dynsym has an invalid string-table link")
        string_header = SECTION_HEADER.unpack_from(
            self.data, self.sh_offset + section[6] * self.sh_entry_size
        )
        strings = self.data[
            string_header[4] : string_header[4] + string_header[5]
        ]
        stride = section[9] or SYMBOL.size
        symbols = {}
        for cursor in range(section[4], section[4] + section[5], stride):
            if cursor + SYMBOL.size > len(self.data):
                break
            name_offset, value, size, info, _other, shndx = SYMBOL.unpack_from(
                self.data, cursor
            )
            name = c_string(strings, name_offset)
            if name:
                symbols[name] = (value, size, shndx)
        return symbols

    def plt_symbols(self) -> dict[str, int]:
        """Map imported names to their ARM PLT stubs from .rel.plt order."""
        dynsym = self.sections.get(".dynsym")
        dynstr = self.sections.get(".dynstr")
        relocations = self.sections.get(".rel.plt")
        plt = self.sections.get(".plt")
        if not (dynsym and dynstr and relocations and plt):
            return {}
        strings = self.data[dynstr[4] : dynstr[4] + dynstr[5]]
        stride = dynsym[9] or SYMBOL.size
        names = []
        values = []
        for cursor in range(dynsym[4], dynsym[4] + dynsym[5], stride):
            if cursor + SYMBOL.size > len(self.data):
                break
            name_offset, value, _size, _info, _other, _shndx = SYMBOL.unpack_from(
                self.data, cursor
            )
            names.append(c_string(strings, name_offset))
            values.append(value)

        # ARM32 PLT0 is 20 bytes; each following entry is three instructions.
        stubs = {}
        for index, cursor in enumerate(
            range(relocations[4], relocations[4] + relocations[5], 8)
        ):
            if cursor + 8 > len(self.data):
                break
            _offset, info = struct.unpack_from("<II", self.data, cursor)
            symbol_index = info >> 8
            if symbol_index >= len(names) or not names[symbol_index]:
                continue
            value = values[symbol_index]
            stubs[names[symbol_index]] = (
                value if value else plt[3] + 20 + index * 12
            )
        return stubs

    def unwind_functions(self, text_start: int, text_end: int) -> list[tuple[int, bool]]:
        section = self.sections.get(".ARM.exidx")
        if section is None:
            return []
        functions = []
        for cursor in range(section[4], section[4] + section[5], 8):
            if cursor + 8 > len(self.data):
                break
            word = struct.unpack_from("<I", self.data, cursor)[0]
            place = section[3] + cursor - section[4]
            address = prel31(word, place)
            thumb = bool(address & 1)
            address &= ~1
            if text_start <= address < text_end:
                functions.append((address, thumb))
        return sorted(set(functions))


def parse_branch_target(operands: str) -> int | None:
    match = BRANCH_TARGET.search(operands)
    if not match:
        return None
    try:
        return int(match.group(1), 0) & 0xFFFFFFFF
    except ValueError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("elf", type=Path, help="stripped QNX ELF executable/shared object")
    parser.add_argument("symbols", nargs="+", help="GLES import names to trace")
    args = parser.parse_args()

    try:
        from capstone import (
            Cs,
            CS_ARCH_ARM,
            CS_MODE_ARM,
            CS_MODE_LITTLE_ENDIAN,
            CS_MODE_THUMB,
        )
    except ImportError:
        print("Capstone is missing; run inside the default `nix develop` shell", file=sys.stderr)
        return 2

    try:
        elf = Elf32(args.elf)
        text = elf.sections.get(".text")
        if text is None:
            raise ElfError("ELF has no .text section")
        text_start = text[3]
        text_end = text_start + text[5]
        symbols = elf.dynamic_symbols()
        plt_symbols = elf.plt_symbols()
        targets = {}
        for name in args.symbols:
            value = symbols.get(name)
            if value is None or value[0] == 0:
                value = (plt_symbols.get(name), 0, 0)
            targets[name] = value
        missing = [name for name, value in targets.items() if value[0] is None]
        if missing:
            raise ElfError("dynamic symbols not found: " + ", ".join(missing))

        functions = elf.unwind_functions(text_start, text_end)
        modes = {thumb for _address, thumb in functions}
        if len(modes) > 1:
            raise ElfError("mixed ARM/Thumb unwind entries need per-function decoding")
        thumb = next(iter(modes)) if modes else False
        mode = CS_MODE_THUMB if thumb else CS_MODE_ARM
        disassembler = Cs(CS_ARCH_ARM, mode | CS_MODE_LITTLE_ENDIAN)
        disassembler.skipdata = True
        disassembler.skipdata_setup = ("db", None, 2 if thumb else 4)

        target_to_name = {}
        for name, (value, _size, _section) in targets.items():
            if not (0 <= value < 0xFFFFFFFF):
                raise ElfError(f"{name} has no usable PLT address")
            target_to_name.setdefault(value & ~1, []).append(name)

        code = elf.data[text[4] : text[4] + text[5]]
        found = []
        indirect = []
        pc_load = re.compile(
            r"(r(?:1[0-2]|[0-9])), \[pc, #(-?(?:0x[0-9a-fA-F]+|[0-9]+))\]"
        )
        move_pc = re.compile(r"pc, (r(?:1[0-2]|[0-9]+))$")
        blx_register = re.compile(r"(r(?:1[0-2]|[0-9]+))$")
        previous: tuple[int, str, str] | None = None
        last_loaded: dict[str, tuple[int, int, list[str]]] = {}
        for address, _size, mnemonic, operands in disassembler.disasm_lite(code, text_start):
            # QNX's ARM compiler frequently emits `mov lr, pc; mov pc, rN`
            # instead of BLX for imported calls. Resolve simple PC-literal loads
            # of the corresponding PLT address and retain only an unmodified
            # register through the call sequence.
            if mnemonic == "mov" and previous == (address - 4, "mov", "lr, pc"):
                call = move_pc.fullmatch(operands)
                if call:
                    register = call.group(1)
                    loaded = last_loaded.get(register)
                    if loaded and address - loaded[0] <= 24:
                        load_address, target, names = loaded
                        indirect.append((address, target, load_address, names))
            elif mnemonic == "blx":
                call = blx_register.fullmatch(operands)
                if call:
                    loaded = last_loaded.get(call.group(1))
                    if loaded and address - loaded[0] <= 24:
                        load_address, target, names = loaded
                        indirect.append((address, target, load_address, names))

            if mnemonic not in ("bl", "blx"):
                target = None
            else:
                target = parse_branch_target(operands)
                names = target_to_name.get(target) if target is not None else None
                if names:
                    if functions:
                        index = bisect.bisect_right(functions, (address, True)) - 1
                        function_start, function_thumb = functions[index]
                        function_end = functions[index + 1][0] if index + 1 < len(functions) else text_end
                        if function_start <= address < function_end and function_thumb == thumb:
                            found.append((address, target, function_start, function_end, names))
                    else:
                        found.append((address, target, 0, 0, names))

            load = pc_load.search(operands) if mnemonic == "ldr" else None
            if load:
                register = load.group(1)
                displacement = int(load.group(2), 0)
                pc = address + (4 if thumb else 8)
                literal = ((pc + 3) & ~3) + displacement if thumb else pc + displacement
                value = elf.read_vaddr_u32(literal)
                names = target_to_name.get(value & ~1) if value is not None else None
                if names:
                    last_loaded[register] = (address, value & ~1, names)
                else:
                    last_loaded.pop(register, None)
            else:
                # A normal destination write invalidates any remembered target.
                destination = operands.split(",", 1)[0].strip()
                if destination in last_loaded:
                    last_loaded.pop(destination, None)
            previous = (address, mnemonic, operands)

        print(f"ELF: {args.elf}")
        print(f".text: 0x{text_start:08x}-0x{text_end:08x} ({text[5]} bytes)")
        print(
            f".ARM.exidx: {len(functions)} function boundaries; "
            f"mode={'Thumb' if thumb else 'ARM'}"
        )
        for name, (value, size, _section) in targets.items():
            print(f"import {name}: stub=0x{value:08x} symbol_size={size}")
        if not found and not indirect:
            print("No direct BL/BLX or simple PC-literal indirect calls to selected stubs were found.")
        for address, target, start, end, names in found:
            caller = (
                f"enclosing function 0x{start:08x}-0x{end:08x}"
                if start or end
                else "no unwind function boundary available"
            )
            print(f"call 0x{address:08x} -> 0x{target:08x} ({', '.join(names)}); {caller}")
        for address, target, load_address, names in indirect:
            index = bisect.bisect_right(functions, (address, True)) - 1
            function_start = functions[index][0]
            function_end = functions[index + 1][0] if index + 1 < len(functions) else text_end
            print(
                f"indirect call 0x{address:08x} -> 0x{target:08x} ({', '.join(names)}); "
                f"PC-literal load 0x{load_address:08x}; "
                f"enclosing function 0x{function_start:08x}-0x{function_end:08x}"
            )
        return 0
    except (OSError, ElfError, struct.error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
