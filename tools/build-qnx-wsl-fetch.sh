#!/usr/bin/env bash
# WSL2 port: builds the guest-side overlay downloader (see qnx-wsl-fetch.c).
set -euo pipefail
if [[ $# != 1 ]]; then
  echo "Usage: $0 OUTPUT_EXECUTABLE" >&2
  exit 2
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
qnx_clang="${IDRIVE_QNX_CLANG:-clang}"
scratch="$(mktemp -d "${TMPDIR:-/tmp}/idrive-wsl-fetch.XXXXXX")"
trap 'rm -rf "$scratch"' EXIT
flags=(--target=armv7-none-eabi -mfloat-abi=soft -fPIC -ffreestanding -fno-stack-protector)
"$qnx_clang" "${flags[@]}" -c "$script_dir/qnx-wsl-fetch-link-stub.c" -o "$scratch/libc.o"
"$qnx_clang" "${flags[@]}" -DWSL_FETCH_LIBSOCKET -c "$script_dir/qnx-wsl-fetch-link-stub.c" -o "$scratch/libsocket.o"
ld.lld -m armelf -shared -soname libc.so.3 -o "$scratch/libc.so" "$scratch/libc.o"
ld.lld -m armelf -shared -soname libsocket.so.3 -o "$scratch/libsocket.so" "$scratch/libsocket.o"
"$qnx_clang" "${flags[@]}" -std=c11 -Wall -Wextra -c "$script_dir/qnx-wsl-fetch.c" -o "$scratch/fetch.o"
ld.lld -m armelf -e _start --dynamic-linker /usr/lib/ldqnx.so.2 \
  -o "$1" "$scratch/fetch.o" "$scratch/libsocket.so" "$scratch/libc.so"
echo "Built QNX WSL overlay downloader: $1"
