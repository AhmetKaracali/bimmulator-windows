# Shared settings for the WSL2 helper scripts. Sourced, never run directly.
# Every value can be overridden from the environment before calling a script.

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IDRIVE_HOME="${IDRIVE_HOME:-$HOME/idrive}"            # launcher links, overlay, logs, flag files
IDRIVE_CACHE="${IDRIVE_CACHE:-$HOME/.cache/idrive6}"  # must equal the launcher's cacheDir (default)
IDRIVE_CONFIG="${IDRIVE_CONFIG:-$REPO/idrive6.toml}"
LAUNCHER="$IDRIVE_HOME/launcher/bin/idrive6"
MESA_LINK="$IDRIVE_HOME/mesa"
OVERLAY_DIR="$IDRIVE_HOME/overlay"
RUN_LOG="$IDRIVE_HOME/run.log"
STATE="$IDRIVE_CACHE/state/prestarter-car006027.qcow2"
OVERLAY_PORT=41600          # the guest fetches overlay.tar from this host port before HmiMain3D
IOC_PORT=8766               # vehicle-sim/ioc_sim.py   (MOST link of the Jacinto side, NAL-SIPC)
DIAG_PORT=6801              # vehicle-sim/diag_sim.py  (HSFZ diagnostic gateway, guest 160.48.199.253)
export IDRIVE_HOME IDRIVE_CACHE

nix_env() {
    # shellcheck disable=SC1091
    if ! command -v nix >/dev/null 2>&1; then
        source /etc/profile.d/nix.sh 2>/dev/null ||
            source /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh 2>/dev/null || true
    fi
}

# QMP socket of the newest emulator run (for key.py / tap.py / screendump.py).
current_qmp() {
    local run
    run=$(grep -o "Run ID: [0-9TZ]*" "$RUN_LOG" 2>/dev/null | tail -1 | cut -d" " -f3)
    [ -n "$run" ] || { echo "no running emulator (no Run ID in $RUN_LOG)" >&2; return 1; }
    echo "$IDRIVE_CACHE/runs/$run/qmp.sock"
}

as_root() { if [ "$(id -u)" -eq 0 ]; then "$@"; else sudo "$@"; fi; }
