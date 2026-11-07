#!/usr/bin/env bash
set -euo pipefail
if [[ $# -gt 1 ]]; then
  echo "Usage: $0 [BUILD_DIRECTORY] (inside nix develop .#shader)" >&2
  exit 2
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -z "${IDRIVE_VITA3K_SOURCE:-}" || -z "${IDRIVE_GLSLANG_INCLUDE:-}" ]]; then
  echo "Enter nix develop .#shader for the pinned translator and builder sources." >&2
  exit 2
fi
build="${1:-$script_dir/../build/idrive6-cache/usse-recompiler}"
cmake -S "$script_dir/usse-recompiler" -B "$build" -G Ninja \
  -DVITA3K_ROOT="$IDRIVE_VITA3K_SOURCE" -DCMAKE_BUILD_TYPE=Release
cmake --build "$build" -j "${IDRIVE_SHADER_BUILD_JOBS:-4}"
