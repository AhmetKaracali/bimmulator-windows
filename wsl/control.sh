#!/usr/bin/env bash
# Drive the running emulator from a shell (also usable by scripts and AI agents).
#
#   wsl/control.sh key next next press        controller: next/prev (turn), left/right/up/down (tilt),
#                                              press, back, menu, option; wait:<s>; shot:<file.png>
#   wsl/control.sh tap 720 270 [x y ...]      touch the 1440x540 CID
#   wsl/control.sh shot screen.png            screenshot of the head-unit display
#   wsl/control.sh wait-frame screen.png [s]  wait (default 900 s) until the display is not black
#   wsl/control.sh stop                       stop what wsl/emulator.sh of this checkout started
#
# Step slowly: keys pressed while a screen is still loading can be dropped.
set -euo pipefail
source "$(dirname "$0")/env.sh"
CMD="${1:-}"; shift || true
case "$CMD" in
    key)  python3 "$REPO/wsl/key.py" "$(current_qmp)" "$@" ;;
    tap)  python3 "$REPO/wsl/tap.py" "$(current_qmp)" "$@" ;;
    shot) python3 "$REPO/wsl/screendump.py" "$(current_qmp)" "${1:-screen.png}" ;;
    wait-frame) python3 "$REPO/wsl/screendump.py" --wait "${2:-900}" "$(current_qmp)" "${1:-screen.png}" ;;
    stop) stop_tracked ;;
    *) sed -n '2,13p' "$0"; exit 2 ;;
esac
