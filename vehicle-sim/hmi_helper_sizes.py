"""Classify small reader helpers by the primitive reads they make (writes helper_sizes.json)."""
import json, sys, collections, capstone
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from elfsyms import Elf
e = Elf(sys.argv[1] if len(sys.argv) > 1 else "HmiMain3D")   # usage: hmi_helper_sizes.py <HmiMain3D>
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
PRIM = {0x1f91e70: 1, 0x258df8: 1, 0x1f923b8: 2, 0x20f004: 2, 0x1f922c4: 4, 0x20d894: 4, 0x1f91ce0: 1,
        0x1f92418: 2, 0x1f9224c: 4, 0x1f9233c: 2}
NOREAD = {0x1f8eb14, 0x1f7e720, 0x1f8dd40, 0x1f8d790, 0x1f9161c, 0x20d888, 0x20c1c0, 0x20c460}
L = json.load(open("hmi_layouts.json"))
helpers = collections.Counter(r[0] for v in L.values() for r in v["reads"])
sizes = {}
for h in helpers:
    if h in PRIM:
        continue
    o = e.v2o(h)
    if o is None:
        continue
    total, ok = 0, True
    for i in md.disasm(e.data[o:o + 0x200], h):
        if i.mnemonic in ("bl", "blx") and i.op_str.startswith("#"):
            t = int(i.op_str[1:], 16)
            if t in PRIM: total += PRIM[t]
            elif t in NOREAD: pass
            else: ok = False; break
        elif i.mnemonic == "blx":
            ok = False; break
        if i.mnemonic.startswith("pop") and "pc" in i.op_str:
            break
        if i.mnemonic == "b" and i.op_str.startswith("#"):
            t = int(i.op_str[1:], 16)
            if t in PRIM: total += PRIM[t]; break
            if t in NOREAD: break
    if ok and total:
        sizes[hex(h)] = total
json.dump(sizes, open("helper_sizes.json", "w"), indent=0)
print(len(sizes), "helpers classified")
