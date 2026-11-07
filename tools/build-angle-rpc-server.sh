#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd "$script_dir/.." && pwd)"
angle_root="${IDRIVE_ANGLE_ROOT:-}"
cxx="${IDRIVE_HOST_CXX:-clang++}"
output="${1:-$repo_dir/build/idrive6-cache/angle-frame-server}"

if [[ -z "$angle_root" || ! -d "$angle_root/include/EGL" || ! -d "$angle_root/lib" ]]; then
  echo "ANGLE is unavailable; run this script in the default nix develop shell." >&2
  exit 1
fi
if ! command -v "$cxx" >/dev/null 2>&1; then
  echo "Host C++ compiler is unavailable: $cxx" >&2
  exit 1
fi

mkdir -p "$(dirname "$output")"
"$cxx" -std=c++17 -Wall -Wextra -Werror \
  -I"$angle_root/include" -I"$script_dir" \
  "$script_dir/angle-frame-server.cpp" \
  -L"$angle_root/lib" -Wl,-rpath,"$angle_root/lib" \
  -lEGL -lGLESv2 \
  -o "$output"
echo "Built host ANGLE frame RPC server: $output"
