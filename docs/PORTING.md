# Porting to another head-unit build

Start with [builds/README.md](../builds/README.md): `tools/port-build.py new` does the work and
writes `PORT-REPORT.md`. This page covers what to do when an item in that report says **FAILED**
or when the ported build does not boot cleanly.

## What depends on the firmware build

| Item | Where it is used | How it is ported | If it fails |
|---|---|---|---|
| Package / binary hashes | launcher detection, every patch | computed | — |
| libhmicoding defaults index + pages | `tools/archive-idrive-rootfs.py`, `overlay/make_overlay.py` | found by structure (17 entries key 1..17) | dump the table (`struct <III`) and look for the key run; page sizes must equal the reference |
| Coding page patches | ID6 Light, display, CID, camera, developer menu | same position inside the same page | if the original byte differs, the BMW default differs: check the bit meaning in the coding descriptor before changing the replacement |
| libhmicoding code patches | defaults instead of QNX setpage | masked code patterns | find `CHmiCodingService::openBinaryStream` / `SysetPageGetSh_getBuffer` via exported symbols (`vehicle-sim/elfsyms.py find`) |
| HmiMain3D bench input patches | home input + touch during the bench boot | masked code patterns | compare the function around the old site in a disassembler (capstone); the instruction bytes are given in build.json |
| libhmidb language sites | start language | patterns (the two constructors are identical code: Nth-of-K match) | search for `mvn r0, #0` (`00 00 e0 e3`) inside the two CHmiResourceManager constructors |
| Controller hook addresses | `tools/qnx-hmi-controller.c` (via `-D` defines) | functions: entry patterns or call-site voting; vtables: slot functions located then the table; pop callers: strict + loose patterns | without them the controller keys do nothing, touch still works; port them with Ghidra by comparing the reference function |
| assetDB widget hashes | `tools/materialize-hmi-assetdb.py` | read from the extraction inventory | if a domain is missing, remove it from the list and note it |
| Shader pins | composed shader maps | program fingerprint | see below |
| Profiles | `builds/<id>/profiles/` | copied, release paths rewritten | adjust settings that are model-specific (vehicle, coding switches) |

Patterns mask what moves between builds (branch targets, PC-relative literal offsets, movw/movt
immediates; "loose" patterns also load/store offsets and literal-pool words). Every pattern that
matches must agree on the same address, otherwise the item is reported as failed rather than
guessed.

## Shaders whose program changed

`PORT-REPORT.md` lists library entries whose native program differs in your build. Those draws fall
back to unmapped rendering (often invisible). Options, in order of effort:

1. Generated host shaders: `tools/make-common-host-shaders.py`, `make-widget-host-shaders.py`,
   `make-car-model-shaders.py` write library entries for common/widget/car materials from the
   staged rootfs; then `python3 tools/shader-library.py sync --build <id> --rootfs <rootfs>`.
2. Reconstruct from the native shader: `tools/inspect-sgx-shader.py`, `tools/decode-sgx-usse.py`,
   the USSE recompiler (`nix develop .#shader`), see NATIVE_GRAPHICS_CONTRACT.md.
3. Hand-write ESSL for the material (examples in `hmi-fragment-car006/`) and add a library entry
   with `source_path`, `basis` and the program fingerprint of your native file.

Unmapped shader binaries met at run time can be dumped with
`EXTRA="IDRIVE_ANGLE_SHADER_DUMP_DIR=/tmp/shd" bash wsl/emulator.sh fast`.

## Checklist before a pull request

- `python3 tools/port-build.py verify --build <id> --rootfs <rootfs>` → OK
- boots to the home screen, controller keys and touch work; note what you verified in `verified`
- `python3 tools/port-build.py signatures --build <id> --rootfs <rootfs>`
- `python3 -m unittest discover -s tests` passes
- only `builds/<id>/`, library entries and tool fixes are in the diff; no firmware or personal data
