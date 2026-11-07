#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 2 ]]; then
  echo "Usage: $0 REALIZED_QNX_ROOT OUTPUT_EXECUTABLE" >&2
  exit 2
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$1"
output="$2"
for library in "$root/lib/libEGL.so.1" "$root/lib/libGLESv2.so.1"; do
  if [[ ! -f "$library" ]]; then
    echo "The realized QNX root is missing $library" >&2
    exit 1
  fi
done
qnx_clang="${IDRIVE_QNX_CLANG:-clang}"
for program in "$qnx_clang" ld.lld; do
  if ! command -v "$program" >/dev/null 2>&1; then
    echo "$program is missing; launch through the Nix app or enter the Nix development shell." >&2
    exit 1
  fi
done

scratch="$(mktemp -d "${TMPDIR:-/tmp}/idrive-angle-egl-smoke.XXXXXX")"
trap 'rm -rf "$scratch"' EXIT
flags=(--target=armv7-none-eabi -mfloat-abi=soft -fPIC -ffreestanding -fno-stack-protector)
"$qnx_clang" "${flags[@]}" -c \
  "$script_dir/qnx-angle-egl-provider-smoke.c" -o "$scratch/smoke.o"
"$qnx_clang" "${flags[@]}" -c "$script_dir/qnx-libc-link-stub.c" \
  -o "$scratch/stub.o"
ld.lld -m armelf -shared -soname libc.so.3 -o "$scratch/stub.so" "$scratch/stub.o"
mkdir -p "$(dirname "$output")"
ld.lld -m armelf -e _start --dynamic-linker /usr/lib/ldqnx.so.2 \
  --allow-shlib-undefined -o "$output" "$scratch/smoke.o" \
  "$root/lib/libEGL.so.1" "$root/lib/libGLESv2.so.1" "$scratch/stub.so"
echo "Built QNX public EGL/GLES provider smoke client: $output"
