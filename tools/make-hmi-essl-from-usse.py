#!/usr/bin/env python3
"""Adapt translated BMW vertex-register code to one exact IMG .shd interface.

The SPIR-V module is emitted by idrive-usse-graphics in native-register mode,
then converted to ESSL 300 by the pinned SPIRV-Cross tool. This script applies
the names, types, constant-copy table and register slots recovered from the
matching BMW .shd and QNX IMG finalizer output. It does not accept arbitrary
shader binaries or guess missing instructions.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path
import re
import struct
import sys


TYPE_NAMES = {
    2: "float",
    3: "vec2",
    4: "vec3",
    5: "vec4",
    0x16: "mat4",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_shader_parser():
    path = Path(__file__).with_name("inspect-sgx-shader.py")
    spec = importlib.util.spec_from_file_location("idrive_inspect_sgx_shader", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load .shd parser: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def glsl_scalar(name: str, type_code: int, index: int) -> str:
    if type_code == 2:
        return name
    if type_code in (3, 4, 5):
        return f"{name}.{('xyzw'[index])}"
    if type_code == 0x16:
        return f"{name}[{index // 4}][{index % 4}]"
    raise ValueError(f"unsupported uniform type code 0x{type_code:x}")


def attr_value(name: str, type_code: int) -> str:
    if type_code == 2:
        return f"vec4({name}, 0.0, 0.0, 1.0)"
    if type_code == 3:
        return f"vec4({name}, 0.0, 1.0)"
    if type_code == 4:
        return f"vec4({name}, 1.0)"
    if type_code == 5:
        return name
    raise ValueError(f"unsupported attribute type code 0x{type_code:x}")


def output_value(name: str, register: int, type_code: int) -> str:
    if type_code == 2:
        return f"_output[{register}].x"
    if type_code == 3:
        return f"_output[{register}].xy"
    if type_code == 4:
        return f"_output[{register}].xyz"
    if type_code == 5:
        return f"_output[{register}]"
    raise ValueError(f"unsupported varying type code 0x{type_code:x} for {name}")


def adapt(shader_path: Path, candidate_path: Path, table_path: Path) -> tuple[str, dict]:
    shader = load_shader_parser().parse_shader(shader_path)
    if shader["stage"] != "vertex":
        raise ValueError("the native-register ESSL adapter currently supports vertex shaders")
    source = candidate_path.read_text(encoding="utf-8")
    if "BMWSecondaryAttributes" not in source or "primary_program();" not in source:
        raise ValueError("candidate source is not the expected native-register SPIRV-Cross output")

    symbols = []
    for row in shader["symbols"]:
        metadata = bytes.fromhex(row["metadata_hex"])
        symbols.append({
            "name": row["name"],
            "type": metadata[2],
            "class": metadata[3],
            "base": metadata[12],
            "count": metadata[13],
        })

    attributes: dict[int, dict] = {}
    uniforms = []
    varyings: dict[int, dict] = {}
    inactive_varyings = []
    for symbol in symbols:
        type_code = symbol["type"]
        if symbol["class"] == 4:
            register = symbol["base"] // 4
            if register >= 16:
                raise ValueError(f"attribute register {register} exceeds candidate interface: {symbol['name']}")
            if register in attributes:
                raise ValueError(f"multiple native attributes use PA{register}")
            if type_code not in TYPE_NAMES or type_code == 0x16:
                raise ValueError(f"unsupported native attribute type 0x{type_code:x}: {symbol['name']}")
            attributes[register] = {**symbol, "register": register}
        elif symbol["class"] == 3:
            if type_code not in TYPE_NAMES:
                raise ValueError(f"unsupported native uniform type 0x{type_code:x}: {symbol['name']}")
            uniforms.append(symbol)
        elif symbol["class"] == 5 and symbol["name"] != "gl_Position":
            # A few BMW symbol tables keep zero-count output aliases whose
            # base overlaps a live varying (mat_list_bg.vert.shd has p_bnd
            # at p_fd's base). Preserve them in metadata, but do not emit a
            # second ESSL output for an unallocated native symbol.
            if symbol["count"] == 0:
                inactive_varyings.append({
                    **symbol,
                    "reason": "zero-count native varying symbol",
                })
                continue
            register = 1 + symbol["base"] // 4
            if register >= 16:
                raise ValueError(f"varying register {register} exceeds candidate interface: {symbol['name']}")
            if register in varyings:
                raise ValueError(f"multiple native varyings use output register {register}")
            varyings[register] = {**symbol, "register": register}

    # Rewrite the candidate input declarations to exact native symbols. Inputs
    # absent from the .shd interface become constants and therefore cannot
    # appear as accidental active HMI attributes.
    for register in range(16):
        declaration = re.compile(
            rf"^\s*layout\s*\(location\s*=\s*{register}\)\s+in\s+vec4\s+attribute_register_{register};\s*$",
            re.M,
        )
        symbol = attributes.get(register)
        if symbol is None:
            source, count = declaration.subn(
                f"const vec4 attribute_register_{register} = vec4(0.0);", source)
            if count != 1:
                raise ValueError(f"expected one candidate declaration for PA{register}, found {count}")
            continue
        name = symbol["name"]
        type_name = TYPE_NAMES[symbol["type"]]
        replacement = f"in {type_name} {name};"
        source, count = declaration.subn(replacement, source)
        if count != 1:
            raise ValueError(f"expected one candidate declaration for PA{register}, found {count}")
        source, count = re.subn(
            rf"pa\[{register}\]\s*=\s*attribute_register_{register};",
            f"pa[{register}] = {attr_value(name, symbol['type'])};", source)
        if count != 1:
            raise ValueError(f"expected one candidate assignment for PA{register}, found {count}")

    # Populate source constants from the .shd's literal table, then let dynamic
    # uniform declarations override their native scalar ranges.
    constant_data = bytes.fromhex(shader["constant_data_hex"])
    if len(constant_data) != shader["constant_count"] * 4:
        raise ValueError(".shd constant data length disagrees with its count")
    source_constants = {
        index: f"uintBitsToFloat(0x{int.from_bytes(constant_data[index * 4:index * 4 + 4], 'big'):08x}u)"
        for index in range(shader["constant_count"])
    }
    uniform_declarations = []
    for symbol in uniforms:
        type_name = TYPE_NAMES[symbol["type"]]
        uniform_declarations.append(f"uniform {type_name} {symbol['name']};")
        component_count = 16 if symbol["type"] == 0x16 else symbol["count"]
        for index in range(component_count):
            source_constants[symbol["base"] + index] = glsl_scalar(
                symbol["name"], symbol["type"], index)

    table = table_path.read_bytes()
    if len(table) % 20:
        raise ValueError("native constant-copy table is not a whole number of 20-byte records")
    constant_copies = []
    unmapped_sources = []
    for offset in range(0, len(table), 20):
        source_index, _reserved, destination, _reserved2, flags = struct.unpack_from("<5I", table, offset)
        if source_index >= 128 or destination >= 128:
            continue
        expression = source_constants.get(source_index)
        if expression is None:
            unmapped_sources.append(source_index)
            continue
        component = "xyzw"[destination % 4]
        constant_copies.append(
            f"    sa[{destination // 4}].{component} = {expression};")

    # Convert the interface and output bank to the exact names/types carried in
    # the source .shd. Varying output register = 1 + scalar base / 4, as seen
    # in the Rectangle and HMI startup shader register evidence.
    for register in range(1, 16):
        declaration = re.compile(
            rf"^\s*(?:layout\s*\(location\s*=\s*{register - 1}\)\s+)?"
            rf"out\s+vec4\s+output_register_{register};\s*$",
            re.M,
        )
        symbol = varyings.get(register)
        if symbol is None:
            source, count = declaration.subn("", source)
            if count != 1:
                raise ValueError(f"expected one candidate varying output register {register}, found {count}")
            source, count = re.subn(
                rf"^\s*output_register_{register}\s*=\s*_output\[{register}\];\s*$",
                "", source, flags=re.M)
            if count != 1:
                raise ValueError(f"expected one output assignment for register {register}, found {count}")
            continue
        type_name = TYPE_NAMES.get(symbol["type"])
        if not type_name:
            raise ValueError(f"unsupported varying type 0x{symbol['type']:x}: {symbol['name']}")
        source, count = declaration.subn(
            f"out {type_name} {symbol['name']};", source)
        if count != 1:
            raise ValueError(f"expected one candidate varying output register {register}, found {count}")
        source, count = re.subn(
            rf"^\s*output_register_{register}\s*=\s*_output\[{register}\];\s*$",
            f"    {symbol['name']} = {output_value(symbol['name'], register, symbol['type'])};",
            source, flags=re.M)
        if count != 1:
            raise ValueError(f"expected one output assignment for register {register}, found {count}")

    # The UBO is only a candidate harness interface. Runtime uniforms are
    # represented by the names and types from the BMW symbol records instead.
    source, block_count = re.subn(
        r"layout\s*\(std140\)\s*uniform\s+BMWSecondaryAttributes\s*\{\s*"
        r"vec4\s+_m0\[32\];\s*\}\s*secondary_attributes\s*;\s*",
        "", source, count=1)
    if block_count != 1:
        raise ValueError("expected one candidate secondary-attribute block")
    source, loads = re.subn(
        r"^\s*sa\[\d+\]\s*=\s*secondary_attributes\._m0\[\d+\];\s*$",
        "", source, flags=re.M)
    if loads != 32:
        raise ValueError(f"expected 32 candidate SA loads, found {loads}")
    call_target = "secondary_program" if re.search(
        r"^\s*secondary_program\(\);\s*$", source, re.M) else "primary_program"
    constant_insertion = (
        "\\1// Native uniform/constants copied through the IMG table.\n"
        + "\n".join(constant_copies)
        + f"\n\\1{call_target}();"
    )
    source, inserted = re.subn(
        rf"^(\s*){call_target}\(\);$",
        constant_insertion,
        source, count=1, flags=re.M)
    if inserted != 1:
        raise ValueError(f"could not locate the candidate {call_target}-program call")

    version_end = source.find("\n")
    source = source[:version_end + 1] + "\n".join(uniform_declarations) + "\n" + source[version_end + 1:]
    provenance = (
        "// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.\n"
        f"// .shd sha256: {sha256(shader_path.read_bytes())}\n"
        f"// Candidate module sha256: {sha256(candidate_path.read_bytes())}\n"
        f"// Constant-copy table sha256: {sha256(table)}\n"
    )
    if source.startswith("#version "):
        version_end = source.find("\n")
        source = source[:version_end + 1] + provenance + source[version_end + 1:]
    else:
        source = provenance + source
    metadata = {
        "shader": str(shader_path),
        "shader_sha256": sha256(shader_path.read_bytes()),
        "candidate_essl_sha256": sha256(candidate_path.read_bytes()),
        "constant_copy_table_sha256": sha256(table),
        "attributes": [attributes[key] for key in sorted(attributes)],
        "uniforms": uniforms,
        "varyings": [varyings[key] for key in sorted(varyings)],
        "inactive_varying_symbols": inactive_varyings,
        "constant_copy_assignments": len(constant_copies),
        "unmapped_constant_sources": sorted(set(unmapped_sources)),
        "interface_basis": "exact .shd symbol names/types/banks; vertex outputs map to output register 1 + scalar base / 4",
    }
    return source, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("shader_shd", type=Path)
    parser.add_argument("candidate_essl", type=Path,
                        help="SPIRV-Cross output from --native-register-interface SPIR-V")
    parser.add_argument("constant_copy_table", type=Path,
                        help="vertex.table_54.bin from native QNX finalizer output")
    parser.add_argument("output", type=Path)
    parser.add_argument("--metadata", type=Path,
                        help="optional JSON sidecar recording source hashes and interface")
    args = parser.parse_args()
    try:
        source, metadata = adapt(args.shader_shd, args.candidate_essl,
                                 args.constant_copy_table)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    args.output.write_text(source.rstrip() + "\n", encoding="utf-8")
    if args.metadata:
        import json
        args.metadata.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"generated {args.output}: {len(metadata['attributes'])} attributes, "
          f"{len(metadata['uniforms'])} uniforms, {len(metadata['varyings'])} varyings, "
          f"{metadata['constant_copy_assignments']} constant-copy assignments")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
