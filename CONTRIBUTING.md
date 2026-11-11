# Contributing

Contributions are welcome — especially support for more head-unit builds (other PSdZData releases).

- **New firmware build:** follow [builds/README.md](builds/README.md). `tools/port-build.py` ports
  most of it automatically; [docs/PORTING.md](docs/PORTING.md) covers the rest.
- **Shader reconstructions:** add or fix entries in the shared library
  (`tools/shaders/native-reconstructions/hmi-*-library.json`). A fix must be right for every build
  that pins the entry.
- **Vehicle simulation:** `vehicle-sim/` (protocol notes in `vehicle-sim/NOTES.md`).
- **Windows/WSL scripts:** `wsl/`, `windows/`.

Rules:

1. Never commit BMW software or anything extracted from it, VINs, coding backups or other personal data.
2. Keep build-specific values in `builds/<id>/`; tools read them through `tools/buildinfo.py`.
3. Run `python3 -m unittest discover -s tests` before opening a pull request.
4. By contributing you agree that your contribution is licensed under the repository's
   [PolyForm Noncommercial License 1.0.0](LICENSE) (QEMU patches under `nix/patches/` stay
   GPL-2.0-or-later).

AI coding agents: read [AGENTS.md](AGENTS.md).
