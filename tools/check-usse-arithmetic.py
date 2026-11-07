#!/usr/bin/env python3
"""Check genuine cover-shader register arithmetic on a Vulkan compute device.

This is not a texture, rasterization, HMI or rendered-pixel acceptance test.
Vertex expectations are independent column-major matrix multiplication and UV
forwarding. Fragment expectations decode the captured instruction's PA1*SA9
operation and UNORM8 packing; PA1's native sampler-channel binding is unproved.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--runner", type=Path,
                        default=Path("build/idrive6-cache/usse-recompiler/idrive-vulkan-compute"))
    parser.add_argument("--output", type=Path, required=True, help="new evidence directory")
    args = parser.parse_args()
    fixture = args.fixture
    # These expectations describe this genuine control pair, not every shader.
    expected_codes = {
        "vertex.primary.usse.bin": "bdf1efc17e37bfed1e8179f16b523268a0f3ded212ece65933ca5f0e8ada0a67",
        "fragment.primary.usse.bin": "bae9a9df20c18bc6963f6199575b30aeb3ae50aa9afbe983a3664d4e21cfc041",
        "fragment.secondary.usse.bin": "1dd499a93e1b49638e27a4792f387a4cdb10d906fc4a73a4220824ceded5694d",
    }
    for name, digest in expected_codes.items():
        if sha(fixture / name) != digest:
            raise ValueError("Unknown control program: " + name)
    for stage in ("vertex", "fragment"):
        subprocess.run(["spirv-val", "--target-env", "vulkan1.0", str(fixture / f"{stage}.compute.spv")], check=True)
    args.output.mkdir(parents=True, exist_ok=False)
    reports = []

    def run(stage, name, state):
        source, target = args.output / (name + ".in.bin"), args.output / (name + ".out.bin")
        source.write_bytes(struct.pack("<528f", *state))
        result = subprocess.run([str(args.runner.resolve()), str((fixture / f"{stage}.compute.spv").resolve()),
                                 str(source), str(target)], capture_output=True, text=True, timeout=30)
        (args.output / (name + ".stdout.log")).write_text(result.stdout)
        (args.output / (name + ".stderr.log")).write_text(result.stderr)
        result.check_returncode()
        data = target.read_bytes()
        if len(data) != 528 * 4:
            raise ValueError("Incomplete register readback")
        return data, result

    identity = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    dense = [[2, 3, 5, 7], [-1, .5, 4, 2], [.25, -3, 1, 9], [.1, .2, .3, 1]]
    for name, rows, position, uv in (
        ("vertex-identity", identity, [2, 3, 4, 1], [.25, .75]),
        ("vertex-affine", dense, [2, 3, 4, 1], [.125, .875]),
        ("vertex-negative", dense, [-2, .5, -1, 1], [.875, .125]),
    ):
        state = [0.0] * 528
        state[:2], state[4:7] = uv, position[:3]
        constants = [0.0] * 4 + [rows[r][c] for c in range(4) for r in range(4)]
        table = (fixture / "vertex.table_54.bin").read_bytes()
        if len(table) != 320:
            raise ValueError("Unmapped vertex constant table")
        for offset in range(0, len(table), 20):
            src, aux, dest, aux2, reserved, kind = struct.unpack_from("<IIHHII", table, offset)
            if aux or aux2 or reserved or kind or src >= len(constants) or dest >= 128:
                raise ValueError("Unsupported constant copy record")
            state[128 + dest] = constants[src]
        data, result = run("vertex", name, state)
        actual = list(struct.unpack_from("<6f", data, 400 * 4))
        expected = [sum(x * y for x, y in zip(row, position)) for row in rows] + uv
        if not all(math.isclose(a, e, rel_tol=1e-5, abs_tol=1e-5) for a, e in zip(actual, expected)):
            raise ValueError(f"{name}: expected {expected}, observed {actual}")
        reports.append({"case": name, "expected": expected, "actual": actual,
                        "device": result.stdout.strip(), "backend_diagnostics": result.stderr.strip()})

    fragment_table = struct.unpack("<IIHHII", (fixture / "fragment.table_54.bin").read_bytes())
    if fragment_table != (4, 0, 9, 0, 0, 0):
        raise ValueError("Unmapped fragment constant binding")
    for name, pa1, opacity, packed in (
        ("fragment-register-product", .4, .5, 0x33000000),
        ("fragment-transparent", 1, 0, 0),
        ("fragment-opaque", 1, 1, 0xff000000),
    ):
        state = [0.0] * 528
        state[:4] = [.2, pa1, .6, .8]
        state[128 + 9] = opacity
        data, result = run("fragment", name, state)
        actual = struct.unpack_from("<I", data, 400 * 4)[0]
        if actual != packed:
            raise ValueError(f"{name}: expected packed {packed:#x}, observed {actual:#x}")
        reports.append({"case": name, "pa1": pa1, "opacity": opacity,
                        "expected_packed": hex(packed), "actual_packed": hex(actual),
                        "device": result.stdout.strip(), "backend_diagnostics": result.stderr.strip()})
    report = {"scope": "register arithmetic only; native texture input layout and rendering unproved",
              "source_code_hashes": expected_codes,
              "spirv_hashes": {s: sha(fixture / f"{s}.compute.spv") for s in ("vertex", "fragment")},
              "runner_sha256": sha(args.runner), "cases": reports}
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print("PASS: three matrix/UV and three fragment-register controls; no texture/pixel claim")
    if any(r["backend_diagnostics"] for r in reports):
        print("Backend diagnostics retained in report.json and per-case stderr logs")


if __name__ == "__main__":
    main()
