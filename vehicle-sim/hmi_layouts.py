"""Extract MOST property payload layouts from HmiMain3D (006.027.001).

Every CPxy<Group>::<Property> class has the deserializer in vtable slot 6 (word index 8 of the
_ZTV symbol). It calls reader helpers in order; this walks the call sequence (following one level
of small wrappers) and records each helper with the r2/r3 range arguments.
Output: hmi_layouts.json {"Group::Class": {"func": addr, "reads": [[helper, min, max], ...]}}
"""
import json, re, struct, sys, collections
import capstone
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from elfsyms import Elf

BIN = sys.argv[1] if len(sys.argv) > 1 else "HmiMain3D"   # usage: hmi_layouts.py <HmiMain3D from your rootfs>
e = Elf(BIN)
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
SKIP = {0x1f8eb14, 0x1f7e720, 0x1f8dd40, 0x1f8d790}   # init / notify / error paths


def calls(addr, limit=0x800):
    o = e.v2o(addr)
    regs, out = {}, []
    for i in md.disasm(e.data[o:o + limit], addr):
        if i.mnemonic in ("mov", "movw", "mvn") and i.op_str[:3] in ("r2,", "r3,"):
            v = i.op_str.split("#")[-1] if "#" in i.op_str else None
            try:
                regs[i.op_str[:2]] = int(v, 16) if v else None
            except ValueError:
                regs[i.op_str[:2]] = None
            if i.mnemonic == "mvn" and regs[i.op_str[:2]] is not None:
                regs[i.op_str[:2]] = ~regs[i.op_str[:2]] & 0xffffffff
        if i.mnemonic == "bl" and i.op_str.startswith("#"):
            t = int(i.op_str[1:], 16)
            if t not in SKIP:
                out.append([t, regs.get("r2"), regs.get("r3")])
            regs = {}
        if (i.mnemonic.startswith("pop") and "pc" in i.op_str) or (i.mnemonic == "b" and i.op_str.startswith("#") and int(i.op_str[1:], 16) in SKIP and False):
            break
    return out


res = {}
pat = re.compile(r"^_ZTVN(\d+)(CPxy\w+?)(\d+)(\w+)E$")
for sym, (va, size) in e.symbols.items():
    if not sym.startswith("_ZTVN") or "CPxy" not in sym or size < 0x24:
        continue
    m = re.match(r"^_ZTVN(\d+)", sym)
    n = int(m.group(1)); rest = sym[m.end():]
    group = rest[:n]; rest = rest[n:]
    m2 = re.match(r"^(\d+)", rest)
    if not m2:
        continue
    k = int(m2.group(1)); cls = rest[m2.end():m2.end() + k]
    if not group.startswith("CPxy") or rest[m2.end() + k:] != "E":
        continue
    w = struct.unpack_from(f"<{size // 4}I", e.data, e.v2o(va))
    if len(w) < 9:
        continue
    f = w[8]
    res[f"{group[4:]}::{cls}"] = {"func": f, "reads": calls(f)}
hist = collections.Counter(r[0] for v in res.values() for r in v["reads"])
json.dump(res, open("hmi_layouts.json", "w"), indent=0)
print(len(res), "classes")
for h, c in hist.most_common(40):
    print(hex(h), c)
