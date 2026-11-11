# Shared settings for the WSL2 helper scripts. Sourced, never run directly.
# Every value can be overridden from the environment before calling a script.

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IDRIVE_HOME="${IDRIVE_HOME:-$HOME/idrive}"            # launcher links, overlay, logs, pid files
IDRIVE_CACHE="${IDRIVE_CACHE:-$HOME/.cache/idrive6}"  # must equal the launcher's cacheDir (default)
IDRIVE_CONFIG="${IDRIVE_CONFIG:-$REPO/idrive6.toml}"
LAUNCHER="$IDRIVE_HOME/launcher/bin/idrive6"
MESA_LINK="$IDRIVE_HOME/mesa"
OVERLAY_DIR="$IDRIVE_HOME/overlay"
RUN_LOG="$IDRIVE_HOME/run.log"
PID_DIR="$IDRIVE_HOME/pids"   # processes started by these scripts (stop only touches these)
OVERLAY_PORT="${OVERLAY_PORT:-41600}"  # the guest fetches overlay.tar from this host port
IOC_PORT="${IOC_PORT:-8766}"           # vehicle-sim/ioc_sim.py  (Jacinto-side MOST link, NAL-SIPC)
DIAG_PORT="${DIAG_PORT:-6801}"         # vehicle-sim/diag_sim.py (HSFZ gateway, guest 160.48.199.253)
export IDRIVE_HOME IDRIVE_CACHE

nix_env() {
    # shellcheck disable=SC1091
    if ! command -v nix >/dev/null 2>&1; then
        source /etc/profile.d/nix.sh 2>/dev/null ||
            source /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh 2>/dev/null || true
    fi
}

# Build id (builds/<id>): $IDRIVE_BUILD_ID, `build = ".."` in the config, the last detected one,
# or detected from the PSdZData packages named in the config.
current_build_id() {
    if [ -n "${IDRIVE_BUILD_ID:-}" ]; then echo "$IDRIVE_BUILD_ID"; return; fi
    local forced psdz
    forced=$(sed -n 's/^[[:space:]]*build[[:space:]]*=[[:space:]]*"\(.*\)".*/\1/p' "$IDRIVE_CONFIG" 2>/dev/null | head -1)
    if [ -n "$forced" ]; then echo "$forced"; return; fi
    if [ -s "$IDRIVE_HOME/build-id" ]; then cat "$IDRIVE_HOME/build-id"; return; fi
    psdz=$(sed -n 's/^[[:space:]]*psdzdata[[:space:]]*=[[:space:]]*"\(.*\)".*/\1/p' "$IDRIVE_CONFIG" 2>/dev/null | head -1)
    [ -n "$psdz" ] || { echo "psdzdata missing in $IDRIVE_CONFIG" >&2; return 1; }
    mkdir -p "$IDRIVE_HOME"
    python3 "$REPO/tools/buildinfo.py" detect "$psdz" | tee "$IDRIVE_HOME/build-id"
}

build_value() {  # build_value <id> <key>   (top-level string value of build.json)
    python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$REPO/builds/$1/build.json" "$2"
}

# QMP socket of the newest emulator run (for key.py / tap.py / screendump.py).
current_qmp() {
    local run
    run=$(grep -o "Run ID: [0-9TZ]*" "$RUN_LOG" 2>/dev/null | tail -1 | cut -d" " -f3)
    [ -n "$run" ] || { echo "no running emulator (no Run ID in $RUN_LOG)" >&2; return 1; }
    echo "$IDRIVE_CACHE/runs/$run/qmp.sock"
}

# Start a background process in its own process group and remember it under $PID_DIR/<name>.
start_tracked() {  # start_tracked <name> <logfile> <command...>
    local name=$1 log=$2; shift 2
    mkdir -p "$PID_DIR"
    setsid "$@" > "$log" 2>&1 < /dev/null &
    echo $! > "$PID_DIR/$name"
}

# Stop the process groups this checkout started (never other emulator instances).
stop_tracked() {
    local f pid
    for f in "$PID_DIR"/*; do
        [ -f "$f" ] || continue
        pid=$(cat "$f")
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null
        fi
        rm -f "$f"
    done
}

as_root() { if [ "$(id -u)" -eq 0 ]; then "$@"; else sudo "$@"; fi; }
