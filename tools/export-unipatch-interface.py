#!/usr/bin/env python3
"""Export a versioned, evidence-linked view of a native UniPatch shader pair.

This tool joins the shipped IMG driver's CPU finalizer output with the original
BMW .shd containers and bounded Ghidra Evidence. It preserves opaque fields and
marks incomplete interface semantics as unknown; it does not render a frame.
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
from typing import Any


DRIVER_SHA256 = "d4776fc2f6cf01668ca21b326338960e14b6d69510ca2f0e6b37cf72269ccf69"
TABLES = [
    {"name": "fragment_input_records", "count_offset": 0x44, "pointer_offset": 0x48,
     "count_kind": "u16", "stride": 28},
    {"name": "native_table_4c", "count_offset": 0x4C, "pointer_offset": 0x50,
     "count_kind": "u32", "stride": 20},
    {"name": "native_constant_copy_records", "count_offset": 0x54, "pointer_offset": 0x58,
     "count_kind": "u16", "stride": 20},
    {"name": "native_table_5c", "count_offset": 0x5C, "pointer_offset": 0x60,
     "count_kind": "u16", "stride": 12},
    {"name": "native_table_64", "count_offset": 0x64, "pointer_offset": 0x68,
     "count_kind": "u32", "stride": 12},
    {"name": "native_texture_state_records", "count_offset": 0x94, "pointer_offset": 0x98,
     "count_kind": "u32", "stride": 36},
]
EXTRACTED_TABLE_NAMES = {
    0x44: "table_44",
    0x4C: "table_4c",
    0x54: "table_54",
    0x5C: "table_5c",
    0x64: "table_64",
    0x94: "table_94",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relpath(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"input is outside project root: {path}") from exc


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def u16(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 2 > len(data):
        raise ValueError(f"truncated u16 at 0x{offset:x}")
    return struct.unpack_from("<H", data, offset)[0]


def u32(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise ValueError(f"truncated u32 at 0x{offset:x}")
    return struct.unpack_from("<I", data, offset)[0]


def load_shader_parser():
    path = Path(__file__).with_name("inspect-sgx-shader.py")
    spec = importlib.util.spec_from_file_location("idrive_inspect_sgx_shader", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load shader container parser at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_capture_stage(capture_text: str, stage: str) -> dict[str, str]:
    start = re.search(r"^BMW-UNIPATCH-BEGIN " + stage + r"$", capture_text, re.M)
    if not start:
        raise ValueError(f"capture is missing {stage} stage")
    section = capture_text[start.end():]
    boundary = re.search(r"^BMW-UNIPATCH-BEGIN ", section, re.M)
    if boundary:
        section = section[:boundary.start()]
    result: dict[str, str] = {}
    for key in ("parsed-record", "parsed-PSU", "final-pointer", "final-size",
                "instruction-count", "instruction-pointer"):
        matches = re.findall(r"^" + re.escape(key) + r"=0x([0-9a-fA-F]{8})$", section, re.M)
        if len(matches) != 1:
            raise ValueError(f"{stage}: expected one {key} in native capture")
        result[key] = "0x" + matches[0].lower()
    if not re.search(r"^BMW-UNIPATCH-PASS " + stage + r"$", section, re.M):
        raise ValueError(f"{stage}: native finalizer did not pass")
    return result


def read_final_table(stage_dir: Path, stage: str, final: bytes, table: dict[str, Any],
                     allocation_base: int, expected_range: dict[str, Any]) -> dict[str, Any]:
    if table["count_kind"] == "u16":
        count = u16(final, table["count_offset"])
    else:
        count = u32(final, table["count_offset"])
    pointer = u32(final, table["pointer_offset"])
    extracted_name = EXTRACTED_TABLE_NAMES[table["count_offset"]]
    path = stage_dir / f"{stage}.{extracted_name}.bin"
    payload = path.read_bytes()
    if len(payload) != count * table["stride"]:
        raise ValueError(f"{path}: byte length disagrees with descriptor count/stride")
    if count and (pointer < allocation_base or pointer - allocation_base != expected_range["offset"]):
        raise ValueError(f"{path}: descriptor pointer disagrees with captured allocation range")
    records: list[dict[str, Any]] = []
    if table["name"] == "fragment_input_records":
        for index in range(count):
            offset = index * table["stride"]
            words = list(struct.unpack_from("<7I", payload, offset))
            records.append({
                "index": index,
                "raw_words_u32": words,
                "branch_evidence": {
                    "ghidra_address": "0x571c8",
                    "record_word_0": "zero selects non-texture iterator path; nonzero selects texture lookup path",
                    "record_word_2": "used as the fragment input / texture-unit lookup index",
                    "record_word_3_low16": "used by the non-texture format path",
                    "record_byte_0x0e_u16": "indexes a native texture-state record in the texture path",
                    "record_word_1_bit_0": "changes a generated hardware flag; semantic name unresolved",
                },
                "decoded_fixture_fields": {
                    "kind_word": words[0],
                    "routing_flags_word": words[1],
                    "input_or_texture_unit_index": words[2],
                    "format_or_index_word": words[3],
                    "texture_state_record_index": struct.unpack_from("<H", payload, offset + 0x0E)[0],
                    "opaque_words_4_to_6": words[4:7],
                },
            })
    elif table["name"] == "native_constant_copy_records":
        for index in range(count):
            words = list(struct.unpack_from("<5I", payload, index * table["stride"]))
            records.append({
                "index": index,
                "raw_words_u32": words,
                "source_constant_index": words[0],
                "destination_uniform_register": words[2],
                "other_words": [words[1], words[3], words[4]],
                "field_mapping_basis": "IMG draw/setup copy path; retained as a partial mapping",
            })
    elif table["name"] == "native_texture_state_records":
        for index in range(count):
            offset = index * table["stride"]
            words = list(struct.unpack_from("<9I", payload, offset))
            records.append({
                "index": index,
                "raw_words_u32": words,
                "lookup_fields_u16": [
                    struct.unpack_from("<H", payload, offset)[0],
                    struct.unpack_from("<H", payload, offset + 2)[0],
                ],
                "semantic_limit": "SetupUSEFragmentShader consumes the first two u16 values; field names remain unknown",
            })
    else:
        for index in range(count):
            raw = payload[index * table["stride"]:(index + 1) * table["stride"]]
            records.append({"index": index, "raw_hex": raw.hex()})
    return {
        "name": table["name"],
        "descriptor_offset": f"0x{table['count_offset']:02x}",
        "pointer_offset": f"0x{table['pointer_offset']:02x}",
        "count": count,
        "record_bytes": table["stride"],
        "sha256": sha256(payload),
        "records": records,
    }


def parse_stage(stage: str, root: Path, source_path: Path, run_inputs: dict[str, Any],
                capture_fields: dict[str, str], capture_dir: Path,
                finalizer_stage: dict[str, Any]) -> dict[str, Any]:
    source_path = source_path.resolve()
    source_rel = relpath(source_path, root)
    source_bytes = source_path.read_bytes()
    source_hash = sha256(source_bytes)
    input_meta = run_inputs.get(source_rel)
    if not input_meta or input_meta.get("sha256") != source_hash:
        raise ValueError(f"{source_rel}: source identity disagrees with finalizer run manifest")
    shader_parser = load_shader_parser()
    source = shader_parser.parse_shader(source_path)
    expected_stage_id = {"vertex": 0, "fragment": 1}[stage]
    if source["stage_id"] != expected_stage_id:
        raise ValueError(f"{source_rel}: .shd stage ID is not {stage}")

    stage_dir = capture_dir
    final = (stage_dir / f"{stage}.final.bin").read_bytes()
    if len(final) < 0xA4:
        raise ValueError(f"{stage}: finalizer allocation is truncated")
    if len(final) != finalizer_stage["allocation_bytes"] or sha256(final) != finalizer_stage["allocation_sha256"]:
        raise ValueError(f"{stage}: native finalizer allocation disagrees with extraction manifest")

    primary_count, secondary_count = u16(final, 0x0C), u16(final, 0x1C)
    primary = (stage_dir / f"{stage}.primary.usse.bin").read_bytes()
    secondary = (stage_dir / f"{stage}.secondary.usse.bin").read_bytes()
    if len(primary) != primary_count * 8 or len(secondary) != secondary_count * 8:
        raise ValueError(f"{stage}: code byte lengths disagree with native instruction counts")
    patch_index = u16(final, 0x14)
    placeholder = (patch_index < primary_count and
                   primary[patch_index * 8:(patch_index + 1) * 8] == bytes(8))

    tables = []
    manifest_ranges = finalizer_stage["ranges"]
    for table in TABLES:
        extracted_name = EXTRACTED_TABLE_NAMES[table["count_offset"]]
        expected = manifest_ranges[extracted_name]
        parsed_table = read_final_table(stage_dir, stage, final, table,
                                        int(capture_fields["final-pointer"], 16), expected)
        if (parsed_table["count"] != expected["count"] or
                parsed_table["sha256"] != expected["sha256"] or
                parsed_table["record_bytes"] * parsed_table["count"] != expected["bytes"]):
            raise ValueError(f"{stage}: {extracted_name} disagrees with extraction manifest")
        tables.append(parsed_table)
    mask_bits = u32(final, 0x9C)
    mask_file = stage_dir / f"{stage}.table_9c.bin"
    mask_data = mask_file.read_bytes()
    if len(mask_data) != ((mask_bits + 31) // 32) * 4:
        raise ValueError(f"{stage}: output-mask word count disagrees with native descriptor")

    payloads = []
    for item in source["payloads"]:
        start, length = item["offset"], item["length"]
        payloads.append({
            **item,
            "payload_sha256": sha256(source_bytes[start:start + length]),
        })
    symbols = []
    for item in source["symbols"]:
        name = item["name"]
        if name.startswith("a_"):
            role = "attribute_candidate"
        elif name.startswith("u_"):
            role = "uniform_candidate"
        elif name.startswith("tex"):
            role = "sampler_candidate"
        elif name == "varCoord":
            role = "varying_candidate"
        elif name in ("gl_Position", "gl_FragColor"):
            role = "built_in_output_candidate"
        else:
            role = "unclassified"
        symbols.append({**item, "role_candidate_from_name": role,
                        "role_confidence": "inferred_from_name_only"})

    return {
        "stage": stage,
        "source_container": {
            "path": source_rel,
            "size": len(source_bytes),
            "sha256": source_hash,
            "format": "BMW / IMG .shd container",
            "stage_id": source["stage_id"],
            "stage_info_hex": source["stage_info_hex"],
            "payload_candidates": payloads,
            "selected_payload_index": None,
            "selection_note": "The CPU parser returned parsed-record+0x88 for finalization, but its source-payload index has not been mapped.",
            "constant_words_u32": [int.from_bytes(bytes.fromhex(source["constant_data_hex"])[i:i + 4], "big")
                                   for i in range(0, len(bytes.fromhex(source["constant_data_hex"])), 4)],
            "symbols": symbols,
        },
        "native_parse_selection": {
            "parser_raw_address": "0x0c7c8",
            "stage_argument": 1 if stage == "vertex" else 0,
            "variant_argument": 0,
            "flags_argument": 0,
            "parsed_record_guest_address": capture_fields["parsed-record"],
            "selected_psu_root_guest_address": capture_fields["parsed-PSU"],
            "pointer_identity_note": "Guest-local pointer for this capture, not a stable source identity.",
        },
        "programs": {
            "primary": {
                "instruction_count": primary_count,
                "sha256": sha256(primary),
                "native_patch_instruction_index": patch_index,
                "patch_word_is_zero_placeholder": placeholder,
                "instruction_bytes_file": f"{stage}.primary.usse.bin",
                "execution_order": "not established by this extraction",
            },
            "secondary": {
                "instruction_count": secondary_count,
                "sha256": sha256(secondary),
                "instruction_bytes_file": f"{stage}.secondary.usse.bin",
                "role": "native secondary program; scheduling/task glue semantics are not fully mapped",
                "execution_order": "not established by this extraction",
            },
        },
        "native_tables": tables,
        "output_mask": {
            "bit_count": mask_bits,
            "words_u32_le": list(struct.unpack("<" + "I" * (len(mask_data) // 4), mask_data)) if mask_data else [],
            "sha256": sha256(mask_data),
        },
        "stage_interfaces": {
            "attributes": "draw-time binding and conversion not captured in this CPU finalizer run",
            "uniforms": "source names and native constant-copy records are present; locations and mutability are incomplete",
            "varyings": "vertex/fragment linkage and interpolation state are not established",
            "samplers": "fragment input and texture-state records are partially mapped; sampled channel/register mapping is unresolved",
            "fragment_outputs": "native output mask and shader pack instruction are retained; target format and blend state are not captured",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--capture-dir", type=Path, required=True)
    parser.add_argument("--capture-log", type=Path, required=True)
    parser.add_argument("--ghidra-evidence", type=Path, required=True)
    parser.add_argument("--vertex-shd", type=Path, required=True)
    parser.add_argument("--fragment-shd", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="new JSON file; existing files are rejected")
    args = parser.parse_args()

    try:
        root = args.project_root.resolve()
        run_path = args.run_manifest.resolve()
        capture_dir = args.capture_dir.resolve()
        log_path = args.capture_log.resolve()
        evidence_path = args.ghidra_evidence.resolve()
        run_manifest = load_json(run_path)
        extractor_manifest = load_json(capture_dir / "manifest.json")
        ghidra = load_json(evidence_path)
        capture_bytes = log_path.read_bytes()
        capture_text = capture_bytes.decode("ascii", errors="replace").replace("\r", "")
        run_inputs = run_manifest["inputs"]

        driver_rel = next((key for key in run_inputs if key.endswith("/libImgGLESv2.so")), None)
        if driver_rel is None or run_inputs[driver_rel].get("sha256") != DRIVER_SHA256:
            raise ValueError("run manifest does not identify the verified X20511I IMG GLES driver")
        if len(ghidra.get("artifacts", [])) != 1:
            raise ValueError("Ghidra Evidence must identify exactly one analyzed artifact")
        artifact = ghidra["artifacts"][0]
        artifact_hash = artifact.get("digest", {}).get("sha256")
        if artifact_hash != DRIVER_SHA256:
            raise ValueError("Ghidra Evidence artifact does not match the verified IMG driver")
        if extractor_manifest.get("capture_sha256") != sha256(capture_bytes):
            raise ValueError("native capture bytes do not match the extraction manifest")
        run_capture = run_manifest.get("capture")
        if run_capture and run_capture != relpath(log_path, root):
            raise ValueError("native capture path disagrees with finalizer run manifest")

        evidence_by_query = {}
        for record in ghidra.get("records", []):
            params = record.get("parameters") or {}
            key = (record.get("operation"), params.get("procedure"))
            evidence_by_query.setdefault(key, []).append(record)
        required_queries = [
            ("procedure_pseudo_code", "0x571c8"),
            ("procedure_pseudo_code", "0x56d6c"),
            ("procedure_pseudo_code", "0x61e40"),
        ]
        missing = [key for key in required_queries if not evidence_by_query.get(key)]
        if missing:
            raise ValueError("Ghidra Evidence is missing required queries: " + repr(missing))
        ghidra_refs = [
            {"evidence_id": evidence_by_query[key][0]["evidence_id"],
             "operation": key[0], "ghidra_address": key[1]}
            for key in required_queries
        ]
        gl_tex = evidence_by_query.get(("procedure_pseudo_code", "glTexImage2D"), [])
        if gl_tex:
            ghidra_refs.append({"evidence_id": gl_tex[0]["evidence_id"],
                                "operation": "procedure_pseudo_code", "procedure": "glTexImage2D"})

        finalizer_stages = {item["stage"]: item for item in extractor_manifest["stages"]}
        stages = {}
        for stage, source in (("vertex", args.vertex_shd), ("fragment", args.fragment_shd)):
            fields = parse_capture_stage(capture_text, stage)
            stages[stage] = parse_stage(stage, root, source, run_inputs, fields,
                                        capture_dir, finalizer_stages[stage])

        fragment_input = stages["fragment"]["native_tables"][0]
        fragment_texture = next(t for t in stages["fragment"]["native_tables"]
                                if t["name"] == "native_texture_state_records")
        report = {
            "schema": {"id": "org.idrive6.native-unipatch-pair", "version": 1},
            "target": {
                "vehicle_runtime": "NBTevo_X20511I",
                "software": "X20511I",
                "authority": "shipped-artifact native CPU parser/finalizer plus static analysis",
                "renderer_passed": False,
                "hmi_draw_state_observed": bool(run_manifest.get("fixture_state", {}).get("native_hmi_draw_state_observed")),
            },
            "driver": {"path": driver_rel, "sha256": DRIVER_SHA256,
                       "ghidra_image_coordinate_rule": "Ghidra shared-library address = raw VA + 0x10000"},
            "capture": {
                "log": relpath(log_path, root),
                "log_sha256": sha256(capture_bytes),
                "extracted_dir": relpath(capture_dir, root),
                "extraction_manifest_sha256": sha256((capture_dir / "manifest.json").read_bytes()),
                "ghidra_evidence": relpath(evidence_path, root),
            },
            "native_analysis_evidence": ghidra_refs,
            "pair": stages,
            "sampler_contract": {
                "native_input_record_table": fragment_input,
                "native_texture_state_table": fragment_texture,
                "native_rgba8_unsigned_byte_descriptor": {
                    "raw_driver_data_address": "0x802b4",
                    "ghidra_address": "0x902b4",
                    "descriptor_words_copied_by_pvr_unipatch_set_texture_format": [4, 0, 1, 2, 3],
                    "claimed_gl_format": "GL_RGBA / GL_UNSIGNED_BYTE",
                    "claim_basis": "CPU finalizer fixture and native driver data table",
                },
                "fixture_mapping": {
                    "input_record_word_0_nonzero": "native fragment setup takes texture lookup branch",
                    "input_or_texture_unit_index": 0,
                    "texture_state_record_index_from_byte_0x0e": 0,
                    "texture_state_first_two_u16": [0, 0],
                    "sample_result_register": None,
                    "sampled_channel_order": None,
                    "status": "texture resource routing is partly observed; sampled-value register/channel routing remains unresolved",
                },
                "discriminating_next_draw": {
                    "purpose": "determine which sampled component reaches the fragment operation consuming PA1",
                    "texture": "one 1x1 RGBA8 texel with four distinct byte values, sampled at the center with nearest filtering",
                    "controlled_uniform": "SA9 = 0.5, matching the recovered constant-copy record",
                    "candidate_scalar_outputs": {
                        "R": 14, "G": 47, "B": 79, "A": 113,
                        "note": "UNORM8 rounding of each candidate channel multiplied by 0.5; final output lane/packing must be read from the actual draw",
                    },
                    "expected_observation": "a native SGX/HU draw with this state identifies the source channel; record its input descriptor, texture format, draw state, and output bytes",
                    "host_harness_limit": "a host draw for each candidate mapping validates the harness and records candidate pixels, but cannot establish which mapping BMW's native driver uses",
                    "authority_required": "read-only HU draw capture or an independently verified reconstruction of the native SGX sampler path",
                    "availability": "native sampled-value mapping remains unknown; a host-only candidate draw is useful for renderer qualification but does not resolve this contract",
                },
            },
            "limitations": [
                "The .shd fragment has two PSU payload candidates; selected_payload_index remains unknown.",
                "Native input/texture records configure lookup state but do not establish sampled component data in PA1.",
                "Primary/secondary scheduling and task glue remain incomplete; this is not a graphics-stage executable IR.",
                "Attribute fetch, vertex-to-fragment varying linkage, render-target format, and blend state remain unobserved.",
                "The captured fixture uses explicit RGBA8/UNSIGNED_BYTE descriptor state and is not an HMI draw capture.",
            ],
        }
        output = args.output.resolve()
        if output.exists():
            raise FileExistsError(f"refusing to overwrite {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"output": relpath(output, root), "sha256": sha256(output.read_bytes()),
                          "ghidra_evidence": len(ghidra_refs), "stages": list(stages)}, indent=2))
        return 0
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
