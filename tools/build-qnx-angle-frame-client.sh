#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 2 ]]; then
  echo "Usage: $0 REALIZED_QNX_ROOT OUTPUT_EXECUTABLE" >&2
  exit 2
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$1"
output="$2"
qnx_clang="${IDRIVE_QNX_CLANG:-clang}"
if [[ ! -f "$root/lib/libsocket.so.3" ]]; then
  echo "The realized QNX runtime is missing $root/lib/libsocket.so.3" >&2
  exit 1
fi
for program in "$qnx_clang" ld.lld; do
  if ! command -v "$program" >/dev/null 2>&1; then
    echo "$program is missing; enter nix develop path:." >&2
    exit 1
  fi
done

scratch="$(mktemp -d "${TMPDIR:-/tmp}/idrive-angle-rpc-build.XXXXXX")"
trap 'rm -rf "$scratch"' EXIT
flags=(--target=armv7-none-eabi -mfloat-abi=soft -fPIC -ffreestanding -fno-stack-protector)
"$qnx_clang" "${flags[@]}" -I"$script_dir" -c \
  "$script_dir/qnx-angle-frame-client.c" -o "$scratch/client.o"
"$qnx_clang" "${flags[@]}" -c "$script_dir/qnx-libc-link-stub.c" \
  -o "$scratch/stub.o"
ld.lld -m armelf -shared -soname libc.so.3 -o "$scratch/stub.so" "$scratch/stub.o"
mkdir -p "$(dirname "$output")"
ld.lld -m armelf -e _start --dynamic-linker /usr/lib/ldqnx.so.2 \
  --allow-shlib-undefined -o "$output" "$scratch/client.o" \
  "$root/lib/libsocket.so.3" "$scratch/stub.so"
echo "Built QNX host-render RPC client: $output"
