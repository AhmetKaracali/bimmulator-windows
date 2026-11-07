#!/usr/bin/env bash
set -euo pipefail

mode="${3:-}"
if [[ $# -lt 2 || $# -gt 3 ||
      ( -n "$mode" && "$mode" != "--finalize" && "$mode" != "--finalize-batch" ) ]]; then
  echo "Usage: $0 STAGED_ROOT OUTPUT_EXECUTABLE [--finalize|--finalize-batch]" >&2
  exit 2
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$1"
output="$2"
vertex="${IDRIVE_SHADER_PROBE_VERTEX:-$root/opt/hmi/ID5/data/ro/common/widgetasset/cover/shaders/mat_cover_bg.vert.shd}"
fragment="${IDRIVE_SHADER_PROBE_FRAGMENT:-$root/opt/hmi/ID5/data/ro/common/widgetasset/cover/shaders/mat_cover_bg.frag.shd}"
probe_source="$script_dir/qnx-shader-parser-probe.c"
if [[ "$mode" == "--finalize" ]]; then
  probe_source="$script_dir/qnx-shader-finalizer-probe.c"
elif [[ "$mode" == "--finalize-batch" ]]; then
  probe_source="$script_dir/qnx-shader-finalizer-batch-probe.c"
fi
driver="$root/lib/graphics/omap5430_ES2_0/libImgGLESv2.so"
if [[ "$mode" == "--finalize-batch" ]]; then
  if [[ -z "${IDRIVE_SHADER_PROBE_BATCH_MANIFEST:-}" ||
        ! -f "$IDRIVE_SHADER_PROBE_BATCH_MANIFEST" ]]; then
    echo "--finalize-batch requires IDRIVE_SHADER_PROBE_BATCH_MANIFEST." >&2
    exit 2
  fi
  python3 - "$driver" "$root" "$IDRIVE_SHADER_PROBE_BATCH_MANIFEST" <<'PY'
import hashlib, json, sys
from pathlib import Path
driver, root, manifest = map(Path, sys.argv[1:])
if hashlib.sha256(driver.read_bytes()).hexdigest() != 'd4776fc2f6cf01668ca21b326338960e14b6d69510ca2f0e6b37cf72269ccf69':
    raise SystemExit('The UniPatch function ABI has not been verified for this driver')
data_root = root / 'opt/hmi/ID5/data/ro'
entries = json.loads(manifest.read_text()).get('inputs', [])
if not entries:
    raise SystemExit('batch manifest contains no inputs')
for entry in entries:
    if entry.get('stage') not in ('vertex', 'fragment'):
        raise SystemExit(f"batch entry has no supported shader stage: {entry.get('name')}")
    asset = data_root / entry['path']
    if not asset.is_file() or hashlib.sha256(asset.read_bytes()).hexdigest() != entry['sha256']:
        raise SystemExit(f"shader input does not match its manifest hash: {asset}")
PY
else
  for file in "$driver" "$vertex" "$fragment"; do
  if [[ ! -f "$file" ]]; then
    echo "The staged root is missing $file" >&2
    exit 1
  fi
  done
fi
if [[ "$mode" == "--finalize" ]]; then
  python3 - "$driver" <<'PY'
import hashlib, sys
from pathlib import Path
if hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest() != 'd4776fc2f6cf01668ca21b326338960e14b6d69510ca2f0e6b37cf72269ccf69':
    raise SystemExit('The UniPatch function ABI has not been verified for this driver')
PY
fi
qnx_clang="${IDRIVE_QNX_CLANG:-clang}"
for program in "$qnx_clang" ld.lld python3; do
  if ! command -v "$program" >/dev/null 2>&1; then
    echo "$program is missing; enter the Nix development shell." >&2
    exit 1
  fi
done

scratch="$(mktemp -d "${TMPDIR:-/tmp}/idrive-shader-probe.XXXXXX")"
trap 'rm -rf "$scratch"' EXIT
if [[ "$mode" == "--finalize-batch" ]]; then
  python3 - "$root" "$IDRIVE_SHADER_PROBE_BATCH_MANIFEST" "$scratch/shader-payloads.c" <<'PY'
from pathlib import Path
import hashlib, json, sys

