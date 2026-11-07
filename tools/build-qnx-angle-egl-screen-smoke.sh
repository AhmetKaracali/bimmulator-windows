#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 2 ]]; then
  echo "Usage: $0 REALIZED_QNX_ROOT OUTPUT_EXECUTABLE" >&2
  exit 2
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$1"
output="$2"
for library in "$root/lib/libscreen.so.1" "$root/lib/libEGL.so.1" \
               "$root/lib/libGLESv2.so.1"; do
  if [[ ! -f "$library" ]]; then
    echo "The realized QNX root is missing $library" >&2
    exit 1
  fi
done
qnx_clang="${IDRIVE_QNX_CLANG:-clang}"
hold_seconds="${IDRIVE_ANGLE_SCREEN_HOLD_SECONDS:-30}"
if [[ ! "$hold_seconds" =~ ^[1-9][0-9]*$ ]]; then
  echo "IDRIVE_ANGLE_SCREEN_HOLD_SECONDS must be a positive integer." >&2
  exit 2
fi
for program in "$qnx_clang" ld.lld; do
  if ! command -v "$program" >/dev/null 2>&1; then
    echo "$program is missing; enter nix develop path:." >&2
    exit 1
  fi
done

scratch="$(mktemp -d "${TMPDIR:-/tmp}/idrive-angle-egl-screen-smoke.XXXXXX")"
trap 'rm -rf "$scratch"' EXIT
flags=(--target=armv7-none-eabi -mfloat-abi=soft -fPIC -ffreestanding -fno-stack-protector -Wall -Wextra -Werror)
flags+=("-DIDRIVE_SCREEN_SMOKE_HOLD_SECONDS=$hold_seconds")
"$qnx_clang" "${flags[@]}" -c \
  "$script_dir/qnx-angle-egl-screen-smoke.c" -o "$scratch/smoke.o"
stub_flags=(--target=armv7-none-eabi -mfloat-abi=soft -fPIC -ffreestanding -fno-stack-protector)
"$qnx_clang" "${stub_flags[@]}" -c "$script_dir/qnx-libc-link-stub.c" \
  -o "$scratch/stub.o"
ld.lld -m armelf -shared -soname libc.so.3 -o "$scratch/stub.so" "$scratch/stub.o"
mkdir -p "$(dirname "$output")"
ld.lld -m armelf -e _start --dynamic-linker /usr/lib/ldqnx.so.2 \
  --allow-shlib-undefined -o "$output" "$scratch/smoke.o" \
  "$root/lib/libscreen.so.1" "$root/lib/libEGL.so.1" \
  "$root/lib/libGLESv2.so.1" "$scratch/stub.so"
echo "Built QNX ANGLE Screen window smoke client: $output"
