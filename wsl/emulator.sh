#!/usr/bin/env bash
# Start the head-unit emulator (HU 006.027.001 / HMI ID5_1811) inside WSL2.
#
#   wsl/emulator.sh snapshot   first run: stage firmware, full boot (~7 min), save a pre-starter snapshot
#   wsl/emulator.sh fast       later runs: resume from that snapshot (first frame in ~2-3 min)
#   wsl/emulator.sh full       full boot without snapshot
#   wsl/emulator.sh otf        full boot and capture BMW's OTF trace stream into the run folder
#   wsl/emulator.sh prepare    only check and stage the firmware from PSdZData
#
# Environment:
#   SIM=0          do not start the host vehicle simulators (vehicle-sim/)
#   DIAG_RECORD=d  let diag_sim.py replay your own IDriveReader record instead of synthetic values
#   EXTRA="K=V .." additional emulator profile settings (IDRIVE_PROFILE_EXTRA_SETTINGS)
# The window opens through WSLg. Logs: $IDRIVE_HOME/run.log, run folders: $IDRIVE_CACHE/runs/.
set -u
source "$(dirname "$0")/env.sh"
MODE="${1:-fast}"
nix_env
[ -x "$LAUNCHER" ] || { echo "Launcher missing: run wsl/setup.sh first." >&2; exit 2; }
[ -f "$IDRIVE_CONFIG" ] || { echo "Config missing: $IDRIVE_CONFIG (wsl/setup.sh writes one)." >&2; exit 2; }

ICD=$(ls "$MESA_LINK"/share/vulkan/icd.d/lvp_icd.*.json 2>/dev/null | head -1)
export VK_DRIVER_FILES="${VK_DRIVER_FILES:-$ICD}"
export VK_ICD_FILENAMES="$VK_DRIVER_FILES"

cd "$REPO"   # the launcher uses the working directory as source root
if [ "$MODE" = "prepare" ]; then
    exec "$LAUNCHER" --config "$IDRIVE_CONFIG" --prepare-only
fi

# Stop leftovers of an earlier run (a second QEMU/ANGLE pair would fight over the ports).
pkill -f "[q]emu-system-arm" 2>/dev/null
pkill -f "[a]ngle-egl-rpc-server" 2>/dev/null

case "$MODE" in
    snapshot)
        mkdir -p "$(dirname "$STATE")"; rm -f "$STATE"
        export IDRIVE_ROOTFS_READY_HOLD_SECONDS=12 IDRIVE_QEMU_STATE_FILE="$STATE" ;;
    fast)
        [ -f "$STATE" ] || { echo "No snapshot yet: run 'wsl/emulator.sh snapshot' once." >&2; exit 2; }
        export IDRIVE_ROOTFS_READY_HOLD_SECONDS=12 IDRIVE_QEMU_STATE_FILE="$STATE" IDRIVE_QEMU_RESUME_VM=prestarter ;;
    full) ;;
    otf)
        EXTRA="${EXTRA:-} IDRIVE_OTF_CAPTURE=1 IDRIVE_OTF_CAPTURE_OUTPUT={run_dir}/otf.bin IDRIVE_OTF_CAPTURE_SERVER_LOG={run_dir}/otf-server.log"
        MODE=full ;;
    *) echo "usage: $0 snapshot|fast|full|otf|prepare" >&2; exit 2 ;;
esac

mkdir -p "$IDRIVE_HOME" "$OVERLAY_DIR"
: > "$RUN_LOG"
PIDS=()
cleanup() { kill "${PIDS[@]}" 2>/dev/null; }
trap cleanup EXIT

# overlay.tar (wsl/overlay.sh) is fetched by the guest right before HmiMain3D starts.
pkill -f "[h]ttp.server $OVERLAY_PORT" 2>/dev/null
python3 -m http.server "$OVERLAY_PORT" --bind 127.0.0.1 --directory "$OVERLAY_DIR" >/dev/null 2>&1 &
PIDS+=($!)

SETTINGS="${EXTRA:-}"
if [ "${SIM:-1}" = "1" ]; then
    SIMDIR="$REPO/vehicle-sim"
    pkill -f "[i]oc_sim.py" 2>/dev/null; pkill -f "[j]5_server.py" 2>/dev/null; pkill -f "[d]iag_sim.py" 2>/dev/null
    python3 "$SIMDIR/ioc_sim.py" --port "$IOC_PORT" --log "$IDRIVE_HOME/ioc.jsonl" > "$IDRIVE_HOME/ioc.out" 2>&1 &
    PIDS+=($!)
    python3 "$SIMDIR/j5_server.py" "$IDRIVE_HOME/j5.jsonl" > "$IDRIVE_HOME/j5.out" 2>&1 &
    PIDS+=($!)
    python3 "$SIMDIR/diag_sim.py" --port "$DIAG_PORT" ${DIAG_RECORD:+--record "$DIAG_RECORD"} > "$IDRIVE_HOME/diag_sim.out" 2>&1 &
    PIDS+=($!)
    SETTINGS="IDRIVE_MOST_SIPC_HOST_PORT=$IOC_PORT IDRIVE_MOST_TRACE_CONFIG=$SIMDIR/most.tp $SETTINGS"
fi
export IDRIVE_PROFILE_EXTRA_SETTINGS="$SETTINGS"

"$LAUNCHER" --config "$IDRIVE_CONFIG" >> "$RUN_LOG" 2>&1 &
RUNNER=$!
echo "Emulator starting ($MODE). Log: $RUN_LOG"

if [ "$MODE" != "full" ]; then
    RUN=""
    while [ -z "$RUN" ] && kill -0 "$RUNNER" 2>/dev/null; do
        RUN=$(grep -o "Run ID: [0-9TZ]*" "$RUN_LOG" 2>/dev/null | tail -1 | cut -d" " -f3)
        sleep 0.5
    done
    if [ -n "$RUN" ]; then
        if [ "$MODE" = "snapshot" ]; then
            python3 "$REPO/tools/wsl-snapshot.py" save "$IDRIVE_CACHE/runs/$RUN" prestarter | tee -a "$RUN_LOG"
        else
            python3 "$REPO/tools/wsl-snapshot.py" resume "$IDRIVE_CACHE/runs/$RUN" | tee -a "$RUN_LOG"
        fi
    fi
fi
wait "$RUNNER"
echo "RUN_EXIT=$?" >> "$RUN_LOG"