root, manifest, output = map(Path, sys.argv[1:])
data_root = root / 'opt/hmi/ID5/data/ro'
entries = json.loads(manifest.read_text())['inputs']
chunks = ['#include <stdint.h>\n']
rows = []
for index, entry in enumerate(entries):
    data = (data_root / entry['path']).read_bytes()
    if hashlib.sha256(data).hexdigest() != entry['sha256']:
        raise SystemExit(f"hash mismatch while embedding {entry['path']}")
    symbol = f'shader_batch_{index:04d}'
    rows.extend('    ' + ', '.join(f'0x{byte:02x}' for byte in data[start:start + 12])
                for start in range(0, len(data), 12))
    chunks.append(f'const uint8_t {symbol}[] = {{\n' + ',\n'.join(rows) + '\n};\n')
    chunks.append(f'const uint32_t {symbol}_size = {len(data)}u;\n')
    rows = []
chunks.append('typedef struct { const char *name; const uint8_t *bytes; uint32_t size; uint32_t vertex; } batch_shader;\n')
chunks.append('const batch_shader shader_batch[] = {\n')
for index, entry in enumerate(entries):
    symbol = f'shader_batch_{index:04d}'
    vertex = 1 if entry['stage'] == 'vertex' else 0
    chunks.append(f'    {{ {json.dumps(entry["name"])}, {symbol}, {symbol}_size, {vertex}u }},\n')
chunks.append('};\n')
chunks.append(f'const uint32_t shader_batch_count = {len(entries)}u;\n')
output.write_text(''.join(chunks), encoding='ascii')
PY
else
python3 - "$vertex" "$fragment" "$scratch/shader-payloads.c" <<'PY'
from pathlib import Path
import sys

vertex, fragment, output = map(Path, sys.argv[1:])

def emit(name: str, path: Path) -> str:
    data = path.read_bytes()
    payload_ranges = []
    first_length = int.from_bytes(data[68:72], "big")
    first_offset = 72
    payload_ranges.append((first_offset, first_length))
    next_length_offset = first_offset + first_length
    if next_length_offset + 4 <= len(data):
        next_length = int.from_bytes(data[next_length_offset:next_length_offset + 4], "big")
        next_offset = next_length_offset + 4
        if next_length and next_offset + next_length <= len(data):
            payload_ranges.append((next_offset, next_length))
    rows = []
    for start in range(0, len(data), 12):
        rows.append("    " + ", ".join(f"0x{byte:02x}" for byte in data[start:start + 12]))
    result = (
        f"const uint8_t shader_{name}[] = {{\n" + ",\n".join(rows) +
        f"\n}};\nconst uint32_t shader_{name}_size = {len(data)}u;\n"
    )
    for index in range(2):
        offset, size = payload_ranges[index] if index < len(payload_ranges) else (0, 0)
        result += (
            f"const uint32_t shader_{name}_payload{index}_offset = {offset}u;\n"
            f"const uint32_t shader_{name}_payload{index}_size = {size}u;\n"
        )
    return result

output.write_text(
    "#include <stdint.h>\n" + emit("vertex", vertex) + emit("fragment", fragment),
    encoding="ascii",
)
PY
fi

flags=(--target=armv7-none-eabi -mfloat-abi=soft -fPIC -ffreestanding
       -fno-stack-protector -fno-builtin)
"$qnx_clang" "${flags[@]}" -c "$script_dir/qnx-libc-link-stub.c" -o "$scratch/stub.o"
ld.lld -m armelf -shared -soname libc.so.3 -o "$scratch/stub.so" "$scratch/stub.o"
if [[ "$mode" == "--finalize-batch" ]]; then
  flags+=( -ffunction-sections -fdata-sections )
fi
"$qnx_clang" "${flags[@]}" -c "$probe_source" -o "$scratch/probe.o"
"$qnx_clang" "${flags[@]}" -c "$scratch/shader-payloads.c" -o "$scratch/shaders.o"
mkdir -p "$(dirname "$output")"
ld_flags=(-m armelf -e _start --dynamic-linker /usr/lib/ldqnx.so.2)
if [[ "$mode" == "--finalize-batch" ]]; then
  ld_flags+=( --gc-sections )
fi
ld.lld "${ld_flags[@]}" \
  --allow-shlib-undefined -o "$output" "$scratch/probe.o" \
  "$scratch/shaders.o" -L"$(dirname "$driver")" -lImgGLESv2 "$scratch/stub.so"
echo "Built QNX authentic shader probe${mode:+ ($mode)}: $output"

