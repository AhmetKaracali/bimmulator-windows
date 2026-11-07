#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 1 ]]; then
  echo "Usage: $0 OUTPUT_EXECUTABLE" >&2
  exit 2
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scratch="$(mktemp -d "${TMPDIR:-/tmp}/idrive-title-cache.XXXXXX")"
trap 'rm -rf "$scratch"' EXIT
clang="${IDRIVE_QNX_CLANG:-clang}"
flags=(--target=armv7-none-eabi -mfloat-abi=soft -Os -fPIC -ffreestanding -fno-stack-protector)
"$clang" "${flags[@]}" -DIDRIVE_HMI_TITLE_CACHE_LINK \
  -c "$script_dir/qnx-libc-link-stub.c" -o "$scratch/stub.o"
ld.lld -m armelf -shared -soname libc.so.3 -o "$scratch/stub.so" "$scratch/stub.o"
"$clang" "${flags[@]}" -Wall -Wextra -Werror -c "$script_dir/qnx-hmi-title-cache.c" -o "$scratch/probe.o"
ld.lld -m armelf -e _start --strip-all --dynamic-linker /usr/lib/ldqnx.so.2 \
  -o "$1" "$scratch/probe.o" "$scratch/stub.so"
