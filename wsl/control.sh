#!/usr/bin/env bash
# Drive the running emulator from a shell (also usable by scripts and AI agents).
#
#   wsl/control.sh key next next press        controller: next/prev (turn), left/right/up/down (tilt),
#                                              press, back, menu, option; wait:<s>; shot:<file.png>
#   wsl/control.sh tap 720 270 [x y ...]      touch the 1440x540 CID
#   wsl/control.sh shot screen.png            screenshot of the head-unit display
#   wsl/control.sh stop                       stop QEMU, ANGLE server and the simulators
#
# Step slowly: keys pressed while a screen is still loading can be dropped.
set -euo pipefail
source "$(dirname "$0")/env.sh"
CMD="${1:-}"; shift || true
case "$CMD" in
    key)  python3 "$REPO/wsl/key.py" "$(current_qmp)" "$@" ;;
    tap)  python3 "$REPO/wsl/tap.py" "$(current_qmp)" "$@" ;;
    shot) python3 "$REPO/wsl/screendump.py" "$(current_qmp)" "${1:-screen.png}" ;;
    stop)
        pkill -f "[q]emu-system-arm" || true
        pkill -f "[a]ngle-egl-rpc-server" || true
        pkill -f "[i]oc_sim.py" || true; pkill -f "[j]5_server.py" || true; pkill -f "[d]iag_sim.py" || true
        pkill -f "[h]ttp.server $OVERLAY_PORT" || true ;;
    *) sed -n '2,12p' "$0"; exit 2 ;;
esac
