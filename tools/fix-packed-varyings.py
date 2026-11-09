#!/usr/bin/env python3
"""Rewrite reconstructed HMI vertex shaders to read SGX-packed varying outputs.

make-hmi-essl-from-usse.py assumed every varying owns its own output register
(register = 1 + scalar base / 4). The finalized USSE code proves the SGX
compiler packs varyings back to back in symbol-base order, starting at o1.x:

  vec4 -> 4 components, vec3 -> 3, vec2 -> 2, float -> 2 (one padding lane).

Evidence (car 006.027.001 rootfs): CursorBG/mat_bg.vert writes fd to o1.xyz and
uv to o1.w/o2.x; Cursor/mat_frame4.vert writes its two scalars to o3.x/o3.z;
panel/mat_list_mirrored.vert writes am_inner_stack/am_outer_stack/px to
o1.z/o2.x/o2.z. With the old mapping those shaders fed zeros or the wrong lanes
into the fragment stage, so cursor, panel and list materials drew nothing.

Usage: fix-packed-varyings.py MAP.json [MAP.json ...]
Rewrites each mapped vertex source in place (idempotent) and refreshes the
source_essl_sha256 of every map entry that points at a rewritten file.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIDTH = {"float": 1, "vec2": 2, "vec3": 3, "vec4": 4}
LANES = {"float": 2, "vec2": 2, "vec3": 3, "vec4": 4}
ASSIGN = re.compile(r"^(\s*)(\w+) = _output\[(\d+)\](?:\.([xyzw]+))?;\s*$", re.M)
PACKED_MARK = "// Varyings read with SGX packing (tools/fix-packed-varyings.py)."


def lane(offset: int) -> str:
    return f"_output[{offset // 4}].{'xyzw'[offset % 4]}"


def rewrite(source: str) -> str:
    if PACKED_MARK in source:
        return source
    main = source.rfind("void main()")
    if main < 0:
        return source
    head, tail = source[:main], source[main:]
    outs = {name: type_name for type_name, name in
            re.findall(r"^out (?:highp |mediump |lowp )?(float|vec[234]) (\w+);", head, re.M)}
    rows = [m for m in ASSIGN.finditer(tail) if m.group(2) in outs]
    if not rows:
        return source
    rows.sort(key=lambda m: int(m.group(3)))
    offset = 4
    replacements = {}
    for m in rows:
        type_name = outs[m.group(2)]
        lanes = [lane(offset + i) for i in range(WIDTH[type_name])]
        value = lanes[0] if type_name == "float" else f"{type_name}({', '.join(lanes)})"
        replacements[m.group(0)] = f"{m.group(1)}{m.group(2)} = {value};"
        offset += LANES[type_name]
    for old, new in replacements.items():
        tail = tail.replace(old, new, 1)
    return head + PACKED_MARK + "\n" + tail


def essl_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> int:
    maps = [Path(arg) for arg in sys.argv[1:]]
    if not maps:
        print(__doc__, file=sys.stderr)
        return 2
    changed = set()
    for map_path in maps:
        data = json.loads(map_path.read_text(encoding="utf-8"))
        for entry in data["mappings"]:
            source_path = ROOT / entry["source_path"]
            text = source_path.read_text(encoding="utf-8").replace("\r\n", "\n")
            fixed = rewrite(text)
            if fixed != text:
                source_path.write_text(fixed, encoding="utf-8", newline="\n")
                changed.add(entry["source_path"])
                print(f"packed: {entry['asset_path']}")
    for map_path in maps:
        data = json.loads(map_path.read_text(encoding="utf-8"))
        touched = 0
        for entry in data["mappings"]:
            sha = essl_sha(ROOT / entry["source_path"])
            if entry.get("source_essl_sha256") != sha:
                entry["source_essl_sha256"] = sha
                touched += 1
        if touched:
            map_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"{map_path.name}: {touched} hashes refreshed")
    print(f"{len(changed)} vertex sources rewritten")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
