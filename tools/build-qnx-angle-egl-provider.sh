#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 2 ]]; then
  echo "Usage: $0 REALIZED_QNX_ROOT OUTPUT_LIBRARY" >&2
  exit 2
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$1"
output="$2"
for library in "$root/lib/libsocket.so.3" "$root/lib/libscreen.so.1" \
               "$root/lib/libEGL.so.1" "$root/lib/libGLESv2.so.1"; do
  if [[ ! -f "$library" ]]; then
    echo "The realized QNX root is missing $library" >&2
    exit 1
  fi
done
for source in "$script_dir/angle-egl-rpc.h" \
              "$script_dir/qnx-angle-egl-provider.c" \
              "$script_dir/qnx-gles2-provider-symbols.inc" \
              "$script_dir/qnx-gles2-provider-unsupported.inc"; do
  if [[ ! -f "$source" ]]; then
    echo "Provider build input is missing: $source" >&2
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

scratch="$(mktemp -d "${TMPDIR:-/tmp}/idrive-angle-egl-provider.XXXXXX")"
trap 'rm -rf "$scratch"' EXIT
# QNX enables ARM alignment faults. RPC fields can start at any byte.
flags=(--target=armv7-none-eabi -mfloat-abi=soft -mno-unaligned-access -fPIC -ffreestanding -fno-stack-protector -O2 -std=c11 -Wall -Wextra -Werror)
if [[ "${IDRIVE_ANGLE_EGL_TRACE:-0}" == "1" ]]; then
  flags+=(-DIDRIVE_ANGLE_EGL_TRACE=1)
fi
"$qnx_clang" "${flags[@]}" -I"$script_dir" -c \
  "$script_dir/qnx-angle-egl-provider.c" -o "$scratch/provider.o"
stub_flags=(--target=armv7-none-eabi -mfloat-abi=soft -fPIC -ffreestanding -fno-stack-protector)
"$qnx_clang" "${stub_flags[@]}" -c "$script_dir/qnx-libc-link-stub.c" \
  -o "$scratch/stub.o"
ld.lld -m armelf -shared -soname libc.so.3 \
  -o "$scratch/stub.so" "$scratch/stub.o"
mkdir -p "$(dirname "$output")"
ld.lld -m armelf -shared -soname libidrive-angle-provider.so \
  --allow-shlib-undefined -o "$output" "$scratch/provider.o" \
  "$root/lib/libsocket.so.3" "$root/lib/libscreen.so.1" "$scratch/stub.so"
echo "Built QNX ANGLE EGL/GLES provider: $output"
