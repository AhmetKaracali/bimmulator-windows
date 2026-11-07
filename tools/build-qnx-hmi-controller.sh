#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 1 ]]; then
  echo "Usage: $0 OUTPUT_LIBRARY" >&2
  exit 2
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scratch="$(mktemp -d "${TMPDIR:-/tmp}/idrive-hmi-controller.XXXXXX")"
trap 'rm -rf "$scratch"' EXIT
clang="${IDRIVE_QNX_CLANG:-clang}"
flags=(--target=armv7-none-eabi -mfloat-abi=soft -fPIC -ffreestanding -fno-stack-protector)
"$clang" "${flags[@]}" -std=c11 -Wall -Wextra -Werror \
  -c "$script_dir/qnx-hmi-controller.c" -o "$scratch/controller.o"
"$clang" "${flags[@]}" -c "$script_dir/qnx-libc-link-stub.c" -o "$scratch/libc.o"
ld.lld -m armelf -shared -soname libc.so.3 -o "$scratch/libc.so" "$scratch/libc.o"
ld.lld -m armelf -shared -soname libidrive-hmi-controller.so \
  --allow-shlib-undefined -o "$1" "$scratch/controller.o" "$scratch/libc.so"
echo "Built QNX HMI controller bridge: $1"
