#!/usr/bin/env python3
"""Port the emulator to another head-unit firmware build (another PSdZData release).

Everything build-specific lives in builds/<id>/ (see builds/README.md). This tool derives a new
build folder from an existing one. It needs only YOUR PSdZData: the reference build ships
"signatures" (masked byte patterns around every patch site and hook address), so the reference
firmware is not required.

  port-build.py new --from hu-006.027.001 --id hu-XXX.YYY.ZZZ --psdzdata /path/psdzdata [--vehicle F30]
        extract your head-unit packages, port every value, pin shaders, write builds/<id>/
        (status "draft") and builds/<id>/PORT-REPORT.md with what was ported and what was not
  port-build.py verify --build ID --rootfs ROOTFS
        check build.json against an extracted/staged rootfs (binary hashes, bytes at every site)
  port-build.py signatures --build ID --rootfs ROOTFS
        (maintainers) write builds/<id>/signatures.json from that build's own binaries

Porting method (all checks are exact; nothing is guessed silently):
  * code sites / functions: ARM instructions around the old site with build-dependent fields
    masked (branch targets, PC-relative literals, movw/movt); must match exactly once
  * vtables: functions of the first slots are found by their patterns, then the table that holds
    them is located
  * libhmicoding pages: the defaults index is found by its structure; page patches keep their
    position relative to the page and the original byte must match
  * shaders: program fingerprints (tools/shader-library.py)
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import buildinfo  # noqa: E402
from buildinfo import hexint  # noqa: E402

TOOLS = Path(__file__).resolve().parent
HMI = "opt/hmi/ID5/bin/HmiMain3D"
CODING = "opt/hmi/ID5/lib/libhmicoding.so"
HMIDB = "opt/hmi/ID5/lib/libhmidb.so"
HMICOM = "opt/hmi/ID5/lib/libhmicom.so"
REGISTRY = "opt/hmi/ID5/data/ro/common/widget/variantregistry.pbvar"
HU_PACKAGES = ("swfl_00002719", "swfl_0000271a", "swfl_00002720")
VTABLE_SLOTS = 16


# ---------------------------------------------------------------- ELF32 (file offset <-> address)
class Elf:
    def __init__(self, data: bytes):
        self.data = data
        if data[:4] != b"\x7fELF" or data[4] != 1:
            raise ValueError("not an ELF32 file")
        phoff, = struct.unpack_from("<I", data, 0x1C)
        phentsize, phnum = struct.unpack_from("<HH", data, 0x2A)
        self.loads = []
        for i in range(phnum):
            p_type, p_offset, p_vaddr, _pa, p_filesz = struct.unpack_from("<IIIII", data, phoff + i * phentsize)
            if p_type == 1:
                self.loads.append((p_vaddr, p_offset, p_filesz))

    def v2o(self, va: int) -> int | None:
        for vaddr, offset, size in self.loads:
            if vaddr <= va < vaddr + size:
                return va - vaddr + offset
        return None

    def o2v(self, off: int) -> int | None:
        for vaddr, offset, size in self.loads:
            if offset <= off < offset + size:
                return off - offset + vaddr
        return None


# ---------------------------------------------------------------- masked instruction patterns
def mask_word(w: int, loose: bool = False) -> int:
    """Mask of the bits of one A32 instruction that do not move between builds.

    loose=True also ignores load/store immediate offsets (stack frames and structures shift
    between builds) and words that look like literal-pool data (condition field EQ, no branch)."""
    if loose:
        if (w >> 28) == 0 and ((w >> 24) & 0x0F) not in (0x0A, 0x0B):
            return 0x00000000
        if (w & 0x0E000000) == 0x04000000:                # LDR/STR/LDRB/STRB immediate
            return 0xFFFFF000
        if (w & 0x0E400090) == 0x00400090:                # LDRH/STRH/LDRD/STRD immediate
            return 0xFFFFF0F0
    if ((w >> 24) & 0x0F) in (0x0A, 0x0B):                 # B / BL
        return 0xFF000000
    if (w & 0xFE000000) == 0xFA000000:                    # BLX imm
        return 0xFE000000
    if (w & 0x0F7F0000) == 0x051F0000:                    # LDR/STR [pc, #imm]
        return 0xFFFFF000
    if (w & 0x0E5F0000) == 0x004F0000 and (w & 0x0E000000) == 0:   # LDRH/LDRD pc-relative
        return 0xFFFFF0F0
    if (w & 0x0FF00000) in (0x03000000, 0x03400000):      # MOVW / MOVT
        return 0xFFF0F000
    if (w & 0x0FEF0000) in (0x028F0000, 0x024F0000):      # ADD/SUB rX, pc, #imm
        return 0xFFFFF000
    return 0xFFFFFFFF


def make_pattern(data: bytes, offset: int, count: int, loose: bool = False) -> tuple[str, str]:
    value, mask = bytearray(), bytearray()
    for i in range(count):
        w, = struct.unpack_from("<I", data, offset + 4 * i)
        m = mask_word(w, loose)
        value += struct.pack("<I", w & m)
        mask += struct.pack("<I", m)
    return value.hex(), mask.hex()


def regex(value_hex: str, mask_hex: str) -> re.Pattern:
    parts = []
    for v, m in zip(bytes.fromhex(value_hex), bytes.fromhex(mask_hex)):
        parts.append(re.escape(bytes([v])) if m == 0xFF else b".")
    return re.compile(b"".join(parts), re.DOTALL)


def matches(data: bytes, value_hex: str, mask_hex: str) -> list[int]:
    return [m.start() for m in regex(value_hex, mask_hex).finditer(data) if m.start() % 4 == 0]


def unique_signature(data: bytes, site: int, backs=(0, 4, 8, 16), counts=(8, 12, 16, 24, 32, 48, 64),
                     loose: bool = False) -> dict:
    """Smallest masked pattern starting `back` instructions before `site` that is unique in data.

    Some sites exist as identical code more than once (e.g. C1/C2 constructors). Then the longest
    pattern is kept with its match count and the site's position among the matches."""
    fallback = None
    for back in backs:
        start = site - 4 * back
        if start < 0:
            continue
        for count in counts:
            if start + 4 * count > len(data):
                break
            value, mask = make_pattern(data, start, count, loose)
            hits = matches(data, value, mask)
            if hits == [start]:
                return {"back": back, "value": value, "mask": mask, **({"loose": True} if loose else {})}
            if start in hits and len(hits) <= 4 and (fallback is None or len(hits) < fallback["count"]
                                                     or count >= len(bytes.fromhex(fallback["value"])) // 4):
                fallback = {"back": back, "value": value, "mask": mask, "count": len(hits),
                            "occurrence": hits.index(start)}
    if fallback:
        return fallback
    raise ValueError(f"no unique pattern for offset {site:#x}")


def find_signature(data: bytes, signature: dict) -> int:
    hits = matches(data, signature["value"], signature["mask"])
    expected = signature.get("count", 1)
    if len(hits) != expected:
        raise LookupError(f"pattern matched {len(hits)} times (expected {expected})")
    return hits[signature.get("occurrence", 0)] + 4 * signature["back"]


SITE_BACKS = (0, -2, -4, -8, 2, 4, 6, 8, 12, 16, 20)


def signature_set(data: bytes, site: int, backs=SITE_BACKS, limit: int = 6) -> list[dict]:
    """Several independent patterns (different anchors, strict and loose) for one site.
    At port time every pattern that matches must point at the same place."""
    found, seen = [], set()
    for loose in (False, True):
        taken = 0
        for back in backs:
            try:
                sig = unique_signature(data, site, backs=(back,), loose=loose)
            except ValueError:
                continue
            key = (sig["back"], sig["value"], sig["mask"])
            if key not in seen:
                seen.add(key)
                found.append(sig)
                taken += 1
            if taken >= limit:
                break
    if not found:
        raise ValueError(f"no pattern for offset {site:#x}")
    return found


def find_site(data: bytes, signatures: list[dict]) -> tuple[int, str]:
    results = {}
    for sig in signatures:
        try:
            results.setdefault(find_signature(data, sig), []).append(sig["back"])
        except LookupError:
            continue
    if not results:
        raise LookupError(f"none of {len(signatures)} patterns matched")
    if len(results) > 1:
        raise LookupError(f"patterns disagree: {', '.join(f'{k:#x}' for k in results)}")
    site, backs = next(iter(results.items()))
    return site, f"{len(backs)}/{len(signatures)} patterns agree"


def bl_target(elf: Elf, data: bytes, off: int) -> int | None:
    w, = struct.unpack_from("<I", data, off)
    if (w & 0x0F000000) != 0x0B000000 or (w >> 28) == 0xF:
        return None
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    return elf.o2v(off) + 8 + imm * 4


def call_sites(elf: Elf, data: bytes, target_va: int, limit: int = 24) -> list[int]:
    text_end = elf.loads[0][1] + elf.loads[0][2]
    sites = []
    for off in range(0, text_end, 4):
        if bl_target(elf, data, off) == target_va:
            sites.append(off)
            if len(sites) >= limit:
                break
    return sites


def function_signatures(elf: Elf, data: bytes, va: int) -> dict:
    """Patterns of a function's entry and of up to 8 BL call sites that call it."""
    entry = []
    try:
        entry = signature_set(data, elf.v2o(va), backs=(0, -2, -4, -8))
    except ValueError:
        pass
    calls = []
    for site in call_sites(elf, data, va):
        try:
            calls.append(unique_signature(data, site, backs=(4, 8, 12)))
        except ValueError:
            continue
        if len(calls) >= 8:
            break
    return {"entry": entry, "calls": calls}


def find_function(elf: Elf, data: bytes, sig: dict) -> tuple[int, str]:
    if sig["entry"]:
        try:
            site, how = find_site(data, sig["entry"])
            return elf.o2v(site), f"entry: {how}"
        except LookupError:
            pass
    votes = {}
    for call in sig["calls"]:
        try:
            target = bl_target(elf, data, find_signature(data, call))
        except LookupError:
            continue
        if target is not None:
            votes[target] = votes.get(target, 0) + 1
    if not votes:
        raise LookupError("entry and call-site patterns did not match")
    best = max(votes, key=votes.get)
    if list(votes.values()).count(votes[best]) > 1:
        raise LookupError(f"call sites disagree: {votes}")
    return best, f"call sites vote {votes[best]}/{sum(votes.values())}"


# ---------------------------------------------------------------- libhmicoding defaults index
def find_defaults_index(data: bytes, keys: int = 17) -> int:
    """The BMW defaults index: entries (key, packed size, data offset) for keys 1..N in order."""
    candidates = []
    for start in range(0, len(data) - keys * 12, 4):
        ok = True
        for k in range(keys):
            key, packed, offset = struct.unpack_from("<III", data, start + 12 * k)
            # data offsets may point past the file into the data segment
            if key != k + 1 or not 0 < (packed & 0xFFFF) <= 0x400 or not 0 < offset < 0x10000000:
                ok = False
                break
        if ok:
            candidates.append(start)
    if len(candidates) != 1:
        raise LookupError(f"defaults index found {len(candidates)} times")
    return candidates[0]


def page_of(build: dict, offset: int) -> tuple[int, int]:
    """(defaults key, offset inside the page) of an absolute libhmicoding offset in a build."""
    pages = {int(k): (hexint(v[0]), hexint(v[1])) for k, v in build["coding"]["expected_pages"].items()}
    camera = build["coding"]["camera_rvc"]
    pages.setdefault(camera["page_key"], (0x96, hexint(camera["page_data"])))
    for key, (size, start) in pages.items():
        if start <= offset < start + size:
            return key, offset - start
    raise LookupError(f"offset {offset:#x} is in no known coding page")


# ---------------------------------------------------------------- signatures (reference build)
def cmd_signatures(args) -> None:
    build = buildinfo.get(args.build)
    root = args.rootfs
    hmi = (root / HMI).read_bytes()
    elf = Elf(hmi)
    c = build["controller"]
    sig = {"schema": "bimmulator-build-signatures-v1", "build": build.id, "HmiMain3D": {}, "libhmicoding": {},
           "libhmidb": {}}
    for name in ("allocate_event", "get_display_service_cache", "enable_display"):
        sig["HmiMain3D"][name] = function_signatures(elf, hmi, hexint(c[name]))
    sig["HmiMain3D"]["pop_callers"] = [signature_set(hmi, elf.v2o(hexint(v)), backs=(2, 4, 6, 8, 10, 12, 16, 20, -1, -2))
                                       for v in c["pop_callers"]]
    for name in ("app_vtable", "event_vtable", "display_service_vtable"):
        table = elf.v2o(hexint(c[name]))
        slots = []
        for i in range(VTABLE_SLOTS):
            fp, = struct.unpack_from("<I", hmi, table + 4 * i)
            off = elf.v2o(fp & ~1)
            if off is None or off >= elf.loads[0][1] + elf.loads[0][2]:
                continue
            try:
                slots.append({"slot": i, "thumb": fp & 1, "patterns": signature_set(hmi, off, backs=(0, -2, -4))})
            except ValueError:
                continue
        sig["HmiMain3D"][name] = slots
    sig["HmiMain3D"]["bench_input_patches"] = [signature_set(hmi, hexint(p[0])) for p in build["bench_input_patches"]]
    coding = (root / CODING).read_bytes()
    sig["libhmicoding"]["code_patches"] = [signature_set(coding, hexint(p[0])) for p in build["coding"]["code_patches"]]
    hmidb = (root / HMIDB).read_bytes()
    sig["libhmidb"]["language_sites"] = [signature_set(hmidb, hexint(s)) for s in build["resource_language_sites"]]
    out = build.dir / "signatures.json"
    out.write_text(json.dumps(sig, indent=1) + "\n")
    print(f"{out}: written")


# ---------------------------------------------------------------- port
def port_values(ref, sig: dict, root: Path, report: list[str]) -> dict:
    """All build.json values that depend on binaries, ported from ref via signatures."""
    out: dict = {}
    hmi = (root / HMI).read_bytes()
    elf = Elf(hmi)

    def note(ok: bool, what: str, how: str) -> None:
        report.append(f"| {'ok' if ok else '**FAILED**'} | {what} | {how} |")

    # controller hook: functions, pop call sites, vtables
    ctrl = {}
    for name in ("allocate_event", "get_display_service_cache", "enable_display"):
        try:
            va, how = find_function(elf, hmi, sig["HmiMain3D"][name])
            ctrl[name] = f"{va:#010x}"
            note(True, f"controller.{name}", f"{ref['controller'][name]} -> {ctrl[name]} ({how})")
        except LookupError as error:
            ctrl[name] = None
            note(False, f"controller.{name}", str(error))
    pops = []
    for i, s in enumerate(sig["HmiMain3D"]["pop_callers"]):
        try:
            site, how = find_site(hmi, s)
            pops.append(f"{elf.o2v(site):#010x}")
            note(True, f"controller.pop_callers[{i}]", f"{ref['controller']['pop_callers'][i]} -> {pops[-1]} ({how})")
        except LookupError as error:
            pops.append(None)
            note(False, f"controller.pop_callers[{i}]", str(error))
    ctrl["pop_callers"] = pops
    for name in ("app_vtable", "event_vtable", "display_service_vtable"):
        known = []
        for slot in sig["HmiMain3D"][name]:
            try:
                known.append((slot["slot"], elf.o2v(find_site(hmi, slot["patterns"])[0]) | slot["thumb"]))
            except LookupError:
                continue
        best = None
        if len(known) >= 3:
            first_slot, first_fp = known[0]
            scores = []
            for m in re.finditer(re.escape(struct.pack("<I", first_fp)), hmi):
                if m.start() % 4:
                    continue
                base = m.start() - 4 * first_slot
                score = sum(1 for i, fp in known if struct.unpack_from("<I", hmi, base + 4 * i)[0] == fp)
                scores.append((score, base))
            scores.sort(reverse=True)
            if scores and scores[0][0] >= len(known) - 1 and (len(scores) == 1 or scores[1][0] < scores[0][0]):
                best = elf.o2v(scores[0][1])
        ctrl[name] = f"{best:#010x}" if best else None
        note(best is not None, f"controller.{name}",
             f"{ref['controller'][name]} -> {ctrl[name]} ({len(known)}/{len(sig['HmiMain3D'][name])} slot functions found)")
    if ctrl.get("app_vtable"):
        slot7, = struct.unpack_from("<I", hmi, elf.v2o(hexint(ctrl["app_vtable"])) + 0x1C)
        ctrl["interaction_slot_function"] = f"{slot7:#010x}"
        note(True, "controller.interaction_slot_function", f"app vtable slot 7 -> {ctrl['interaction_slot_function']}")
    else:
        ctrl["interaction_slot_function"] = None
        note(False, "controller.interaction_slot_function", "needs app_vtable")
    out["controller"] = ctrl

    # HmiMain3D bench input patches (file offsets)
    bench = []
    for i, (old, s) in enumerate(zip(ref["bench_input_patches"], sig["HmiMain3D"]["bench_input_patches"])):
        _, expected, replacement = old
        try:
            site, _how = find_site(hmi, s)
            ok = hmi[site:site + len(bytes.fromhex(expected))] == bytes.fromhex(expected)
            bench.append([f"{site:#X}".replace("0X", "0x"), expected, replacement])
            note(ok, f"bench_input_patches[{i}]", f"{old[0]} -> {site:#x}" + ("" if ok else " (original bytes differ!)"))
        except LookupError as error:
            bench.append([None, expected, replacement])
            note(False, f"bench_input_patches[{i}]", str(error))
    out["bench_input_patches"] = bench

    # libhmidb language sites
    hmidb = (root / HMIDB).read_bytes()
    sites = []
    for i, s in enumerate(sig["libhmidb"]["language_sites"]):
        try:
            site, _how = find_site(hmidb, s)
            ok = hmidb[site:site + 4] == bytes.fromhex("00 00 e0 e3")
            sites.append(f"{site:#X}".replace("0X", "0x"))
            note(ok, f"resource_language_sites[{i}]", f"{ref['resource_language_sites'][i]} -> {site:#x}"
                 + ("" if ok else " (not `mvn r0, #0`!)"))
        except LookupError as error:
            sites.append(None)
            note(False, f"resource_language_sites[{i}]", str(error))
    out["resource_language_sites"] = sites

    # libhmicoding: defaults index, pages, code patches, page-relative patches
    coding = (root / CODING).read_bytes()
    rc = ref["coding"]
    new_coding: dict = {}
    try:
        index = find_defaults_index(coding)
        new_coding["defaults_index"] = f"{index:#X}".replace("0X", "0x")
        note(True, "coding.defaults_index", f"{rc['defaults_index']} -> {new_coding['defaults_index']} (structure)")
    except LookupError as error:
        note(False, "coding.defaults_index", str(error))
        index = None
    pages = {}
    if index is not None:
        for key in sorted({int(k) for k in rc["expected_pages"]} | {rc["camera_rvc"]["page_key"]}):
            _k, packed, start = struct.unpack_from("<III", coding, index + (key - 1) * 12)
            pages[key] = (packed & 0xFFFF, start)
        new_coding["expected_pages"] = {}
        for key, (size, start) in rc["expected_pages"].items():
            nsize, nstart = pages[int(key)]
            ok = nsize == hexint(size)
            new_coding["expected_pages"][key] = [f"{nsize:#x}", f"{nstart:#X}".replace("0X", "0x")]
            note(ok, f"coding page {key}", f"size {nsize:#x} at {nstart:#x}" + ("" if ok else f" (reference size {size}!)"))

    def port_page_patch(old, label):
        offset, expected, replacement = old
        key, rel = page_of(ref, hexint(offset))
        if key not in pages:
            note(False, label, "page not found")
            return [None, expected, replacement]
        site = pages[key][1] + rel
        ok = coding[site:site + len(bytes.fromhex(expected))] == bytes.fromhex(expected)
        note(ok, label, f"{offset} -> {site:#x} (page {key} + {rel:#x})" + ("" if ok else
             f" (original byte {coding[site:site + 1].hex()} != {expected}; coding default differs)"))
        return [f"{site:#X}".replace("0X", "0x"), expected, replacement]

    code = []
    for i, (old, s) in enumerate(zip(rc["code_patches"], sig["libhmicoding"]["code_patches"])):
        try:
            site, _how = find_site(coding, s)
            ok = coding[site:site + len(bytes.fromhex(old[1]))] == bytes.fromhex(old[1])
            code.append([f"{site:#X}".replace("0X", "0x"), old[1], old[2]])
            note(ok, f"coding.code_patches[{i}]", f"{old[0]} -> {site:#x}")
        except LookupError as error:
            code.append([None, old[1], old[2]])
            note(False, f"coding.code_patches[{i}]", str(error))
    new_coding["code_patches"] = code
    if pages:
        new_coding["id6l_patches"] = [port_page_patch(p, f"coding.id6l_patches[{i}]") for i, p in enumerate(rc["id6l_patches"])]
        new_coding["developer_menu_patch"] = port_page_patch(rc["developer_menu_patch"], "coding.developer_menu_patch")
        new_coding["cid_1440_patch"] = port_page_patch(rc["cid_1440_patch"], "coding.cid_1440_patch")
        new_coding["cid_touch_patches"] = [port_page_patch(p, f"coding.cid_touch_patches[{i}]") for i, p in enumerate(rc["cid_touch_patches"])]
        cam_key = rc["camera_rvc"]["page_key"]
        new_coding["camera_rvc"] = {"page_key": cam_key,
                                    "page_data": f"{pages[cam_key][1]:#X}".replace("0X", "0x"),
                                    "patch": port_page_patch(rc["camera_rvc"]["patch"], "coding.camera_rvc.patch")}
    out["coding"] = new_coding
    return out


def find_packages(psdzdata: Path, version: str | None) -> dict[str, Path]:
    root = psdzdata / "swe/swfl"
    versions = {}
    for path in root.glob("swfl_00002719.bin.*"):
        versions[path.name.split(".bin.")[1]] = path
    if not versions:
        raise SystemExit(f"no head-unit package swfl_00002719.bin.* in {root}")
    if version is None:
        if len(versions) > 1:
            raise SystemExit(f"several head-unit versions in {root}: {', '.join(sorted(versions))}; pass --version")
        version = next(iter(versions))
    packages = {f"{p}.bin.{version}": root / f"{p}.bin.{version}" for p in HU_PACKAGES}
    missing = [str(p) for p in packages.values() if not p.is_file()]
    if missing:
        raise SystemExit("missing packages: " + ", ".join(missing))
    return packages


def load_shader_library():
    spec = importlib.util.spec_from_file_location("shader_library", TOOLS / "shader-library.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cmd_new(args) -> None:
    ref = buildinfo.get(args.from_build)
    sig_path = ref.dir / "signatures.json"
    if not sig_path.is_file():
        raise SystemExit(f"{ref.id} has no signatures.json; port from a build that has one")
    sig = json.loads(sig_path.read_text())
    target = buildinfo.BUILDS / args.id
    if (target / "build.json").exists() and not args.force:
        raise SystemExit(f"{target} exists (use --force to overwrite)")
    packages = find_packages(args.psdzdata, args.version)
    version = next(iter(packages)).split(".bin.")[1]
    work = Path(args.work) if args.work else Path(tempfile.mkdtemp(prefix=f"port-{args.id}-"))
    extraction = work / "firmware"
    if not (extraction / "extraction.json").is_file():
        shutil.rmtree(extraction, ignore_errors=True)
        subprocess.run([sys.executable, str(TOOLS / "extract-psdz-swfl.py"), *map(str, packages.values()),
                        "--output", str(extraction)], check=True)
    root = extraction / "rootfs"
    inventory = json.loads((extraction / "extraction.json").read_text())["files"]

    report = [f"# Port report: {args.id} (from {ref.id})", "",
              f"Packages: {', '.join(packages)}", "", "| result | value | how |", "|---|---|---|"]
    vehicle = args.vehicle or ref["vehicle"]
    build = {
        "schema": buildinfo.SCHEMA, "id": args.id,
        "title": f"NBT EVO HU {version.replace('_', '.')} (ported from {ref.id}) - fill in HMI version / PSdZData / I-level",
        "status": "draft", "verified": "", "maintainer": "", "derived_from": ref.id,
        "psdzdata": None, "i_level": None, "hmi_version": None,
        "packages": {name: buildinfo.sha256_file(path) for name, path in packages.items()},
        "asset_package": f"swfl_00002720.bin.{version}",
        "release": f"{args.id}-v1", "vehicle": vehicle, "theme": ref["theme"],
        "default_profile": ref["default_profile"],
        "binaries": {name: buildinfo.sha256_file(root / name) for name in (HMI, HMICOM, CODING, HMIDB, REGISTRY)},
    }
    values = port_values(ref, sig, root, report)
    build["coding"] = values["coding"]
    build["variantregistry_paths"] = [[old, f"vehicles/{vehicle}/" + new.split("/", 2)[2].replace(ref["vehicle"], vehicle)]
                                      for old, new in ref["variantregistry_paths"]]
    build["bench_input_patches"] = values["bench_input_patches"]
    build["resource_language_sites"] = values["resource_language_sites"]
    build["controller"] = values["controller"]
    domains = {}
    for relative in ref["assetdb_domains"]:
        record = inventory.get(f"rootfs/opt/hmi/ID5/data/ro/{relative}/widget.pbw")
        domains[relative] = record["sha256"] if record else None
        report.append(f"| {'ok' if record else '**FAILED**'} | assetdb {relative.rsplit('/', 1)[-1]} | "
                      f"{'widget.pbw found' if record else 'domain missing in this firmware'} |")
    build["assetdb_domains"] = domains

    target.mkdir(parents=True, exist_ok=True)
    (target / "profiles").mkdir(exist_ok=True)
    for profile in (ref.dir / "profiles").glob("*.json"):
        data = json.loads(profile.read_text())
        text = json.dumps(data).replace(ref["release"], build["release"])
        data = json.loads(text)
        data["name"] = f"{args.id}-{profile.stem}"
        data["purpose"] = f"{profile.stem} profile ported from {ref.id}; check settings for this build."
        data["paths"]["IDRIVE_ROOT_ARCHIVE_OUTPUT"] = f"{{cache_dir}}/idrive-rootfs-{args.id}-{profile.stem}.tar.gz"
        (target / "profiles" / profile.name).write_text(json.dumps(data, indent=2) + "\n")
    (target / "build.json").write_text(json.dumps(build, indent=2) + "\n")

    library = load_shader_library()
    pins, shader_report = library.compute_pins(root / "opt/hmi/ID5/data/ro")
    library.save_pins(buildinfo.get(args.id), pins)
    report += ["", "## Shaders", "",
               f"* pinned (same program as a library entry): {sum(len(v) for v in pins.values())}",
               f"* asset not present in this firmware: {len(shader_report['asset_missing'])}",
               f"* program changed (needs a new reconstruction, see builds/README.md): {len(shader_report['program_changed'])}"]
    report += [f"  * `{item}`" for item in shader_report["program_changed"]]
    failed = sum(1 for line in report if "**FAILED**" in line or "differ" in line)
    report += ["", f"**{failed} item(s) need manual work.**" if failed else "**All values ported.**",
               "", f"Extraction kept in `{work}` (re-use with --work)."]
    (target / "PORT-REPORT.md").write_text("\n".join(report) + "\n")
    print("\n".join(report))
    print(f"\nWrote {target}/ (status draft). Next: wsl/emulator.sh prepare, then snapshot.")


def cmd_verify(args) -> None:
    build = buildinfo.get(args.build)
    root = args.rootfs
    problems = []
    for name, digest in build["binaries"].items():
        if buildinfo.sha256_file(root / name) != digest:
            problems.append(f"hash {name}")
    data = {CODING: (root / CODING).read_bytes(), HMI: (root / HMI).read_bytes(), HMIDB: (root / HMIDB).read_bytes()}
    c = build["coding"]
    if "defaults_index" not in c or "id6l_patches" not in c:
        print(f"{build.id}: PROBLEMS:\n  coding values were not ported (see PORT-REPORT.md)")
        sys.exit(1)
    checks = [(CODING, p) for p in c["code_patches"] + c["id6l_patches"] + c["cid_touch_patches"]
              + [c["developer_menu_patch"], c["cid_1440_patch"], c["camera_rvc"]["patch"]]]
    checks += [(HMI, p) for p in build["bench_input_patches"]]
    checks += [(HMIDB, [s, "00 00 e0 e3", "02 00 a0 e3"]) for s in build["resource_language_sites"]]
    for name, patch in checks:
        if None in patch:
            problems.append(f"unported site in {name}")
            continue
        offset, expected, _ = buildinfo.patch_triple(patch)
        if data[name][offset:offset + len(expected)] != expected:
            problems.append(f"{name} {offset:#x}: {data[name][offset:offset + len(expected)].hex()} != {expected.hex()}")
    index = hexint(c["defaults_index"])
    for key, (size, start) in c["expected_pages"].items():
        k, packed, offset = struct.unpack_from("<III", data[CODING], index + (int(key) - 1) * 12)
        if (k, packed & 0xFFFF, offset) != (int(key), hexint(size), hexint(start)):
            problems.append(f"coding page {key}")
    elf = Elf(data[HMI])
    ctrl = build["controller"]
    for name in ("allocate_event", "get_display_service_cache", "enable_display", "app_vtable", "event_vtable",
                 "display_service_vtable", "interaction_slot_function", *[f"pop{i}" for i in range(3)]):
        value = ctrl["pop_callers"][int(name[3])] if name.startswith("pop") else ctrl[name]
        if value is None or elf.v2o(hexint(value)) is None:
            problems.append(f"controller.{name} not inside HmiMain3D")
    if ctrl["app_vtable"]:
        slot7, = struct.unpack_from("<I", data[HMI], elf.v2o(hexint(ctrl["app_vtable"])) + 0x1C)
        if slot7 != hexint(ctrl["interaction_slot_function"]):
            problems.append("app vtable slot 7 != interaction_slot_function")
    print(f"{build.id}: " + ("OK - all hashes and patch sites match" if not problems else "PROBLEMS:\n  " + "\n  ".join(problems)))
    sys.exit(1 if problems else 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("new")
    p.add_argument("--from", dest="from_build", default=buildinfo.DEFAULT_BUILD)
    p.add_argument("--id", required=True, help="new build id, e.g. hu-006.030.002")
    p.add_argument("--psdzdata", type=Path, required=True)
    p.add_argument("--version", help="package version suffix if several are present, e.g. 006_030_002")
    p.add_argument("--vehicle", help="3D vehicle body staged for this build (default: the reference's)")
    p.add_argument("--work", help="keep/re-use the extraction in this folder")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_new)
    p = sub.add_parser("verify"); p.add_argument("--build", required=True); p.add_argument("--rootfs", type=Path, required=True)
    p.set_defaults(func=cmd_verify)
    p = sub.add_parser("signatures"); p.add_argument("--build", required=True); p.add_argument("--rootfs", type=Path, required=True)
    p.set_defaults(func=cmd_signatures)
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
