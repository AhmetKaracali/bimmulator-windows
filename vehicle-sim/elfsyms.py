#!/usr/bin/env python3
"""Minimal ELF32 LE symbol tools for porting fixed offsets between firmware builds.

  elfsyms.py where BIN OFFSET...        -> symbol (+delta) containing each file offset
  elfsyms.py find  BIN SYMBOL...        -> file offset + size of each symbol
  elfsyms.py port  OLD NEW OFFSET:HEX.. -> port each patch via its enclosing symbol, verify bytes
"""
import struct
import sys


class Elf:
    def __init__(self, path):
        self.data = data = open(path, "rb").read()
        if data[:4] != b"\x7fELF" or data[4] != 1:
            raise SystemExit(f"not ELF32: {path}")
        shoff, = struct.unpack_from("<I", data, 0x20)
        shentsize, shnum = struct.unpack_from("<HH", data, 0x2E)
        phoff, = struct.unpack_from("<I", data, 0x1C)
        phentsize, phnum = struct.unpack_from("<HH", data, 0x2A)
        self.loads = []
        for i in range(phnum):
            p_type, p_offset, p_vaddr, _pa, p_filesz = struct.unpack_from("<IIIII", data, phoff + i * phentsize)
            if p_type == 1:
                self.loads.append((p_vaddr, p_offset, p_filesz))
        secs = [struct.unpack_from("<IIIIIIIIII", data, shoff + i * shentsize) for i in range(shnum)]
        self.secs = secs
        shstr = secs[struct.unpack_from("<H", data, 0x32)[0]] if shnum else None
        self.secnames = {}
        if shstr:
            for s in secs:
                start = shstr[4] + s[0]
                self.secnames[data[start:data.index(b"\0", start)].decode("latin-1")] = s
        self.symbols = {}
        for s in secs:
            if s[1] in (2, 11):  # SYMTAB, DYNSYM
                strtab = secs[s[6]]
                for j in range(s[5] // 16):
                    name, value, size, info, _o, shndx = struct.unpack_from("<IIIBBH", data, s[4] + j * 16)
                    if size == 0 or shndx == 0:
                        continue
                    start = strtab[4] + name
                    nm = data[start:data.index(b"\0", start)].decode("latin-1")
                    if nm:
                        self.symbols[nm] = (value & ~1, size)

    def plt_map(self):
        """PLT stub address -> imported symbol name (ARM: 20-byte PLT0, 12-byte stubs)."""
        plt, rel = self.secnames.get(".plt"), self.secnames.get(".rel.plt")
        dynsym, dynstr = self.secnames.get(".dynsym"), self.secnames.get(".dynstr")
        if not (plt and rel and dynsym and dynstr):
            return {}
        out = {}
        for i in range(rel[5] // 8):
            _off, info = struct.unpack_from("<II", self.data, rel[4] + 8 * i)
            sym = info >> 8
            name_off = struct.unpack_from("<I", self.data, dynsym[4] + 16 * sym)[0]
            start = dynstr[4] + name_off
            name = self.data[start:self.data.index(b"\0", start)].decode("latin-1")
            out[plt[3] + 20 + 12 * i] = name
        return out

    def v2o(self, vaddr):
        for va, off, sz in self.loads:
            if va <= vaddr < va + sz:
                return vaddr - va + off
        return None

    def o2v(self, offset):
        for va, off, sz in self.loads:
            if off <= offset < off + sz:
                return offset - off + va
        return None

    def where(self, offset):
        v = self.o2v(offset)
        for nm, (val, size) in self.symbols.items():
            if val <= v < val + size:
                return nm, v - val
        return None, None


def main():
    cmd = sys.argv[1]
    if cmd == "where":
        e = Elf(sys.argv[2])
        for o in sys.argv[3:]:
            print(o, *e.where(int(o, 16)))
    elif cmd == "find":
        e = Elf(sys.argv[2])
        for nm in sys.argv[3:]:
            hit = e.symbols.get(nm)
            print(nm, hex(e.v2o(hit[0])) if hit else None, hit and hex(hit[1]))
    elif cmd == "port":
        a, b = Elf(sys.argv[2]), Elf(sys.argv[3])
        for spec in sys.argv[4:]:
            off, hexexp = spec.split(":")
            off = int(off, 16)
            exp = bytes.fromhex(hexexp)
            nm, delta = a.where(off)
            if nm is None or nm not in b.symbols:
                print(spec, "symbol", nm, "not in new binary")
                continue
            va, size = b.symbols[nm]
            base = b.v2o(va)
            func = b.data[base:base + size]
            hits = [base + i for i in range(0, len(func) - len(exp) + 1, 2) if func[i:i + len(exp)] == exp]
            same_delta = base + delta if b.data[base + delta:base + delta + len(exp)] == exp else None
            print(f"{spec} in {nm}+{delta:#x} (old size {a.symbols[nm][1]:#x}, new {size:#x}) "
                  f"-> same-delta {hex(same_delta) if same_delta else None}, matches {[hex(h) for h in hits]}")


if __name__ == "__main__":
    main()
