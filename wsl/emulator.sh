#!/usr/bin/env bash
# Start the head-unit emulator inside WSL2. The firmware build (builds/<id>) is detected from the
# PSdZData packages in idrive6.toml (or forced with `build = "<id>"` there / IDRIVE_BUILD_ID).
#
#   wsl/emulator.sh snapshot   first run of a build: stage firmware, full boot (~7 min), save a snapshot
#   wsl/emulator.sh fast       later runs: resume from that snapshot (first frame after a few minutes)
#   wsl/emulator.sh full       full boot without snapshot
#   wsl/emulator.sh otf        full boot and capture BMW's OTF trace stream into the run folder
#   wsl/emulator.sh prepare    only verify and stage the firmware from PSdZData
#
# Environment:
#   SIM=0          do not start the host vehicle simulators (vehicle-sim/)
#   DIAG_RECORD=d  diag_sim.py replays your own IDriveReader record instead of synthetic values
#   EXTRA="K=V .." additional emulator profile settings (IDRIVE_PROFILE_EXTRA_SETTINGS)
# The window opens through WSLg. Logs: $IDRIVE_HOME/run.log, run folders: $IDRIVE_CACHE/runs/.
# Only processes started by these scripts are stopped (other emulator instances are left alone).
set -u
source "$(dirname "$0")/env.sh"
MODE="${1:-fast}"
nix_env
[ -x "$LAUNCHER" ] || { echo "Launcher missing: run wsl/setup.sh first." >&2; exit 2; }
[ -f "$IDRIVE_CONFIG" ] || { echo "Config missing: $IDRIVE_CONFIG (wsl/setup.sh writes one)." >&2; exit 2; }
mkdir -p "$IDRIVE_HOME" "$OVERLAY_DIR"

ICD=$(ls "$MESA_LINK"/share/vulkan/icd.d/lvp_icd.*.json 2>/dev/null | head -1)
export VK_DRIVER_FILES="${VK_DRIVER_FILES:-$ICD}"
export VK_ICD_FILENAMES="$VK_DRIVER_FILES"

cd "$REPO"   # the launcher uses the working directory as source root
if [ "$MODE" = "prepare" ]; then
    rm -f "$IDRIVE_HOME/build-id"
    BUILD=$(current_build_id) || exit 2
    echo "Build: $BUILD"
    exec "$LAUNCHER" --config "$IDRIVE_CONFIG" --prepare-only
fi
BUILD=$(current_build_id) || exit 2
STATE="$IDRIVE_CACHE/state/prestarter-$BUILD.qcow2"

stop_tracked   # leftovers of an earlier run of this checkout
case "$MODE" in
    snapshot)
        mkdir -p "$(dirname "$STATE")"; rm -f "$STATE"
        export IDRIVE_ROOTFS_READY_HOLD_SECONDS=12 IDRIVE_QEMU_STATE_FILE="$STATE" ;;
    fast)
        [ -f "$STATE" ] || { echo "No snapshot for $BUILD yet: run 'wsl/emulator.sh snapshot' once." >&2; exit 2; }
        export IDRIVE_ROOTFS_READY_HOLD_SECONDS=12 IDRIVE_QEMU_STATE_FILE="$STATE" IDRIVE_QEMU_RESUME_VM=prestarter ;;
    full) ;;
    otf)
        EXTRA="${EXTRA:-} IDRIVE_OTF_CAPTURE=1 IDRIVE_OTF_CAPTURE_OUTPUT={run_dir}/otf.bin IDRIVE_OTF_CAPTURE_SERVER_LOG={run_dir}/otf-server.log"
        MODE=full ;;
    *) echo "usage: $0 snapshot|fast|full|otf|prepare" >&2; exit 2 ;;
esac

: > "$RUN_LOG"
trap stop_tracked EXIT

# overlay.tar (wsl/overlay.sh) is fetched by the guest right before HmiMain3D starts.
start_tracked overlay-http "$IDRIVE_HOME/overlay-http.out" \
    python3 -m http.server "$OVERLAY_PORT" --bind 127.0.0.1 --directory "$OVERLAY_DIR"

SETTINGS="${EXTRA:-}"
if [ "${SIM:-1}" = "1" ]; then
    SIMDIR="$REPO/vehicle-sim"
    start_tracked ioc-sim "$IDRIVE_HOME/ioc.out" python3 "$SIMDIR/ioc_sim.py" --port "$IOC_PORT" --log "$IDRIVE_HOME/ioc.jsonl"
    start_tracked j5-server "$IDRIVE_HOME/j5.out" python3 "$SIMDIR/j5_server.py" "$IDRIVE_HOME/j5.jsonl"
    start_tracked diag-sim "$IDRIVE_HOME/diag_sim.out" python3 "$SIMDIR/diag_sim.py" --port "$DIAG_PORT" \
        ${DIAG_RECORD:+--record "$DIAG_RECORD"}
    SETTINGS="IDRIVE_MOST_SIPC_HOST_PORT=$IOC_PORT IDRIVE_MOST_TRACE_CONFIG=$SIMDIR/most.tp $SETTINGS"
    sleep 1
    for name in ioc-sim j5-server diag-sim; do
        kill -0 "$(cat "$PID_DIR/$name")" 2>/dev/null || {
            echo "$name did not start (port in use by another instance?): see $IDRIVE_HOME/*.out" >&2; exit 1; }
    done
fi
export IDRIVE_PROFILE_EXTRA_SETTINGS="$SETTINGS"

start_tracked emulator "$RUN_LOG" "$LAUNCHER" --config "$IDRIVE_CONFIG"
RUNNER=$(cat "$PID_DIR/emulator")
echo "Emulator starting: build $BUILD, mode $MODE. Log: $RUN_LOG"

if [ "$MODE" != "full" ]; then
    RUN=""
    while [ -z "$RUN" ] && kill -0 "$RUNNER" 2>/dev/null; do
        RUN=$(grep -o "Run ID: [0-9TZ]*" "$RUN_LOG" 2>/dev/null | tail -1 | cut -d" " -f3)
        sleep 0.5
    done
    if [ -n "$RUN" ]; then
        if [ "$MODE" = "snapshot" ]; then
            python3 "$REPO/tools/wsl-snapshot.py" save "$IDRIVE_CACHE/runs/$RUN" prestarter | tee -a "$IDRIVE_HOME/snapshot.log"
        else
            python3 "$REPO/tools/wsl-snapshot.py" resume "$IDRIVE_CACHE/runs/$RUN" | tee -a "$IDRIVE_HOME/snapshot.log"
        fi
    fi
fi
wait "$RUNNER"
echo "RUN_EXIT=$?" >> "$IDRIVE_HOME/snapshot.log"
