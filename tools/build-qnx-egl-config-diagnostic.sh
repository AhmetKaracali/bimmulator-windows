#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 2 ]]; then
  echo "Usage: $0 STAGED_ROOT OUTPUT_EXECUTABLE" >&2
  exit 2
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$1"
output="$2"
libegl="$root/lib/libEGL.so.1"
libscreen="$root/lib/libscreen.so.1"
if [[ ! -f "$libegl" || ! -f "$libscreen" ]]; then
  echo "The staged QNX root needs libEGL.so.1 and libscreen.so.1" >&2
  exit 1
fi
qnx_clang="${IDRIVE_QNX_CLANG:-clang}"
for program in "$qnx_clang" ld.lld; do
  if ! command -v "$program" >/dev/null 2>&1; then
    echo "$program is missing; enter the Nix development shell." >&2
    exit 1
  fi
done
scratch="$(mktemp -d "${TMPDIR:-/tmp}/idrive-egl-build.XXXXXX")"
trap 'rm -rf "$scratch"' EXIT
flags=(--target=armv7-none-eabi -mfloat-abi=soft -fPIC -ffreestanding -fno-stack-protector)
"$qnx_clang" "${flags[@]}" -c "$script_dir/qnx-libc-link-stub.c" -o "$scratch/stub.o"
ld.lld -m armelf -shared -soname libc.so.3 -o "$scratch/stub.so" "$scratch/stub.o"
"$qnx_clang" "${flags[@]}" -c "$script_dir/qnx-egl-config-diagnostic.c" -o "$scratch/diagnostic.o"
mkdir -p "$(dirname "$output")"
ld.lld -m armelf -e _start --dynamic-linker /usr/lib/ldqnx.so.2 \
  --allow-shlib-undefined -o "$output" "$scratch/diagnostic.o" "$libegl" "$libscreen" "$scratch/stub.so"
echo "Built QNX EGL configuration diagnostic: $output"
