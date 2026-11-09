#!/usr/bin/env bash
# WSL2 port: builds the guest-side Jacinto MOST-server bridge (see qnx-j5-bridge.c).
set -euo pipefail
if [[ $# != 1 ]]; then echo "Usage: $0 OUTPUT_EXECUTABLE" >&2; exit 2; fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
qnx_clang="${IDRIVE_QNX_CLANG:-clang}"
scratch="$(mktemp -d "${TMPDIR:-/tmp}/idrive-j5-bridge.XXXXXX")"
trap 'rm -rf "$scratch"' EXIT
flags=(--target=armv7-none-eabi -mfloat-abi=soft -fPIC -ffreestanding -fno-stack-protector -fno-builtin)
stub="$script_dir/qnx-j5-bridge-link-stub.c"
"$qnx_clang" "${flags[@]}" -c "$stub" -o "$scratch/libc.o"
"$qnx_clang" "${flags[@]}" -DJ5_LIBSOCKET -c "$stub" -o "$scratch/libsocket.o"
"$qnx_clang" "${flags[@]}" -DJ5_LIBDSI -c "$stub" -o "$scratch/libdsi.o"
ld.lld -m armelf -shared -soname libc.so.3 -o "$scratch/libc.so" "$scratch/libc.o"
ld.lld -m armelf -shared -soname libsocket.so.3 -o "$scratch/libsocket.so" "$scratch/libsocket.o"
ld.lld -m armelf -shared -soname libsys_dsi_base.cpp-ne.so.4 -o "$scratch/libdsi.so" "$scratch/libdsi.o"
"$qnx_clang" "${flags[@]}" -std=c11 -Wall -Wextra -O1 -c "$script_dir/qnx-j5-bridge.c" -o "$scratch/bridge.o"
ld.lld -m armelf -e _start --dynamic-linker /usr/lib/ldqnx.so.2 -rpath /opt/sys/lib \
  -o "$1" "$scratch/bridge.o" "$scratch/libdsi.so" "$scratch/libsocket.so" "$scratch/libc.so"
echo "Built QNX Jacinto MOST-server bridge: $1"
