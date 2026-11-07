#!/usr/bin/env python3
"""Adapt one translated BMW fragment stage to its exact .shd symbols.

This preserves fragment input/uniform names and maps non-UV varying symbols to
the native PA slots declared in the matching .shd. The sampler result channel
remains an explicit renderer candidate because the IMG texture-to-USSE lane is
not yet established by the retained native table evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import sys


TYPE_NAMES = {2: "float", 3: "vec2", 4: "vec3", 5: "vec4", 0x16: "mat4"}
TYPE_WIDTHS = {2: 1, 3: 2, 4: 3, 5: 4, 0x16: 16}

# Exact X20511I fragment programs consume mediump varyings as F16-packed PA
# words. Keep each adapter scoped to an exact staged payload hash and validate
# its symbol/interface plus the expected native unpack operations below.
F16_PACKED_VARYINGS = {
    "94607d87c4120580a4b7f51328c66c25cf759e884ebe69e252ee2c700fef343b": {
        "name": "cm", "base": 0, "type": 4, "count": 3,
    },
    "726bf332014cfe9aa86842c3b7d4fa2682bccaa0aff75b915578ae270ddb5c9f": {
        "name": "base_co", "base": 0, "type": 4, "count": 3,
    },
    "afbcb6c7aa216e1f273960a0fb3f566a55fd4fe8d02ff737f8f1ae53e2d36b2c": {
        "name": "vColor", "base": 0, "type": 5, "count": 4,
    },
}

# X20511I Text_fragment.shd's sampled result feeds only PA1.x in native USSE.
# The live capture uploads that sampler as a GL_LUMINANCE font atlas, so the
# host ESSL reads coverage from the texture's red component. Keep this
# explicit and hash-scoped; the general RGBA sample-lane mapping is still an
# unverified candidate for other shaders.
SAMPLE_RESULT_COMPONENT_ADAPTERS = {
    "afbcb6c7aa216e1f273960a0fb3f566a55fd4fe8d02ff737f8f1ae53e2d36b2c": {
        "sampler": "tex0",
        "uv": "vTexCoord",
        "register": 1,
        "register_component": "x",
        "texture_component": "r",
        "observed_texture_format": "GL_LUMINANCE (0x1909), V111 font-atlas upload",
        "basis": (
            "V111 submits Text_fragment draws with a luminance glyph atlas. "
            "GLES returns glyph coverage in RGB and constant one in alpha. "
            "The finalized USSE consumes the sampled scalar "
            "through PA1.x."
        ),
    },
}

# Text_fragment table_54 maps source index 2 to uniform register 9 (SA2.y),
# while the exact .shd declares u_opacity at base 3. Text_fragment_fade repeats
# the base-minus-one relation: source index 10 to SA2.y with u_opacity at base
# 11. The native fragment consumes SA2.y's high F16 lane. HmiMain3D reflects
# uniforms by exact name and its debug-text path registers scalar `u_opacity`;
# preserve that scalar interface while packing it for the native consumer.
# The value on ordinary Text draws remains a runtime candidate.
UNIFORM_SOURCE_ADAPTERS = {
    "afbcb6c7aa216e1f273960a0fb3f566a55fd4fe8d02ff737f8f1ae53e2d36b2c": {
        "name": "u_opacity",
        "type": 2,
        "base": 3,
        "count": 4,
        "source_base": 2,
        "native_register": "SA2.y",
        "native_destination": 9,
        "packed_half_lane": "y",
        "host_array_size": 1,
        "reference_payload": "77140b130ca8a7cee0aab7ea128babdcb43afe8e8818e5b21c5e36695054b6e4",
        "reference_uniform_base": 11,
        "reference_source_index": 10,
        "host_contract": {
            "binary": "build/idrive6-cache/rootfs-x20511i/opt/hmi/ID5/bin/HmiMain3D",
            "binary_sha256": "418906bf10aeebcee6a02b8687b63a6c6e530a9263dc7171892c568e4d86845e",
            "uniform_reflection_function": "0x18b0a80",
            "uniform_name_lookup_function": "0x18a3ba4",
            "debug_text_setup_function": "0x193b254",
            "typed_value_setter_function": "0x18a7500",
            "evidence_ids": [
                "ev_c95ccd3da74f0f167c910daa88e71b96f3561cd5071e39356667640c3fc12589",
                "ev_512629255e85810cca70245c73fb4a5d08cb6ea701de7b7024d3564e01eb61c9",
                "ev_03283aa72ef6675756537a929ff5911582cd9d9ca5121fd4de8dd302042b1d99",
                "ev_3b1f96db1798a781313f3a4a2b39ec8c20bfaa64dd40f565d8ec2837001e8225",
            ],
        },
    },
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


def split_call_arguments(text: str) -> list[str]:
    args = []
    depth = 0
    start = 0
    for index, char in enumerate(text):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            args.append(text[start:index].strip())
            start = index + 1
    args.append(text[start:].strip())
    return args


def replace_intrinsic_calls(source: str, name: str, transform) -> tuple[str, int]:
    replaced = 0
    pattern = re.compile(rf"\b{re.escape(name)}\s*\(")
    while match := pattern.search(source):
        opening = source.find("(", match.start())
        depth = 0
        closing = None
        for index in range(opening, len(source)):
            if source[index] == "(":
                depth += 1
            elif source[index] == ")":
                depth -= 1
                if depth == 0:
                    closing = index
                    break
        if closing is None:
            raise ValueError(f"unterminated {name} call in translated fragment")
        args = split_call_arguments(source[opening + 1:closing])
        source = source[:match.start()] + transform(args) + source[closing + 1:]
        replaced += 1
    return source, replaced


def lower_es31_bitfield_helpers(source: str) -> tuple[str, dict[str, int]]:
    """Lower SPIRV-Cross ES 3.1 bitfield helpers to ES 3.0 uint ops."""
    def extract(args: list[str]) -> str:
        if len(args) != 3:
            raise ValueError("bitfieldExtract has an unexpected signature")
        value, offset, count = args
        mask = f"((1u << uint({count})) - 1u)"
        return f"((({value}) >> uint({offset})) & {mask})"

    def insert(args: list[str]) -> str:
        if len(args) != 4:
            raise ValueError("bitfieldInsert has an unexpected signature")
        base, insert_value, offset, count = args
        mask = f"((1u << uint({count})) - 1u)"
        shifted_mask = f"({mask} << uint({offset}))"
        return (f"((({base}) & ~{shifted_mask}) | "
                f"((({insert_value}) & {mask}) << uint({offset})))")

    source, extract_count = replace_intrinsic_calls(source, "bitfieldExtract", extract)
    source, insert_count = replace_intrinsic_calls(source, "bitfieldInsert", insert)
    return source, {"bitfieldExtract": extract_count, "bitfieldInsert": insert_count}


def adapt(shader_path: Path, candidate_path: Path, input_table_path: Path,
          constant_table_path: Path) -> tuple[str, dict]:
    shader = load_shader_parser().parse_shader(shader_path)
    if shader["stage"] != "fragment":
        raise ValueError("the adapter accepts fragment-stage .shd assets only")
    shader_hash = sha256(shader_path.read_bytes())
    source = candidate_path.read_text(encoding="utf-8")
    if "BMWSecondaryAttributes" not in source or "primary_program();" not in source:
        raise ValueError("candidate source is not the expected translated SPIRV-Cross fragment")

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

    inputs = [item for item in symbols
              if item["class"] == 6 and item["count"] > 0]
    outputs = [item for item in symbols if item["class"] == 7]
    uniforms = [item for item in symbols if item["class"] == 3]
    samplers = [item for item in uniforms if item["type"] == 0x18]
    f16_varying = F16_PACKED_VARYINGS.get(shader_hash)
    if f16_varying:
        matching = [item for item in inputs
                    if item["name"] == f16_varying["name"]]
        if (len(matching) != 1 or any(matching[0][key] != value
                                      for key, value in f16_varying.items())):
            raise ValueError("exact F16 varying adapter disagrees with the native .shd symbol")
        if f16_varying["count"] == 4:
            if not all(re.search(rf"\bpa\[0\]\.{component}\b", source)
                       for component in "xyz"):
                raise ValueError("exact F16 vec4 adapter lacks the expected PA0.x/y/z consumers")
        elif len(re.findall(r"\bunpack2xF16\s*\(", source)) < 1:
            raise ValueError("exact F16 varying adapter has no translated F16 input consumer")

    uniform_source_adapter = UNIFORM_SOURCE_ADAPTERS.get(shader_hash)
    if uniform_source_adapter:
        matching = [item for item in uniforms
                    if item["name"] == uniform_source_adapter["name"]]
        expected = {key: uniform_source_adapter[key]
                    for key in ("name", "type", "base", "count")}
        if (len(matching) != 1 or
                any(matching[0][key] != value for key, value in expected.items())):
            raise ValueError("hash-scoped opacity adapter disagrees with the native .shd symbol")

    input_table = input_table_path.read_bytes()
    if len(input_table) % 28:
        raise ValueError("native fragment input table is not whole 28-byte records")
    input_records = [struct.unpack_from("<7I", input_table, offset)
                     for offset in range(0, len(input_table), 28)]
    sample_records = [row for row in input_records if row[0] == 1]
    uv = None
    sample_register = None
    sample_record_indices = []
    native_smp_interface = False
    if samplers:
        if len(sample_records) == 1:
            sample_register = sample_records[0][2]
            sample_record_indices = [sample_records[0][3] >> 16]
        elif len(sample_records) > 1:
            # Some native finalizers expose multiple sampler-input records
            # sharing a single vec2 coordinate PA. The record's upper half of
            # field 3 matches the .shd sampler base for the observed
            # mat_list_bg.frag pair (t=0, tn=1). Preserve the first sampler as
            # a candidate, but do not pretend the remaining sample operations
            # have been reconstructed.
            registers = {row[2] for row in sample_records}
            record_indices = [row[3] >> 16 for row in sample_records]
            sampler_bases = sorted(item["base"] for item in samplers)
            if (len(registers) != 1 or record_indices != sampler_bases or
                    any(row[3] & 0xffff for row in sample_records)):
                raise ValueError(
                    "multiple native sampled-input rows do not match one shared PA "
                    "and ordered .shd sampler bases")
            sample_register = next(iter(registers))
            sample_record_indices = record_indices
        elif not sample_records:
            # mat_pad_bg uses two native SMP operations directly from PA0 and
            # has a vec3 base_co input instead of a separate vec2 uv symbol.
            # The exact decoded words select F16 coordinates in PA0, sampler
            # keys 10/14, and the .shd exposes t/t_rse at bases 0/1.
            if (shader_hash == "726bf332014cfe9aa86842c3b7d4fa2682bccaa0aff75b915578ae270ddb5c9f"
                    and [item["name"] for item in samplers] == ["t", "t_rse"]
                    and f16_varying and f16_varying["name"] == "base_co"):
                native_smp_interface = True
            else:
            # mat_subline.frag.shd's exact table_44 has no class-1 sampled
            # input row. Its SMP coordinates come from the sole vec2 input
            # named "uv" (symbol base 2 -> PA0.xy), matching the captured SMP
            # source operand PA0. The shader also declares exactly one native
            # sampler, so its .shd base is the only possible sampler slot.
            # Keep both fallbacks unambiguous and based on explicit symbols;
            # do not guess from arbitrary vec2 or sampler declarations.
                named_uv = [item for item in inputs
                            if item["type"] == 3 and item["name"].lower() == "uv"]
                if len(named_uv) != 1:
                    raise ValueError(
                        f"no sampled-input row and no unique native vec2 uv symbol: {len(named_uv)}")
                if len(samplers) != 1:
                    raise ValueError(
                        f"no sampled-input row and no unique native sampler symbol: {len(samplers)}")
                uv = named_uv[0]
                sample_register = uv["base"] // 4
                sample_record_indices = [samplers[0]["base"]]
        if sample_register is not None and sample_register >= 32:
            raise ValueError(f"native sample PA register is out of range: {sample_register}")
        if uv is None and sample_register is not None:
            uv_inputs = [item for item in inputs
                         if item["type"] == 3 and item["count"] == 2
                         and item["base"] // 4 == sample_register]
            preferred = [item for item in uv_inputs
                         if item["name"].lower() in ("uv", "vtexcoord", "varcoord")]
            if len(preferred) == 1:
                uv = preferred[0]
            elif len(uv_inputs) == 1:
                uv = uv_inputs[0]
            else:
                raise ValueError(
                    f"native sample row targets PA{sample_register}, but its vec2 input is ambiguous")
    elif sample_records:
        raise ValueError("native sampled-input row exists without a sampler symbol")

    sample_component_adapter = SAMPLE_RESULT_COMPONENT_ADAPTERS.get(shader_hash)
    if sample_component_adapter:
        if (len(samplers) != 1 or samplers[0]["name"] != sample_component_adapter["sampler"] or
                sample_register != sample_component_adapter["register"] or uv is None or
                uv["name"] != sample_component_adapter["uv"]):
            raise ValueError("hash-scoped sample component adapter disagrees with the native .shd interface")

    color_outputs = [item for item in outputs
                     if item["type"] == 5 and item["base"] == 0 and item["count"] == 4]
    if len(color_outputs) != 1 or len(outputs) != 1:
        raise ValueError("expected one vec4 fragment color output at native output base 0")

    sampler_decl = re.compile(
        r"^\s*uniform\s+(?:highp\s+)?sampler2D\s+(\w+)\s*;\s*$", re.M)
    uv_decl = re.compile(
        r"^\s*in\s+(?:highp\s+)?vec2\s+(\w+)\s*;\s*$", re.M)
    candidate_sampler = None
    candidate_uv = None
    sampler = None
    if samplers:
        sampler_declarations = list(sampler_decl.finditer(source))
        for item in samplers:
            if item["count"] != 1:
                raise ValueError(f"unsupported sampler array: {item['name']}")
        if native_smp_interface:
            native_names = {item["name"] for item in samplers}
            candidate_names = {match.group(1) for match in sampler_declarations}
            if native_names != candidate_names:
                raise ValueError(
                    f"native SMP sampler declarations disagree with .shd symbols: "
                    f"{sorted(candidate_names)} != {sorted(native_names)}")
            candidate_sampler = next(item["name"] for item in samplers
                                     if item["name"] == "t")
            candidate_uv_match = uv_decl.search(source)
            if not candidate_uv_match:
                raise ValueError("native SMP candidate lacks its removable synthetic UV input")
            candidate_uv = candidate_uv_match.group(1)
            sampler = next(item for item in samplers if item["name"] == "t")
            source, count = uv_decl.subn("", source, count=1)
            if count != 1:
                raise ValueError("could not remove native SMP's synthetic texture coordinate")
        else:
            if len(sampler_declarations) != 1:
                raise ValueError(
                    f"expected one translated texture input, found {len(sampler_declarations)}")
            candidate_sampler = sampler_declarations[0].group(1)
            candidate_uv_match = uv_decl.search(source)
            if not candidate_uv_match:
                raise ValueError("candidate source has no vec2 texture-coordinate input")
            candidate_uv = candidate_uv_match.group(1)
            sampler = next((item for item in samplers
                            if item["base"] == sample_record_indices[0]), None)
            if sampler is None:
                raise ValueError(
                    f"native sampled-input slot {sample_record_indices[0]} has no .shd sampler symbol")
            sampler_lines = "\n".join(
                f"uniform highp sampler2D {item['name']};" for item in samplers)
            source, count = sampler_decl.subn(sampler_lines, source, count=1)
            if count != 1:
                raise ValueError("could not bind the translated sampler to native names")
            source, count = uv_decl.subn(f"in highp vec2 {uv['name']};", source, count=1)
            if count != 1:
                raise ValueError("could not bind the translated coordinate to its native varying")
    else:
        sampler_declarations = list(sampler_decl.finditer(source))
        candidate_uv_match = uv_decl.search(source)
        if len(sampler_declarations) != 1 or not candidate_uv_match:
            raise ValueError("no-sampler candidate lacks its synthetic texture interface")
        candidate_sampler = sampler_declarations[0].group(1)
        candidate_uv = candidate_uv_match.group(1)
        source, count = sampler_decl.subn("", source, count=1)
        if count != 1:
            raise ValueError("could not remove the synthetic sampler")
        source, count = uv_decl.subn("", source, count=1)
        if count != 1:
            raise ValueError("could not remove the synthetic texture coordinate")

    sample_call = (
        rf"texture\(\s*{re.escape(candidate_sampler)}\s*,\s*"
        rf"{re.escape(candidate_uv)}\s*\)")
    sample_init = re.compile(
        rf"^\s*pa\[0\]\s*=\s*(?:"
        rf"{sample_call}|"
        rf"vec4\(0\.0,\s*{sample_call}\s*\.\s*[xyzwrgba],\s*0\.0,\s*0\.0\)"
        rf");\s*$", re.M)
    if sample_component_adapter:
        native_lane = sample_component_adapter["register_component"]
        texture_lane = sample_component_adapter["texture_component"]
        if not re.search(rf"\bpa\[{sample_register}\]\.{native_lane}\b", source):
            raise ValueError("sample component adapter lane is not read by the translated native body")
        sample_assignment = (
            f"pa[{sample_register}].{native_lane} = "
            f"texture({sampler['name']}, {uv['name']}).{texture_lane};"
        )
    else:
        sample_assignment = (f"pa[{sample_register}] = "
                             f"texture({sampler['name']}, {uv['name']});"
                             if samplers and not native_smp_interface else "")
    source, sample_init_count = sample_init.subn(sample_assignment, source, count=1)
    if sample_init_count != 1:
        raise ValueError("candidate texture-result initialization did not match once")

    # The generated USSE body can contain additional texture instructions
    # using the recompiler's synthetic sampler name. Rebind those references
    # to the exact sampler symbol from the BMW .shd as well. The initial PA
    # result above is a separate adapter input and does not replace these
    # native sampling operations.
    if samplers and candidate_sampler != sampler["name"]:
        source = re.sub(
            rf"\b{re.escape(candidate_sampler)}\b",
            sampler["name"],
            source,
        )

    output_decl = re.compile(
        r"^(\s*(?:layout\s*\(location\s*=\s*0\)\s*)?out\s+)"
        r"(?:highp\s+)?vec4\s+(\w+)\s*;\s*$", re.M)
    match = output_decl.search(source)
    if not match:
        raise ValueError("candidate source has no vec4 fragment output")
    candidate_output = match.group(2)
    output_name = "bmwFragmentColor"
    source, count = output_decl.subn(
        rf"\1highp vec4 {output_name};", source, count=1)
    if count != 1:
        raise ValueError("could not rename the candidate fragment output")
    source, count = re.subn(rf"\b{re.escape(candidate_output)}\b", output_name, source)
    if count < 1:
        raise ValueError("candidate fragment output is not referenced by main")

    uniform_declarations = []
    uniform_aliases = []
    native_to_host_uniform = {}
    constant_data = bytes.fromhex(shader["constant_data_hex"])
    if len(constant_data) != shader["constant_count"] * 4:
        raise ValueError(".shd constant data length disagrees with its count")
    source_constants = {
        index: f"uintBitsToFloat(0x{int.from_bytes(constant_data[index * 4:index * 4 + 4], 'big'):08x}u)"
        for index in range(shader["constant_count"])
    }
    for item in uniforms:
        if item in samplers:
            continue
        type_name = TYPE_NAMES.get(item["type"])
        if not type_name:
            raise ValueError(f"unsupported native uniform type 0x{item['type']:x}: {item['name']}")
        host_name = item["name"]
        if host_name.startswith("gl_"):
            host_name = "bmw_" + host_name[3:]
            native_to_host_uniform[item["name"]] = host_name
            uniform_aliases.append({
                "native_name": item["name"],
                "host_name": host_name,
                "reason": "ESSL reserves identifiers beginning with gl_",
            })
        interface_names = {item["name"] for item in samplers}
        if uv is not None:
            interface_names.add(uv["name"])
        if host_name in interface_names | {output_name}:
            raise ValueError(f"uniform name collides with a fragment interface symbol: {item['name']}")
        uniform_declarations.append(f"uniform highp {type_name} {host_name};")
        width = TYPE_WIDTHS[item["type"]]
        component_count = width if item["type"] == 0x16 else item["count"]
        for index in range(component_count):
            source_constants[item["base"] + index] = glsl_scalar(
                host_name, item["type"], index)

    assignments = []
    occupied_inputs: set[tuple[int, int]] = set()
    input_declarations = []
    for item in inputs:
        if uv is not None and item is uv:
            continue
        type_name = TYPE_NAMES.get(item["type"])
        width = TYPE_WIDTHS.get(item["type"])
        if type_name is None or width is None or item["type"] == 0x16:
            raise ValueError(f"unsupported native varying type 0x{item['type']:x}: {item['name']}")
        if item["count"] != width:
            raise ValueError(f"varying component count disagrees with type: {item['name']}")
        input_declarations.append(f"in highp {type_name} {item['name']};")
        for index in range(width):
            scalar_slot = item["base"] + index
            register, component_index = divmod(scalar_slot, 4)
            if register >= 32:
                raise ValueError(f"fragment input register {register} exceeds the candidate bank")
            if sample_register is not None and register == sample_register:
                raise ValueError(
                    f"varying {item['name']} overlaps sampled-result PA{sample_register}")
            key = (register, component_index)
            if key in occupied_inputs:
                raise ValueError(f"overlapping native fragment inputs at PA{register}.{('xyzw'[component_index])}")
            occupied_inputs.add(key)
            value = item["name"] if width == 1 else f"{item['name']}.{('xyzw'[index])}"
            assignments.append(f"    pa[{register}].{'xyzw'[component_index]} = {value};")

    f16_interface_adapter = None
    if f16_varying:
        item = next(x for x in inputs if x["name"] == f16_varying["name"])
        original_assignments = []
        for index in range(item["count"]):
            scalar_slot = item["base"] + index
            register, component_index = divmod(scalar_slot, 4)
            value = f"{item['name']}.{('xyzw'[index])}"
            original_assignments.append(
                f"    pa[{register}].{'xyzw'[component_index]} = {value};")
        if any(line not in assignments for line in original_assignments):
            raise ValueError("exact F16 varying adapter could not locate the direct input assignments")
        assignments = [line for line in assignments if line not in original_assignments]
        if item["count"] == 3:
            assignments.extend([
                f"    pa[0].x = uintBitsToFloat(packHalf2x16({item['name']}.xy));",
                f"    pa[0].y = uintBitsToFloat(packHalf2x16(vec2({item['name']}.z, 0.0)));",
                "    pa[0].z = 0.0;",
            ])
            native_words = ["PA0.x", "PA0.y"]
            encoding = [
                f"packHalf2x16({item['name']}.xy)",
                f"packHalf2x16(vec2({item['name']}.z, 0.0))",
            ]
        elif item["count"] == 4 and item["type"] == 5:
            # Text_fragment.shd reads the PA0 half-pairs as R/G from x,
            # B from y.x, and alpha from z.x. Keep the single-value pairs
            # explicit so the ordinary ESSL vec4 is encoded as native PA data.
            assignments.extend([
                f"    pa[0].x = uintBitsToFloat(packHalf2x16({item['name']}.xy));",
                f"    pa[0].y = uintBitsToFloat(packHalf2x16(vec2({item['name']}.z, 0.0)));",
                f"    pa[0].z = uintBitsToFloat(packHalf2x16(vec2({item['name']}.w, 0.0)));",
                "    pa[0].w = 0.0;",
            ])
            native_words = ["PA0.x", "PA0.y", "PA0.z"]
            encoding = [
                f"packHalf2x16({item['name']}.xy)",
                f"packHalf2x16(vec2({item['name']}.z, 0.0))",
                f"packHalf2x16(vec2({item['name']}.w, 0.0))",
            ]
        else:
            raise ValueError("unsupported exact F16 varying component layout")
        f16_interface_adapter = {
            "kind": "packed-f16-varying",
            "varying": item["name"],
            "logical_values": [f"{item['name']}.{component}"
                               for component in "xyzw"[:item["count"]]],
            "native_register_words": native_words,
            "encoding": encoding,
            "evidence": ("The exact X20511I Text_fragment candidate unpacks PA0.x, PA0.y and PA0.z; its vColor symbol is vec4 at base 0. "
                         "This adapter packs RG into x, B into y.x, and alpha into z.x, matching those native consumers." if item["count"] == 4 else
                         "The exact translated fragment consumes this varying through F16 unpack operations; the X20511I symbol is a vec3 at base 0."),
            "candidate_status": "runtime candidate; native lane packing remains unverified",
        }

    block = re.compile(
        r"layout\s*\(std140\)\s*uniform\s+BMWSecondaryAttributes\s*\{\s*"
        r"(?:highp\s+)?vec4\s+_m0\[32\];\s*\}\s*secondary_attributes\s*;\s*")
    source, block_count = block.subn("", source, count=1)
    if block_count != 1:
        raise ValueError("expected one candidate secondary-attribute block")
    source, loads = re.subn(
        r"^\s*sa\[\d+\]\s*=\s*secondary_attributes\._m0\[\d+\];\s*$",
        "", source, flags=re.M)
    if loads != 32:
        raise ValueError(f"expected 32 candidate SA loads, found {loads}")

    table = constant_table_path.read_bytes()
    if len(table) % 20:
        raise ValueError("native fragment constant-copy table is not whole 20-byte records")
    native_uniform_adapter_metadata = None
    if uniform_source_adapter:
        source_base = uniform_source_adapter["source_base"]
        native_destination = uniform_source_adapter["native_destination"]
        matching_copies = []
        for offset in range(0, len(table), 20):
            source_index, _reserved, destination, _reserved2, _flags = struct.unpack_from(
                "<5I", table, offset)
            if source_index == source_base and destination == native_destination:
                matching_copies.append((source_index, destination))
        if len(matching_copies) != 1:
            raise ValueError("hash-scoped opacity adapter disagrees with the native constant-copy table")
        source_constants[source_base] = (
            "uintBitsToFloat(packHalf2x16(vec2(0.0, u_opacity)))")
        native_uniform_adapter_metadata = {
            "uniform": uniform_source_adapter["name"],
            "uniform_type": "float",
            "native_symbol_base": uniform_source_adapter["base"],
            "native_symbol_count": uniform_source_adapter["count"],
            "host_uniform_array_size": uniform_source_adapter["host_array_size"],
            "source_constant_index": source_base,
            "native_destination": uniform_source_adapter["native_register"],
            "packed_half_lane": uniform_source_adapter["packed_half_lane"],
            "source_expression": "uintBitsToFloat(packHalf2x16(vec2(0.0, u_opacity)))",
            "reference_payload_sha256": uniform_source_adapter["reference_payload"],
            "reference_uniform_base": uniform_source_adapter["reference_uniform_base"],
            "reference_source_index": uniform_source_adapter["reference_source_index"],
            "host_contract": uniform_source_adapter["host_contract"],
            "evidence": (
                "The exact Text_fragment table_54 maps source index 2 to SA2.y while its .shd "
                "declares u_opacity at base 3. Text_fragment_fade repeats source 10 to SA2.y "
                "with u_opacity at base 11; translated USSE reads the high F16 lane. Ghidra "
                "shows HmiMain3D maps the exact scalar name u_opacity and sets one float. "
                "The source-to-register mapping still needs runtime confirmation."
            ),
            "candidate_status": "static interface evidence; ordinary Text draw value and glyph visibility pending runtime confirmation",
        }
    constant_copies = []
    unmapped_sources = []
    for offset in range(0, len(table), 20):
        source_index, _reserved, destination, _reserved2, _flags = struct.unpack_from(
            "<5I", table, offset)
        if source_index >= 128 or destination >= 128:
            continue
        expression = source_constants.get(source_index)
        if expression is None:
            unmapped_sources.append(source_index)
            continue
        constant_copies.append(
            f"    sa[{destination // 4}].{'xyzw'[destination % 4]} = {expression};")

    call_target = ("secondary_program" if re.search(
        r"^\s*secondary_program\(\);\s*$", source, re.M) else "primary_program")
    insertion = "\n".join(assignments + constant_copies + [f"    {call_target}();"])
    source, inserted = re.subn(
        rf"^\s*{call_target}\(\);$",
        insertion,
        source, count=1, flags=re.M)
    if inserted != 1:
        raise ValueError(f"could not locate candidate {call_target} call")

    source, lowered_helpers = lower_es31_bitfield_helpers(source)

    version_end = source.find("\n")
    declarations = input_declarations + uniform_declarations
    source = source[:version_end + 1] + "\n".join(declarations) + "\n" + source[version_end + 1:]
    for native_name, host_name in native_to_host_uniform.items():
        source = re.sub(rf"\b{re.escape(native_name)}\b", host_name, source)
        if not re.search(rf"\b{re.escape(host_name)}\b", source):
            raise ValueError(f"host uniform alias was not emitted in generated ESSL: {host_name}")
    if sample_component_adapter:
        sample_provenance = (
            f"// Sample result candidate: texture {sample_component_adapter['texture_component']} maps to "
            f"native PA{sample_register}.{sample_component_adapter['register_component']} for "
            f"{sample_component_adapter['observed_texture_format']}; native lane mapping is not "
            "independently verified.\n"
        )
    elif samplers and not native_smp_interface and uv is not None:
        sample_provenance = (
            f"// Sample result candidate: full RGBA in PA{sample_register} from {sampler['name']}"
            f" using UV {uv['name']} at native base {uv['base']}; lane mapping is unverified.\n"
        )
    elif native_smp_interface:
        sample_provenance = "// Native SMP operations remain bound to their exact .shd samplers.\n"
    else:
        sample_provenance = "// Native shader has no sampler symbol; no sample is injected.\n"
    provenance = (
        "// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.\n"
        f"// .shd sha256: {sha256(shader_path.read_bytes())}\n"
        f"// Candidate module sha256: {sha256(candidate_path.read_bytes())}\n"
        f"// Native input table sha256: {sha256(input_table)}\n"
        f"// Constant-copy table sha256: {sha256(table)}\n"
        "// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.\n" +
        (f"// Host interface adapter: {f16_varying['name']} is encoded as packed F16 varying words.\n"
         if f16_interface_adapter else "") +
        ("// Host uniform adapter: exact-hash scalar u_opacity is packed into the high F16 lane of SA2.y; runtime candidate.\n"
         if native_uniform_adapter_metadata else "") +
        sample_provenance
        + "".join(
            f"// IDRIVE_UNIFORM_ALIAS native={item['native_name']} host={item['host_name']}\n"
            for item in uniform_aliases)
    )
    source = source[:version_end + 1] + provenance + source[version_end + 1:]
    metadata = {
        "stage": "fragment",
        "shader": str(shader_path),
        "shader_sha256": sha256(shader_path.read_bytes()),
        "candidate_essl_sha256": sha256(candidate_path.read_bytes()),
        "constant_copy_table_sha256": sha256(table),
        "samplers": samplers,
        "mapped_sampler_candidate": ("native-smp-exact" if native_smp_interface else
                                      sampler["name"] if samplers else None),
        "unmapped_sampler_symbols": ([] if native_smp_interface else
                                     [item["name"] for item in samplers
                                      if item["name"] != sampler["name"]] if samplers else []),
        "native_sample_record_count": len(sample_records),
        "native_sample_record_sampler_bases": sample_record_indices,
        "uv_input": uv["name"] if uv else None,
        "sample_pa_register_candidate": sample_register,
        "varying_inputs": inputs,
        "native_register_assignments": assignments,
        "uniforms": [item for item in uniforms if item not in samplers],
        "uniform_aliases": uniform_aliases,
        "constant_copy_assignments": len(constant_copies),
        "unmapped_constant_sources": sorted(set(unmapped_sources)),
        "sample_result_candidate": (
            "component-remap-candidate" if sample_component_adapter else
            "native-smp" if native_smp_interface else
            "full_rgba" if samplers else "not-sampled"),
        "sample_result_native_verified": False,
        "sample_result_adapter": ({
            **sample_component_adapter,
            "candidate_status": "runtime-candidate",
            "native_lane": f"PA{sample_component_adapter['register']}.{sample_component_adapter['register_component']}",
            "source_expression": (
                f"texture({sample_component_adapter['sampler']}, "
                f"{sample_component_adapter['uv']}).{sample_component_adapter['texture_component']}"
            ),
        } if sample_component_adapter else None),
        "output_byte_order_candidate": "packed_lsb_to_rgba",
        "output_byte_order_native_verified": False,
        "es31_bitfield_helpers_lowered": lowered_helpers,
        "host_interface_adapter": f16_interface_adapter,
        "native_uniform_adapters": ([native_uniform_adapter_metadata]
                                     if native_uniform_adapter_metadata else []),
        "native_smp_interface": native_smp_interface,
        "limitations": ([
            "Two exact SMP instructions are translated and bound to t/t_rse; source coordinate packing, sampled texture formats, result lanes and output packing remain runtime candidates.",
            "The .shd has two PSU payloads; this adapter uses the CPU finalizer's selected allocation without assigning payload identity.",
        ] if native_smp_interface else [
            ("A hash-scoped luminance to PA lane adapter is based on the captured GL_LUMINANCE font atlas and native PA use; "
             "the SGX sampled-lane assignment is still a runtime candidate." if sample_component_adapter else
             "The finalized native input row and vec2 varying agree on the sampled-result PA register; all four texture result lanes are preserved, while native lane mapping remains unverified."),
            "Only the first sampled result is represented. Additional sampler symbols are retained by name but their sampling operations are not reconstructed.",
            "The .shd has two PSU payloads; this adapter uses the CPU finalizer's selected allocation without assigning payload identity.",
        ]),
    }
    return source, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("shader_shd", type=Path)
    parser.add_argument("candidate_essl", type=Path)
    parser.add_argument("native_input_table", type=Path)
    parser.add_argument("constant_copy_table", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--metadata", type=Path)
    args = parser.parse_args()
    try:
        source, metadata = adapt(args.shader_shd, args.candidate_essl,
                                 args.native_input_table, args.constant_copy_table)
    except (OSError, KeyError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    args.output.write_text(source.rstrip() + "\n", encoding="utf-8")
    if args.metadata:
        args.metadata.write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"generated {args.output}: {len(metadata['varying_inputs'])} inputs, "
          f"{len(metadata['uniforms'])} uniforms, "
          f"{metadata['constant_copy_assignments']} constant-copy assignments, "
          f"sample={metadata['sample_result_candidate']} "
          "(native lane mapping unverified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
