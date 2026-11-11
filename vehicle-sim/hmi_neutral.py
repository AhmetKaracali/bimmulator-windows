"""Build neutral (minimum valid) payloads for MOST properties from hmi_layouts.json.
Primitive readers (HmiMain3D 006): u8 0x1f91e70(min,max), u16 0x1f923b8, s16 0x1f9233c,
u32 0x1f922c4, s32 0x1f9224c, bool 0x1f91ce0, full-range u8 wrappers, u16 0x1f92418,
remaining-bytes buffer 0x1f920f0 (may be empty), end-check 0x1f91b88 (no data)."""
import json, struct, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
import os
# hmi_layouts.json / helper_sizes.json: generate them from YOUR HmiMain3D with hmi_layouts.py and
# hmi_helper_sizes.py. hmi_most_map.json comes from a local herrbimmer/IDEmu checkout
# (IDRIVE_IDEMU_DIR, PolyForm Noncommercial, not redistributed here). Missing files = feature off.
IDEMU = Path(os.environ.get("IDRIVE_IDEMU_DIR", Path.home() / "IDEmu"))
def _load(path, default):
    try:
        return json.load(open(path))
    except (OSError, ValueError):
        return default
L = _load(HERE / "hmi_layouts.json", {})
M = _load(IDEMU / "idemu" / "data" / "hmi_most_map.json", {"devices": [], "functions": {}})
SIZES = {int(k, 16): v for k, v in _load(HERE / "helper_sizes.json", {}).items()}
U8W = {0x227158c, 0x205ff74, 0x207d4ac, 0x204d01c, 0x2041ddc, 0x20fe4b4, 0x1f91ed0}
IGN = {0x1f91b88, 0x25913c, 0x20c460, 0x227180, 0x20c1c0, 0x210d44, 0x1f85c60, 0x1f85c3c,
       0x295f518, 0x295f474, 0x1fdba5c, 0x275ac4, 0x1f9161c,
       0x735708, 0x3feb20, 0x1585e10, 0x1f8f128, 0x1f9b0a0}     # delegate lock/notify, stream ctor

LIST_HEADERS = {0x1f8d0dc, 0x1f8d0b0, 0x1f8d108}   # an all-zero header = empty list
# 1-byte readers: s8 0x1f91de0 (ldrsb + range), enum 0x1f91ae8 (readUByte, 0 always accepted),
# readUByte itself 0x258df8.
ONE_BYTE = {0x1f91de0, 0x1f91ae8, 0x258df8}


def enc(reads):
    out = b""
    in_list = False
    for h, lo, hi in reads:
        lo = lo or 0
        if h in LIST_HEADERS:
            in_list = True
        if h == 0x1f91e70: out += struct.pack(">B", lo & 0xff)
        elif h in ONE_BYTE:
            s = lo - (1 << 32) if lo >= (1 << 31) else lo        # ranges are stored as u32
            top = hi if hi is not None else 127
            val = 0 if s <= 0 <= top else s
            out += struct.pack(">b", max(-128, min(127, val))) if h == 0x1f91de0 else b"\0"
        elif h in U8W or h == 0x1f91ce0: out += b"\0"
        elif h in (0x1f923b8,): out += struct.pack(">H", lo & 0xffff)
        elif h in (0x1f92418, 0x1f9233c): out += b"\0\0"
        elif h == 0x1f8d0dc: out += b"\0\0"
        elif h == 0x1f8d0b0: out += b"\0\0\0"
        elif h in (0x1f922c4, 0x1f9224c): out += struct.pack(">I", lo & 0xffffffff)
        elif h == 0x1f920f0: pass
        elif h == 0x1f921fc: out += b"\x00\x00\x00"        # MOST string: encoding 0 (UTF-16) + NUL
        elif h == 0x1f8d108: out += b"\0\0"                # two u8
        elif h in (0x21051d8, 0x20fdc70): out += b"\0"    # u8 enum wrappers
        elif h == 0x1f86880: out += b"\0" * 7               # u16+u8, u16, u16
        elif h in IGN: pass
        elif h in (0x1f9aff0,): pass                       # nested sub-stream (empty)
        elif h in SIZES: out += bytes(SIZES[h])
        elif in_list: pass          # element reader of an empty list: never called at runtime
        else: return None, hex(h)
    return out, None

def lookup(fb, inst, fkt):
    groups = [d["group"] for d in M["devices"] if d["fblock"] == fb and d["inst"] == inst]
    # instance not in the map: any group that uses this FBlock id on another instance
    groups += [d["group"] for d in M["devices"] if d["fblock"] == fb and d["group"] not in groups]
    for g in groups:
        cls = M["functions"].get(g, {}).get(str(fkt))
        for name in (cls, f"C{cls}") if cls else ():
            if f"{g}::{name}" in L:          # the map drops the C prefix for some classes
                return f"{g}::{name}", L[f"{g}::{name}"]["reads"]
    return None, None

if __name__ == "__main__":
    for key in sys.argv[1:]:
        fb, inst, fkt = (int(x, 16) for x in key.split(":"))
        name, reads = lookup(fb, inst, fkt)
        if not reads: print(key, name, "no layout"); continue
        p, bad = enc(reads)
        print(key, name, p.hex() if p is not None else f"unknown helper {bad}", [hex(r[0]) for r in reads])
