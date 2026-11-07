#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 2 ]]; then
  echo "Usage: $0 STAGED_ROOT OUTPUT_LIBRARY" >&2
  exit 2
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$1"
output="$2"
vendor="$root/lib/graphics/omap5430_ES2_0/libIMGegl.so"
[[ -f "$vendor" ]] || { echo "Missing staged vendor EGL library: $vendor" >&2; exit 1; }
python3 - "$root" <<'PY'
import hashlib, sys
from pathlib import Path
root = Path(sys.argv[1])
expected = {
    'lib/libEGL.so.1': '54ad4bb53ef21d9b4ca61aacccd10749e0b1c897d4388132deef26661e6e6e24',
    'lib/graphics/omap5430_ES2_0/libIMGegl.so': '9dc7179f7515f63b2ff9c5422c8292af73c3263bcc0a3d85ce15ca181f10f762',
}
for name, digest in expected.items():
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
        raise SystemExit(f'Unverified EGL provider ABI in {name}; inspect this version before tracing it')
PY
qnx_clang="${IDRIVE_QNX_CLANG:-clang}"
scratch="$(mktemp -d "${TMPDIR:-/tmp}/idrive-egl-trace.XXXXXX")"
trap 'rm -rf "$scratch"' EXIT
flags=(--target=armv7-none-eabi -mfloat-abi=soft -fPIC -ffreestanding -fno-stack-protector)
"$qnx_clang" "${flags[@]}" -c "$script_dir/qnx-libc-link-stub.c" -o "$scratch/stub.o"
ld.lld -m armelf -shared -soname libc.so.3 -o "$scratch/stub.so" "$scratch/stub.o"
"$qnx_clang" "${flags[@]}" -O1 -c "$script_dir/qnx-egl-provider-trace.c" -o "$scratch/trace.o"
mkdir -p "$(dirname "$output")"
ld.lld -m armelf -shared -soname libidriveegltrace.so --allow-shlib-undefined \
  -o "$output" "$scratch/trace.o" "$vendor" "$scratch/stub.so"
echo "Built QNX EGL provider tracer: $output"
