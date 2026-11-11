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
# Build-specific HmiMain3D addresses (builds/<id>/build.json "controller", $IDRIVE_BUILD).
mapfile -t defines < <(python3 - "$script_dir" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
import buildinfo
c = buildinfo.current_build()["controller"]
names = {"app_vtable": "HMI_APP_VTABLE", "event_vtable": "HMI_EVENT_VTABLE",
         "allocate_event": "HMI_ALLOCATE_EVENT", "get_display_service_cache": "HMI_GET_DISPLAY_SERVICE_CACHE",
         "display_service_vtable": "HMI_DISPLAY_SERVICE_VTABLE", "enable_display": "HMI_ENABLE_DISPLAY",
         "interaction_slot_function": "HMI_INTERACTION_SLOT_FUNCTION"}
for key, macro in names.items():
    print(f"-D{macro}={buildinfo.hexint(c[key]):#010x}u")
for i, caller in enumerate(c["pop_callers"], 1):
    print(f"-DHMI_POP_CALLER_{i}={buildinfo.hexint(caller):#010x}u")
PY
)
"$clang" "${flags[@]}" -std=c11 -Wall -Wextra -Werror "${defines[@]}" \
  -c "$script_dir/qnx-hmi-controller.c" -o "$scratch/controller.o"
"$clang" "${flags[@]}" -c "$script_dir/qnx-libc-link-stub.c" -o "$scratch/libc.o"
ld.lld -m armelf -shared -soname libc.so.3 -o "$scratch/libc.so" "$scratch/libc.o"
ld.lld -m armelf -shared -soname libidrive-hmi-controller.so \
  --allow-shlib-undefined -o "$1" "$scratch/controller.o" "$scratch/libc.so"
echo "Built QNX HMI controller bridge: $1"
