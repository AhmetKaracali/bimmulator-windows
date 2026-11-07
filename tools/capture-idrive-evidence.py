#!/usr/bin/env python3
"""Copy emulator artifacts into a durable cache and write a SHA-256 manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def parse_labeled_path(value: str, option: str) -> tuple[str, Path]:
    label, separator, raw_path = value.partition("=")
    if not separator or not LABEL_RE.fullmatch(label) or not raw_path:
        raise argparse.ArgumentTypeError(
            f"{option} must be LABEL=PATH; labels use letters, numbers, dots, underscores, and hyphens"
        )
    return label, Path(raw_path).expanduser()


def git_revision(root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True, help="Stable name for this run")
    parser.add_argument("--profile", required=True, help="QEMU profile name")
    parser.add_argument(
        "--launch-command",
        default="",
        help="Exact emulator launch command, with environment settings",
    )
    parser.add_argument(
        "--qemu-version",
        default="",
        help="Version string reported by qemu-system-arm --version",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("build/idrive6-cache/evidence"),
        help="Ignored durable cache directory (default: build/idrive6-cache/evidence)",
    )
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        metavar="LABEL=PATH",
        help="Artifact to copy into this evidence bundle; may be repeated",
    )
    parser.add_argument(
        "--reference",
        action="append",
        default=[],
        metavar="LABEL=PATH",
        help="Large input to hash and reference without copying; may be repeated",
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        help="QEMU snapshot file to hash and reference without copying",
    )
    args = parser.parse_args()

    if not LABEL_RE.fullmatch(args.run_id):
        parser.error("--run-id may contain letters, numbers, dots, underscores, and hyphens")
    if not LABEL_RE.fullmatch(args.profile):
        parser.error("--profile may contain letters, numbers, dots, underscores, and hyphens")

    output_root = args.output_root.expanduser().resolve()
    bundle = output_root / args.run_id
    artifact_dir = bundle / "artifacts"
    if bundle.exists():
        parser.error(f"evidence bundle already exists: {bundle}")

    try:
        inputs = [parse_labeled_path(value, "--input") for value in args.input]
        references = [parse_labeled_path(value, "--reference") for value in args.reference]
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    labels = [label for label, _ in inputs + references]
    if len(labels) != len(set(labels)):
        parser.error("artifact and reference labels must be unique")

    snapshot = args.snapshot.expanduser().resolve() if args.snapshot else None
    if not inputs and not references and snapshot is None:
        parser.error("provide at least one --input, --reference, or --snapshot")

    for label, path in inputs + references:
        if not path.is_file():
            parser.error(f"input is not a regular file ({label}): {path}")
    if snapshot is not None and not snapshot.is_file():
        parser.error(f"snapshot is not a regular file: {snapshot}")

    try:
        artifact_dir.mkdir(parents=True, exist_ok=False)
        artifacts = []
        for label, source in inputs:
            destination = artifact_dir / label
            digest = hashlib.sha256()
            size = 0
            with source.open("rb") as input_stream, destination.open("xb") as output_stream:
                while chunk := input_stream.read(CHUNK_SIZE):
                    output_stream.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
            shutil.copystat(source, destination)
            artifacts.append(
                {
                    "label": label,
                    "file": f"artifacts/{label}",
                    "source": str(source.resolve()),
                    "size_bytes": size,
                    "sha256": digest.hexdigest(),
                }
            )

        snapshot_record = None
        if snapshot is not None:
            snapshot_record = {
                "path": str(snapshot),
                "size_bytes": snapshot.stat().st_size,
                "sha256": sha256_file(snapshot),
                "copied_into_bundle": False,
            }

        reference_records = [
            {
                "label": label,
                "path": str(path.resolve()),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "copied_into_bundle": False,
            }
            for label, path in references
        ]

        manifest = {
            "schema_version": 1,
            "captured_utc": datetime.now(timezone.utc).isoformat(),
            "run_id": args.run_id,
            "profile": args.profile,
            "launch_command": args.launch_command,
            "qemu_version": args.qemu_version,
            "repository_revision": git_revision(Path(__file__).resolve().parents[1]),
            "snapshot": snapshot_record,
            "artifacts": artifacts,
            "references": reference_records,
        }
        manifest_path = bundle / "manifest.json"
        with manifest_path.open("x", encoding="utf-8") as output_stream:
            json.dump(manifest, output_stream, indent=2, sort_keys=True)
            output_stream.write("\n")
    except (OSError, shutil.Error) as exc:
        print(f"capture failed: {exc}", file=sys.stderr)
        shutil.rmtree(bundle, ignore_errors=True)
        return 1

    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
