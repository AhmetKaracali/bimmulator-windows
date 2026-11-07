#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOTFS="${1:-$SCRIPT_DIR/build/idrive6-cache/rootfs-x20511i}"
SMOKE="${2:-$SCRIPT_DIR/build/idrive6-cache/angle-host-smoke}"
CACHE_DIR="$SCRIPT_DIR/build/idrive6-cache"
MANIFEST="$SCRIPT_DIR/tools/shaders/native-reconstructions/hmi-vertex-map.json"

if [[ ! -d "$ROOTFS/opt/hmi/ID5/data/ro" ]]; then
  echo "Missing realized BMW HMI assets under $ROOTFS/opt/hmi/ID5/data/ro." >&2
  exit 1
fi

mkdir -p "$CACHE_DIR"
if [[ ! -x "$SMOKE" ]]; then
  "$SCRIPT_DIR/tools/build-angle-host-smoke.sh" "$SMOKE"
fi

MAP_LIST="$(mktemp "$CACHE_DIR/hmi-native-essl-maps.XXXXXX")"
FRAGMENT_100="$(mktemp "$CACHE_DIR/hmi-native-essl-fragment100.XXXXXX")"
FRAGMENT_300="$(mktemp "$CACHE_DIR/hmi-native-essl-fragment300.XXXXXX")"
trap 'rm -f "$MAP_LIST" "$FRAGMENT_100" "$FRAGMENT_300"' EXIT
python3 "$SCRIPT_DIR/tools/prepare-hmi-native-essl-map.py" \
  "$MANIFEST" "$ROOTFS" "$SCRIPT_DIR" > "$MAP_LIST"
cat > "$FRAGMENT_100" <<'GLSL'
precision mediump float;
void main() { gl_FragColor = vec4(1.0); }
GLSL
cat > "$FRAGMENT_300" <<'GLSL'
#version 300 es
precision mediump float;
out vec4 smokeColor;
void main() { smokeColor = vec4(1.0); }
GLSL

while IFS=$'\t' read -r native_shader host_source; do
  [[ -n "$native_shader" && -n "$host_source" ]] || continue
  fragment="$FRAGMENT_100"
  if grep -q '^#version 300 es$' "$host_source"; then
    fragment="$FRAGMENT_300"
  fi
  IDRIVE_ANGLE_GLES_VERSION=3 IDRIVE_ANGLE_SMOKE_COMPILE_ONLY=1 \
    "$SMOKE" "$host_source" "$fragment"
done < "$MAP_LIST"
