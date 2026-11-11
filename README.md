# bimmulator-windows

Run the **real BMW NBT EVO iDrive 6 head-unit software** (QNX 6.5 + HmiMain3D) on a **Windows 11
PC** through WSL2, QEMU and ANGLE. This is the Windows/WSL2 port of
[agent00jackson/bimmulator](https://github.com/agent00jackson/bimmulator) (see Credits), extended
so that the head unit build **HU 006.027.001 / HMI ID5_1811** (F30 3 Series, PSdZData 4.15.12) boots
with a working *My Vehicle* menu, vehicle values and a diagnostic gateway simulator.

> **No BMW software is included.** You need your own extracted PSdZData. This project is not
> affiliated with or endorsed by BMW AG. "BMW", "iDrive" and related names are BMW trademarks.

![status](https://img.shields.io/badge/host-Windows%2011%20%2B%20WSL2-blue) ![license](https://img.shields.io/badge/license-PolyForm%20Noncommercial-orange)

## What works

| Area | State |
|---|---|
| QNX boot, HmiMain3D, ID6 Light home screen and main menu | works |
| Rendering (host ANGLE over Mesa lavapipe, SGX shader reconstructions incl. lists, cursor, 3D F30 car model) | works, software rendering (slow but usable) |
| CID touch (mouse) and iDrive controller (keyboard) | works |
| Snapshot fast start (skip QNX boot) | works, ~2-3 min to first frame |
| *My Vehicle*, vehicle settings, Onboard info, Sport displays, tyre pressure, clock | works with the bundled vehicle simulators (`vehicle-sim/`) |
| Start language (35 languages in `text.db`, e.g. `en-us`, `tr`, `de`) | via `wsl/overlay.sh --language` |
| Your own car's head-unit coding (NCD) | via `wsl/overlay.sh --car-coding` |
| Native RA plug-ins (own apps under *My Vehicle*) | via `wsl/overlay.sh --plugins` |
| HSFZ diagnostic gateway on TCP 6801 for plug-ins (synthetic engine or replay of your own capture) | `vehicle-sim/diag_sim.py` |
| Navigation, media, phone audio, real CAN/MOST bus | not emulated |

## Requirements

- Windows 11 (WSLg shows the emulator window), WSL2 with **Ubuntu** and **systemd enabled**
- 16 GB RAM recommended, ~25 GB free disk inside WSL, a fast CPU (graphics run in software)
- Extracted **PSdZData** containing `swe/swfl/swfl_00002719.bin.006_027_001`,
  `swfl_0000271a.bin.006_027_001`, `swfl_00002720.bin.006_027_001` (NBT EVO, I-level F020-18-11,
  PSdZData 4.15.12). The launcher verifies their SHA-256 before use.

## Quick start

**1. WSL2 + Ubuntu** (PowerShell as administrator, once):

```powershell
wsl --install -d Ubuntu
```

Inside Ubuntu, enable systemd and restart WSL:

```bash
printf '[boot]\nsystemd=true\n' | sudo tee /etc/wsl.conf
```

```powershell
wsl --shutdown
```

**2. Clone inside WSL** (not on `C:\` — speed and line endings):

```bash
git clone https://github.com/AhmetKaracali/bimmulator-windows ~/bimmulator-windows
cd ~/bimmulator-windows
```

**3. Copy PSdZData into WSL and run the setup** (installs Nix, builds the patched QEMU and the ANGLE
server; the first build takes 30-90 minutes):

```bash
mkdir -p ~/psdzdata/swe/swfl
cp /mnt/c/path/to/psdzdata/swe/swfl/swfl_0000271{9,a}.bin.006_027_001 /mnt/c/path/to/psdzdata/swe/swfl/swfl_00002720.bin.006_027_001 ~/psdzdata/swe/swfl/
bash wsl/setup.sh ~/psdzdata
```

**4. First boot** (stages the firmware, boots QNX, saves a snapshot, ~7 minutes):

```bash
bash wsl/emulator.sh prepare
bash wsl/overlay.sh --language en-us
bash wsl/emulator.sh snapshot
```

**5. Every later start:**

```bash
bash wsl/emulator.sh fast
```

From Windows you can use `windows\bimmulator.cmd start` instead (see the file header; set
`BIMMULATOR_REPO` if you cloned somewhere else than `~/bimmulator-windows`).

## Controls

Click the emulator window first. Mouse = CID touch. Mouse wheel / Page Up / Page Down = turn the
controller, arrow keys = tilt, Return or Space = press, Escape or Backspace = back, M = Menu,
O = Options, C/R = Media/Radio, T = Communication, N = Navigation, V = Map.

Scriptable control (used by AI agents and tests):

```bash
bash wsl/control.sh key next next press      # controller steps; step slowly while screens load
bash wsl/control.sh tap 720 270              # touch at x,y on the 1440x540 CID
bash wsl/control.sh shot ~/screen.png        # screenshot
bash wsl/control.sh stop
```

## Customising the head unit (overlay)

`wsl/overlay.sh` writes `~/idrive/overlay/overlay.tar`. The guest downloads it right before
HmiMain3D starts, so changes apply on the next start (also `fast`) without rebuilding the snapshot.

```bash
bash wsl/overlay.sh --language tr                                   # Turkish UI
bash wsl/overlay.sh --car-coding ~/hu_coding_backup.ncd --language de  # your car's HU coding
bash wsl/overlay.sh --plugins ~/my-plugins                          # ~/my-plugins/<Name>/ -> Plugins/<Name>/
HERO=~/mycar.png bash wsl/overlay.sh                                # My Vehicle tile picture (378x243 RGBA)
```

## Vehicle simulators (`vehicle-sim/`)

`wsl/emulator.sh` starts three host processes unless `SIM=0`:

| Process | Port | Role |
|---|---|---|
| `ioc_sim.py` + `rules.py` | 8766 | Jacinto-side MOST link (NAL-SIPC): network registry, power mode, terminal status, mileage, tyre pressures, oil, trip data, live engine values for Sport displays. `rules.py` is hot-reloaded. |
| `j5_server.py` + `j5_rules.py` | 5600 | Host side of the guest bridge `tools/qnx-j5-bridge.c` (DSI `DSYSMOSTServer` stand-in) |
| `diag_sim.py` | 6801 | HSFZ/UDS diagnostic gateway for plug-ins (guest address 160.48.199.253). Synthetic idle engine by default; `DIAG_RECORD=<IDriveReader record>` replays your own read-only capture. |

Protocol notes: [`vehicle-sim/NOTES.md`](vehicle-sim/NOTES.md), tyre-pressure reverse engineering:
[`vehicle-sim/TPM-RE.md`](vehicle-sim/TPM-RE.md).

Optional: properties nobody answers can get "neutral" (minimum valid) payloads. Generate
`vehicle-sim/hmi_layouts.json` and `helper_sizes.json` from *your* `HmiMain3D`
(`python3 vehicle-sim/hmi_layouts.py <HmiMain3D>`, then `hmi_helper_sizes.py`) and point
`IDRIVE_IDEMU_DIR` at a local checkout of [herrbimmer/IDEmu](https://github.com/herrbimmer/IDEmu)
(its data is not redistributed here). Without these files the feature is simply off.

## Repository layout

| Path | Content |
|---|---|
| `wsl/` | Windows/WSL2 workflow: `setup.sh`, `emulator.sh`, `overlay.sh`, `control.sh`, QMP helpers |
| `windows/bimmulator.cmd` | Windows wrapper around the WSL scripts |
| `vehicle-sim/` | Host simulators for the vehicle side (MOST/Jacinto, HSFZ gateway) |
| `overlay/make_overlay.py` | Builds the per-boot overlay (language, coding, plug-ins, 3D body) |
| `tools/idrive6-launch.py`, `run-emulator.sh` | Launcher and QEMU runner (from upstream, ported) |
| `tools/angle-egl-rpc-server.cpp`, `tools/qnx-angle-egl-provider.c` | GLES2 bridge guest → host ANGLE (incl. framebuffer objects) |
| `tools/shaders/native-reconstructions/` | SGX shader reconstructions; `*-car006.json` maps for HU 006.027.001, `hmi-fragment-car006/` hand-written stages |
| `tools/qnx-j5-bridge.c`, `tools/qnx-wsl-fetch.c`, `tools/wsl-snapshot.py` | WSL2 port pieces (Jacinto bridge, overlay fetch, snapshot) |
| `nix/patches/` | QEMU OMAP5430 / SGX / Capricorn-M patches (GPL-2.0-or-later) |
| `profiles/f30-car-006027-id6-light.json` | Emulator profile for HU 006.027.001 |
| `docs/UPSTREAM-README.md` | Original upstream README (macOS, X20511I 007.030.001, 6WB cluster/HUD) |
| `NATIVE_GRAPHICS_CONTRACT.md`, `HMI_STARTUP_DEPENDENCY.md` | Deep technical notes from upstream |
| [`AGENTS.md`](AGENTS.md) | Instructions for AI coding agents |

## Troubleshooting

| Symptom | Fix |
|---|---|
| `systemd is not running` | enable it in `/etc/wsl.conf` (Quick start 1) and `wsl --shutdown` |
| No window appears | Windows 11 with WSLg is required; `echo $WAYLAND_DISPLAY` must be set inside WSL |
| `No snapshot yet` | run `wsl/emulator.sh snapshot` once |
| Black screen for a few minutes after `fast` | normal: HmiMain3D loads assets in software; watch `~/idrive/run.log` |
| Keys seem ignored | click the window; step slowly — keys sent while a screen loads are dropped |
| `My Vehicle` says *Function currently not available* | build the overlay (`wsl/overlay.sh`) and keep `SIM=1` |
| Firmware hash mismatch | your PSdZData files are a different build; only HU 006.027.001 is supported on `main` |

## Credits

- **[agent00jackson/bimmulator](https://github.com/agent00jackson/bimmulator)** by Jackson Randolph —
  the original iDrive 6 emulator (patched QEMU OMAP5430/SGX, ANGLE bridge, shader reconstruction
  pipeline, launcher, 6WB cluster/HUD). This project is inspired by and built on top of that work;
  without it none of this would exist. Upstream history is preserved in this repository.
- [herrbimmer/IDEmu](https://github.com/herrbimmer/IDEmu) — its documentation was used as a
  reference for MOST FBlock/property semantics. No IDEmu code or data is included.
- QEMU, ANGLE, Mesa, Vita3K and Nixpkgs — see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## License

Non-commercial. The additions of this repository (WSL2/Windows port, HU 006.027.001 port, vehicle
simulators, overlay builder, documentation) are licensed under the
**[PolyForm Noncommercial License 1.0.0](LICENSE)**. Files from the upstream project remain under
their author's terms, and the QEMU patches under `nix/patches/` remain GPL-2.0-or-later. Details:
[`LICENSING.md`](LICENSING.md).

---

### Türkçe özet

Bu depo, BMW NBT EVO iDrive 6 ana ünite yazılımını (HU 006.027.001 / ID5_1811, F30) **Windows 11
üzerinde WSL2** ile çalıştırır. BMW yazılımı içermez; kendi PSdZData'nızı kullanırsınız. Kurulum:
yukarıdaki *Quick start* adımları (`wsl/setup.sh`, ardından `wsl/emulator.sh snapshot`, sonra her
seferinde `wsl/emulator.sh fast`). Dil için `wsl/overlay.sh --language tr`. Orijinal proje:
[agent00jackson/bimmulator](https://github.com/agent00jackson/bimmulator). Lisans: ticari olmayan
kullanım (PolyForm Noncommercial 1.0.0).
