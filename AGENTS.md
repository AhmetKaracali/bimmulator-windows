# AGENTS.md — working on bimmulator-windows

Instructions for AI coding agents (and humans) changing or operating this repository.
Read [README.md](README.md) first for what the project does.

## What this is
A QEMU-based emulator that boots the real BMW NBT EVO head-unit software (QNX 6.5, HmiMain3D) for
**HU 006.027.001 / HMI ID5_1811** on Windows 11 via WSL2. Graphics: the guest's GLES2 calls are
forwarded over an RPC bridge to host ANGLE (Vulkan via Mesa lavapipe). Vehicle-side services are
simulated by Python processes in `vehicle-sim/`. Upstream: agent00jackson/bimmulator (macOS,
HU 007.030.001); history is preserved.

## Hard rules
1. **Never commit BMW software or anything extracted from it**: PSdZData, `*.bin`/`*.swfl`, IFS
   images, rootfs files, `HmiMain3D`, the cache (`~/.cache/idrive6`), captures, `hmi_layouts.json`,
   `helper_sizes.json`. `.gitignore` covers most of it — check `git status` before committing.
2. **Never commit personal vehicle data**: VINs, IDriveReader records, NCD coding backups, photos.
3. Do not copy code or data from herrbimmer/IDEmu (PolyForm Noncommercial, separate project). Using
   its documentation as a reference is fine.
4. Keep `nix/patches/**` GPL-2.0-or-later. New original files fall under PolyForm Noncommercial
   (see LICENSING.md).
5. Shell scripts and Python must keep **LF** line endings (`.gitattributes` enforces it); `.cmd`
   files use CRLF. Do not edit the scripts from a Windows editor that rewrites line endings.

## Environment
- Work inside WSL (Ubuntu, systemd on). Repository at `~/bimmulator-windows` by convention.
- All paths come from `wsl/env.sh` (`IDRIVE_HOME` = `~/idrive`, `IDRIVE_CACHE` = `~/.cache/idrive6`).
- Nix: `source /etc/profile.d/nix.sh` if `nix` is not on `PATH` (the scripts do this).
- When calling WSL from Windows tooling, put commands in a script file and run
  `wsl.exe -d Ubuntu -- bash /path/script.sh`; inline `bash -c` strings get `$` mangled by the
  Windows side.

## Common tasks
| Task | Command |
|---|---|
| One-time setup | `bash wsl/setup.sh ~/psdzdata` |
| Stage firmware only | `bash wsl/emulator.sh prepare` |
| First boot + snapshot | `bash wsl/emulator.sh snapshot` |
| Fast start | `bash wsl/emulator.sh fast` (run it in the background; it blocks until QEMU exits) |
| Rebuild overlay | `bash wsl/overlay.sh --language en-us [--car-coding X.ncd] [--plugins DIR]` |
| Keys / touch / screenshot | `bash wsl/control.sh key next press`, `tap X Y`, `shot out.png` |
| Stop everything | `bash wsl/control.sh stop` |
| Logs | `~/idrive/run.log`, per run `~/.cache/idrive6/runs/<RunID>/` (serial log, QMP socket) |
| Unit tests | `python3 -m unittest discover -s tests` |

After changing the launcher (`tools/idrive6-launch.py`), `run-emulator.sh`, the ANGLE server or
anything Nix builds, rebuild: `nix build .#default --out-link ~/idrive/launcher` (the launcher runs
a Nix-store copy of the source). Changes to the **guest GLES provider** (`tools/qnx-angle-egl-provider.c`)
live in the IFS: take a new `snapshot` before `fast` picks them up.

## Operating the emulator (lessons learned)
- Kill old `qemu-system-arm` / `angle-egl-rpc-server` before a new start (`emulator.sh` does).
- Step slowly: controller keys sent while a screen loads are dropped or doubled. Verify with a
  screenshot after each step instead of sending long key sequences.
- Main-menu tile positions shift; navigate by rotating, not by fixed tap coordinates.
- HMI restores its last screen at boot — an unexpected first screen is not a bug.
- `ioc_sim.py` hot-reloads `vehicle-sim/rules.py`; edit values there while the emulator runs.

## Where knowledge lives
- `vehicle-sim/NOTES.md` — MOST/NAL-SIPC/DSI protocol findings, vehicle value layouts.
- `vehicle-sim/TPM-RE.md` — tyre pressure monitor payloads.
- `NATIVE_GRAPHICS_CONTRACT.md`, `HMI_STARTUP_DEPENDENCY.md` — graphics bridge and HMI start-up.
- `tools/shaders/native-reconstructions/` — shader maps; `*-car006.json` are the maps pinned for
  HU 006.027.001 (`tools/make-car006-shader-maps.py` regenerates them from a staged rootfs,
  `tools/set-shader-map-source.py` repoints one entry, `tools/fix-packed-varyings.py` fixes SGX
  varying packing).
- `overlay/make_overlay.py` — documents the libhmicoding / libhmidb patch sites per firmware.

## Before you commit
- `git status` — no firmware, captures, NCDs, JSON generated from HmiMain3D.
- `python3 -m unittest discover -s tests` passes.
- Scripts still run from a fresh clone (no absolute personal paths; use `wsl/env.sh` variables).
