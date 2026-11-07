#!/usr/bin/env python3
"""Run the existing strict Vita3K USSE visitor over extracted native stages."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_dir", type=Path,
                        help="output of extract-unipatch-batch.py")
    parser.add_argument("runner", type=Path,
                        help="existing idrive-usse-recompile executable")
    parser.add_argument("--spirv-val", default="spirv-val",
                        help="SPIR-V validator available in the pinned shader shell")
    parser.add_argument("--stage", choices=("vertex", "fragment"),
                        help="fallback stage for legacy manifests that do not record it")
    parser.add_argument("output", type=Path, help="new translation evidence directory")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output directory already exists: {args.output}")
    source = json.loads((args.capture_dir / "manifest.json").read_text())
    if not args.runner.is_file():
        raise SystemExit(f"recompiler is missing: {args.runner}")
    validator = shutil.which(args.spirv_val)
    if not validator:
        raise SystemExit(f"SPIR-V validator is missing from PATH: {args.spirv_val}")
    args.output.mkdir(parents=True)
    results = []
    for shader in source["results"]:
        if shader["status"] != "passed":
            results.append({"name": shader["name"], "status": "not-run",
                            "reason": "native finalization failed"})
            continue
        stage = shader.get("stage") or args.stage or "vertex"
        if stage not in ("vertex", "fragment"):
            raise ValueError(f"{shader['name']}: unsupported shader stage {stage!r}")
        fixture = args.capture_dir / shader["name"]
        translated = args.output / shader["name"]
        translated.mkdir()
        output = translated / f"{stage}.graphics.spv"
        process = subprocess.run(
            [str(args.runner.resolve()), str(fixture.resolve()), stage, str(output.resolve())],
            capture_output=True, text=True, check=False)
        result = {"name": shader["name"], "stage": stage,
                  "status": "translated" if process.returncode == 0 else "rejected",
                  "return_code": process.returncode,
                  "stdout": process.stdout.strip(), "stderr": process.stderr.strip(),
                  "asset_path": shader.get("asset_path"),
                  "source_sha256": shader.get("source_sha256")}
        if process.returncode == 0 and output.is_file():
            result["spirv_bytes"] = output.stat().st_size
            result["spirv_sha256"] = sha256(output)
            validation = subprocess.run(
                [validator, "--target-env", "vulkan1.0", str(output.resolve())],
                capture_output=True, text=True, check=False)
            result["spirv_validation"] = {
                "status": "valid" if validation.returncode == 0 else "invalid",
                "return_code": validation.returncode,
                "stdout": validation.stdout.strip(),
                "stderr": validation.stderr.strip(),
            }
            if validation.returncode:
                result["status"] = "invalid-spirv"
        results.append(result)
    report = {"source_manifest": str(args.capture_dir / "manifest.json"),
              "source_manifest_sha256": sha256(args.capture_dir / "manifest.json"),
              "runner": str(args.runner.resolve()), "runner_sha256": sha256(args.runner),
              "results": results,
              "translated": sum(row["status"] == "translated" for row in results),
              "invalid_spirv": sum(row["status"] == "invalid-spirv" for row in results),
              "rejected": sum(row["status"] == "rejected" for row in results),
              "not_run": sum(row["status"] == "not-run" for row in results),
              "scope": "strict existing USSE visitor coverage only; no native interface, graphics draw, or UI result"}
    (args.output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "translated": report["translated"],
                      "invalid_spirv": report["invalid_spirv"],
                      "rejected": report["rejected"], "not_run": report["not_run"],
                      "results": [{"name": row["name"], "status": row["status"],
                                   "stdout": row.get("stdout"), "stderr": row.get("stderr"),
                                   "spirv_validation": row.get("spirv_validation"),
                                   "asset": row.get("asset_path")} for row in results]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
