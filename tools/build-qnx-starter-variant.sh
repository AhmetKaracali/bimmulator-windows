#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 2 || ! "$1" =~ ^0x[0-9a-fA-F]{1,8}$ ]]; then
  echo "Usage: $0 0xVARIANT_MASK OUTPUT_EXECUTABLE" >&2
  exit 2
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
qnx_clang="${IDRIVE_QNX_CLANG:-clang}"
for program in "$qnx_clang" ld.lld; do
  if ! command -v "$program" >/dev/null 2>&1; then
    echo "$program is missing; enter the Nix development shell." >&2
    exit 1
  fi
done
scratch="$(mktemp -d "${TMPDIR:-/tmp}/idrive-variant-build.XXXXXX")"
trap 'rm -rf "$scratch"' EXIT
flags=(--target=armv7-none-eabi -mfloat-abi=soft -fPIC -ffreestanding -fno-stack-protector)
"$qnx_clang" "${flags[@]}" -c "$script_dir/qnx-variant-libc-link-stub.c" -o "$scratch/stub.o"
ld.lld -m armelf -shared -soname libc.so.3 -o "$scratch/stub.so" "$scratch/stub.o"
"$qnx_clang" "${flags[@]}" -D"IDRIVE_VARIANT_MASK=$1" -c "$script_dir/qnx-starter-variant.c" -o "$scratch/client.o"
ld.lld -m armelf -e _start --dynamic-linker /usr/lib/ldqnx.so.2 \
  -o "$2" "$scratch/client.o" "$scratch/stub.so"
echo "Built QNX starter development variant helper: $2"
