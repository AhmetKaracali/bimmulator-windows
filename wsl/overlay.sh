#!/usr/bin/env bash
# Build $IDRIVE_HOME/overlay/overlay.tar. The guest downloads it right before HmiMain3D starts and
# unpacks it over its root volume, so nothing in the staged firmware or the snapshot changes.
#
#   wsl/overlay.sh [--language en-us|tr|de|...] [--car-coding hu_coding_backup.ncd] [--plugins DIR]
#
# Always included:
#   * libhmidb.so with the chosen start language (default en-us)
#   * the Jacinto MOST-server stand-in (tools/qnx-j5-bridge.c) + autostart hook; together with
#     vehicle-sim/ (started by wsl/emulator.sh) it makes "My Vehicle" and the vehicle values work
# Optional:
#   * --car-coding: your head unit's coding pages (IDriveReader NCD backup), emulator bits re-applied
#   * --plugins DIR: every sub-folder of DIR is copied to Plugins/<Name>/ (RA plug-ins)
#   * HERO=picture.png: 378x243 RGBA picture for the My Vehicle tile (F30)
#   * J5=0: leave the Jacinto bridge out (stock behaviour, empty My Vehicle)
# Re-run after every change; the next emulator start (also `fast`) picks it up.
set -euo pipefail
source "$(dirname "$0")/env.sh"
nix_env
[ -x "$LAUNCHER" ] || { echo "Launcher missing: run wsl/setup.sh first." >&2; exit 2; }
ROOTFS="$IDRIVE_CACHE/firmware/car-006_027_001-v1/firmware/rootfs"
[ -d "$ROOTFS" ] || { echo "Firmware not staged yet: run wsl/emulator.sh prepare (or snapshot) first." >&2; exit 2; }

mkdir -p "$OVERLAY_DIR"
OUT="$OVERLAY_DIR/overlay.tar"
python3 "$REPO/overlay/make_overlay.py" --firmware car006 --vehicle F30 -o "$OUT" "$@"

if [ "${J5:-1}" = "1" ]; then
    WORK="$IDRIVE_HOME/build/j5"; mkdir -p "$WORK"
    CLANG=$(grep -o 'IDRIVE_QNX_CLANG="[^"]*"' "$LAUNCHER" | cut -d'"' -f2)
    LLD=$(grep -o '/nix/store/[^:"]*-lld-[^:/"]*/bin' "$LAUNCHER" | head -1)
    PATH="$LLD:$PATH" IDRIVE_QNX_CLANG="$CLANG" bash "$REPO/tools/build-qnx-j5-bridge.sh" "$WORK/j5-bridge" >/dev/null
    STAGE="$WORK/stage"; rm -rf "$STAGE"; mkdir -p "$STAGE/opt/idrive"
    cp "$WORK/j5-bridge" "$STAGE/opt/idrive/j5-bridge"
    cat > "$STAGE/opt/idrive/autostart.sh" <<'SH'
#!/bin/ksh
# Emulator only: Jacinto MOSTSubSystemServer stand-in (host side: vehicle-sim/j5_server.py).
export LD_LIBRARY_PATH=/opt/sys/lib:/lib:/usr/lib:/opt/core/lib:/proc/boot
export SOCK=/idrive
/fs/sda0/opt/idrive/j5-bridge &
SH
    chmod 755 "$STAGE/opt/idrive/j5-bridge" "$STAGE/opt/idrive/autostart.sh"
    tar --owner=0 --group=0 --format=ustar -rf "$OUT" -C "$STAGE" opt/idrive/j5-bridge opt/idrive/autostart.sh
    echo "  + Jacinto MOST-server bridge (opt/idrive)"
fi

if [ -n "${HERO:-}" ]; then
    H="$IDRIVE_HOME/build/hero"; rm -rf "$H"
    D=opt/hmi/ID5/data/ro/bmw/id6l/assetDB/Domains/Main/Heroes/hero_myvehicle_F30
    mkdir -p "$H/$D" && cp "$HERO" "$H/$D/id6hero_f30.png"
    tar --owner=0 --group=0 --format=ustar -rf "$OUT" -C "$H" "$D/id6hero_f30.png"
    echo "  + My Vehicle picture ($HERO)"
fi
echo "-> $OUT"
