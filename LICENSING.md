# Licensing

This repository combines work from several sources. Each part keeps its own terms.

| Part | Terms |
|---|---|
| Additions of this repository — the Windows/WSL2 port (`wsl/`, `windows/`, WSL2 changes in `tools/`, `run-emulator.sh`, `flake.nix`), the HU 006.027.001 port (car-006027 commits, `*-car006*` shader maps and hand-written shaders, `builds/`), the build registry and porting tools (`tools/buildinfo.py`, `tools/shader-library.py`, `tools/port-build.py`), the shader library, `vehicle-sim/`, `overlay/`, and the documentation added here | **PolyForm Noncommercial License 1.0.0** — see [LICENSE](LICENSE). Required notice: Copyright (c) 2026 Ahmet Karaçalı |
| Code and documents from [agent00jackson/bimmulator](https://github.com/agent00jackson/bimmulator) (upstream commit `bf03f2e`, author Jackson Randolph) | Remain the upstream author's. The upstream repository was published without a license file; this repository credits it and does not grant any additional rights to that code. |
| QEMU patches in `nix/patches/` | GPL-2.0-or-later (they modify QEMU) — [licenses/GPL-2.0.txt](licenses/GPL-2.0.txt) |
| Vita3K USSE visitor used by the optional shader diagnostics (fetched, not included) | GPL-2.0-or-later |
| BMW software (PSdZData, firmware) | Not included. You need your own lawful copy. |

Non-commercial means: personal use, research, education and hobby projects are allowed;
selling the software, bundling it into a paid product or service, or other commercial use is not.
See the license text for the exact terms.

If you are the upstream author and want the terms or attribution changed, please open an issue.
