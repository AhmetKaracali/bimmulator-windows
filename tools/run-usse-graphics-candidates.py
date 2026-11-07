#!/usr/bin/env python3
"""Generate and rasterize four labeled host candidates for the BMW cover pair.

This creates renderer evidence only. It does not identify BMW's native texture
component mapping, render-target packing, or any HMI frame.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import subprocess


EXPECTED = {
    "vertex.primary.usse.bin": "bdf1efc17e37bfed1e8179f16b523268a0f3ded212ece65933ca5f0e8ada0a67",
    "fragment.primary.usse.bin": "bae9a9df20c18bc6963f6199575b30aeb3ae50aa9afbe983a3664d4e21cfc041",
    "fragment.secondary.usse.bin": "1dd499a93e1b49638e27a4792f387a4cdb10d906fc4a73a4220824ceded5694d",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mapped_bank(table_path, constants):
    table = table_path.read_bytes()
    if len(table) % 20:
        raise ValueError(f"Malformed constant mapping table: {table_path}")
    bank = [0.0] * 128
    for offset in range(0, len(table), 20):
        source, aux, destination, aux2, reserved, kind = struct.unpack_from("<IIHHII", table, offset)
        if aux or aux2 or reserved or kind or source >= len(constants) or destination >= len(bank):
            raise ValueError(f"Unsupported constant mapping record at byte {offset}")
        bank[destination] = constants[source]
    return struct.pack("<128f", *bank)


def bmp_colors(path):
    data = path.read_bytes()
    if len(data) < 54 or data[:2] != b"BM":
        raise ValueError(f"Not a BMP: {path}")
    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    width, signed_height = struct.unpack_from("<ii", data, 18)
    height = abs(signed_height)
    bits = struct.unpack_from("<H", data, 28)[0]
    if width != 256 or height != 256 or bits != 32 or len(data) != pixel_offset + width * height * 4:
        raise ValueError(f"Unexpected BMP layout: {path}")
    counts = Counter()
    for y in range(height):
        row = pixel_offset + y * width * 4
        for x in range(width):
            i = row + x * 4
            counts[tuple(data[i:i + 4])] += 1  # File order: BGRA.
    def pixel_top_left(x, y):
        storage_y = height - 1 - y if signed_height > 0 else y
        i = pixel_offset + (storage_y * width + x) * 4
        return tuple(data[i:i + 4])
    samples = {"upper_left": pixel_top_left(64, 64),
               "upper_right": pixel_top_left(192, 64),
               "lower_left": pixel_top_left(64, 192),
               "lower_right": pixel_top_left(192, 192)}
    return {"width": width, "height": height,
            "colors_bgra": {"%02x%02x%02x%02x" % color: count
                            for color, count in sorted(counts.items())},
            "samples_bgra": {key: "%02x%02x%02x%02x" % color
                             for key, color in samples.items()}}


def run(args):
    fixture = args.fixture.resolve()
    output = args.output.resolve()
    if output.exists():
        raise ValueError(f"Output directory already exists: {output}")
    for name, expected_hash in EXPECTED.items():
        actual = sha256(fixture / name)
        if actual != expected_hash:
            raise ValueError(f"Unexpected control program {name}: {actual}")
    output.mkdir(parents=True)

    # Identity transform copied through this control pair's recovered table;
    # fragment opacity is 0.5 via the known source scalar used by table_54.
    identity = [[1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0]]
    vertex_constants = [0.0] * 4 + [identity[row][column]
                                      for column in range(4) for row in range(4)]
    fragment_constants = [0.0] * 4 + [0.5]
    vertex_uniforms = mapped_bank(fixture / "vertex.table_54.bin", vertex_constants)
    fragment_uniforms = mapped_bank(fixture / "fragment.table_54.bin", fragment_constants)
    vertex_uniform_path = output / "vertex.uniforms.bin"
    fragment_uniform_path = output / "fragment.uniforms.bin"
    vertex_uniform_path.write_bytes(vertex_uniforms)
    fragment_uniform_path.write_bytes(fragment_uniforms)
    non_symmetric_matrix = [[0.8, 0.15, 0.0, 0.0],
                            [-0.1, 0.9, 0.0, 0.0],
                            [0.0, 0.0, 1.0, 0.0],
                            [0.0, 0.0, 0.0, 1.0]]
    non_symmetric_constants = [0.0] * 4 + [non_symmetric_matrix[row][column]
                                             for column in range(4) for row in range(4)]
    non_symmetric_uniform_path = output / "vertex.uniforms.nonsymmetric.bin"
    non_symmetric_uniform_path.write_bytes(
        mapped_bank(fixture / "vertex.table_54.bin", non_symmetric_constants))

    # Top-down RGBA8 texture: red, green / blue, white. Each component has a
    # deliberately distinct two-texel pattern; alpha is 255 everywhere.
    texture_path = output / "synthetic-distinct-channels.rgba"
    texture_path.write_bytes(bytes([255, 0, 0, 255, 0, 255, 0, 255,
                                    0, 0, 255, 255, 255, 255, 255, 255]))
    vertex_spv = output / "candidate.vertex.spv"
    subprocess.run([str(args.generator), str(fixture), "vertex", str(vertex_spv)], check=True)
    subprocess.run(["spirv-val", "--target-env", "vulkan1.0", str(vertex_spv)], check=True)

    cases = []
    expected_counts = {
        "R": {"00008000": 32768, "00000000": 32768},
        "G": {"00008000": 32768, "00000000": 32768},
        "B": {"00008000": 32768, "00000000": 32768},
        "A": {"00008000": 65536},
    }
    clear = "00000000"
    red_half = "00008000"
    expected_samples = {
        "R": {"upper_left": clear, "upper_right": red_half,
              "lower_left": red_half, "lower_right": clear},
        "G": {"upper_left": clear, "upper_right": red_half,
              "lower_left": clear, "lower_right": red_half},
        "B": {"upper_left": red_half, "upper_right": red_half,
              "lower_left": clear, "lower_right": clear},
        "A": {"upper_left": red_half, "upper_right": red_half,
              "lower_left": red_half, "lower_right": red_half},
    }
    for channel in "RGBA":
        fragment_spv = output / f"candidate.fragment.{channel}.spv"
        subprocess.run([str(args.generator), str(fixture), "fragment", str(fragment_spv), channel], check=True)
        subprocess.run(["spirv-val", "--target-env", "vulkan1.0", str(fragment_spv)], check=True)
        image_path = output / f"candidate-{channel}-fresh.bmp"
        cache_path = output / f"candidate-{channel}.pipeline-cache.bin"
        fresh = subprocess.run([
            str(args.runner), str(vertex_spv), str(fragment_spv),
            str(vertex_uniform_path), str(fragment_uniform_path), str(texture_path),
            "2", "2", str(image_path), "-", str(cache_path)],
            check=True, capture_output=True, text=True)
        actual = bmp_colors(image_path)
        if actual["colors_bgra"] != expected_counts[channel]:
            raise ValueError(f"{channel} candidate pixel counts differ: {actual['colors_bgra']}")
        if actual["samples_bgra"] != expected_samples[channel]:
            raise ValueError(f"{channel} candidate sample positions differ: {actual['samples_bgra']}")
        cached_image_path = output / f"candidate-{channel}-cached.bmp"
        cached = subprocess.run([
            str(args.runner), str(vertex_spv), str(fragment_spv),
            str(vertex_uniform_path), str(fragment_uniform_path), str(texture_path),
            "2", "2", str(cached_image_path), str(cache_path), "-"],
            check=True, capture_output=True, text=True)
        cached_actual = bmp_colors(cached_image_path)
        if cached_actual != actual or cached_image_path.read_bytes() != image_path.read_bytes():
            raise ValueError(f"{channel} fresh and cached render outputs differ")
        cases.append({
            "sample_component_candidate": channel,
            "packed_lane_candidate": "packed MSB to red",
            "expected_rgba_behavior": "selected component multiplied by SA9=0.5; low 8-bit lane remains zero",
            "fresh_bmp": str(image_path),
            "cache_reuse_bmp": str(cached_image_path),
            "pipeline_cache_path": str(cache_path),
            "pipeline_cache_bytes": cache_path.stat().st_size,
            **actual,
            "fresh_runner_stdout": fresh.stdout.strip(),
            "fresh_runner_stderr": fresh.stderr.strip(),
            "cached_runner_stdout": cached.stdout.strip(),
            "cached_runner_stderr": cached.stderr.strip(),
            "fresh_and_cached_bmp_bytes_identical": True,
        })

    # Reuse the genuine fragment arithmetic with a non-symmetric transform and
    # three SA9 values. The shape and texture vary by pixel; opacity must scale
    # the selected component without changing the geometry/sample mask.
    cached_g_pipeline = output / "candidate-G.pipeline-cache.bin"
    opacity_expectations = {
        "0": {"colors": {"00000000": 65536},
              "samples": {key: clear for key in expected_samples["G"]}},
        "0.5": {"colors": {"00000000": 41454, "00008000": 24082},
                "samples": {"upper_left": clear, "upper_right": red_half,
                            "lower_left": clear, "lower_right": red_half}},
        "1": {"colors": {"00000000": 41454, "0000ff00": 24082},
              "samples": {"upper_left": clear, "upper_right": "0000ff00",
                          "lower_left": clear, "lower_right": "0000ff00"}},
    }
    opacity_cases = []
    opacity_images = {}
    for opacity in (0.0, 0.5, 1.0):
        label = str(opacity).removesuffix(".0")
        fragment_bank = mapped_bank(
            fixture / "fragment.table_54.bin", [0.0] * 4 + [opacity])
        fragment_bank_path = output / f"fragment.uniforms.opacity-{label}.bin"
        fragment_bank_path.write_bytes(fragment_bank)
        image_path = output / f"nonsymmetric-opacity-{label}.bmp"
        result = subprocess.run([
            str(args.runner), str(vertex_spv), str(output / "candidate.fragment.G.spv"),
            str(non_symmetric_uniform_path), str(fragment_bank_path), str(texture_path),
            "2", "2", str(image_path), str(cached_g_pipeline), "-"],
            check=True, capture_output=True, text=True)
        actual = bmp_colors(image_path)
        expected = opacity_expectations[label]
        if actual["colors_bgra"] != expected["colors"] or actual["samples_bgra"] != expected["samples"]:
            raise ValueError(f"Opacity {label} result differs: {actual}")
        opacity_images[label] = image_path.read_bytes()
        opacity_cases.append({
            "sa9_opacity": opacity,
            "vertex_matrix_rows": non_symmetric_matrix,
            "fragment_uniform_sha256": sha256(fragment_bank_path),
            "actual_bmp": str(image_path),
            **actual,
            "pipeline_cache_sha256": sha256(cached_g_pipeline),
            "pipeline_cache_bytes": cached_g_pipeline.stat().st_size,
            "runner_stdout": result.stdout.strip(),
            "runner_stderr": result.stderr.strip(),
        })
    zero_bmp, half_bmp, full_bmp = (opacity_images[k] for k in ("0", "0.5", "1"))
    for offset in range(54, len(half_bmp), 4):
        half_is_red = half_bmp[offset + 2] == 128
        if any(zero_bmp[offset:offset + 4]):
            raise ValueError("Zero opacity did not clear the fragment's candidate output")
        expected_full = (0, 0, 255, 0) if half_is_red else (0, 0, 0, 0)
        if tuple(full_bmp[offset:offset + 4]) != expected_full:
            raise ValueError("Opacity 1.0 did not preserve the 0.5 candidate mask at full intensity")
    for label, bmp in opacity_images.items():
        if len(bmp) != len(half_bmp):
            raise ValueError(f"Opacity {label} BMP size differs")

    report = {
        "scope": "host Vulkan candidate renderer control only; no BMW native sampler/output mapping or HMI frame claim",
        "source_hashes": EXPECTED,
        "fixture_directory": str(fixture),
        "runner_sha256": sha256(args.runner),
        "generator_sha256": sha256(args.generator),
        "vertex_uniform_sha256": sha256(vertex_uniform_path),
        "fragment_uniform_sha256": sha256(fragment_uniform_path),
        "synthetic_texture_sha256": sha256(texture_path),
        "backend": "RGBA8 offscreen target, nearest 2x2 sampled RGBA8 texture, identity matrix, SA9 opacity 0.5",
        "expected_native_channel_mapping": "unresolved",
        "cases": cases,
        "non_symmetric_opacity_control": {
            "scope": "same genuine cover pair; matrix and uniform variation are host controls only",
            "vertex_uniform_sha256": sha256(non_symmetric_uniform_path),
            "pixel_scaling_verified": True,
            "opacity_cases": opacity_cases,
        },
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"PASS: four component candidates and three non-symmetric/opacity controls matched 256x256 pixel expectations; evidence: {output}")
    print("This qualifies the host raster/sample path only; the native BMW component and output mappings remain unresolved.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--generator", type=Path,
                        default=Path("build/idrive6-cache/usse-recompiler/idrive-usse-graphics"))
    parser.add_argument("--runner", type=Path,
                        default=Path("build/idrive6-cache/usse-recompiler/idrive-vulkan-graphics"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
