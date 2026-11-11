# Head-unit builds

Every PSdZData / head-unit software build the emulator supports has its own folder here. The
launcher picks the build automatically by the SHA-256 of your head-unit packages
(`swfl_00002719`, `swfl_0000271a`, `swfl_00002720`), so several builds can live side by side in
`main` and everybody can add theirs.

| Build | Status | Notes |
|---|---|---|
| [`hu-006.027.001`](hu-006.027.001/build.json) | verified | ID5_1811, PSdZData 4.15.12, F30 assets, vehicle-sim rules developed here |
| [`hu-007.030.001`](hu-007.030.001/build.json) | verified-upstream | NBTevo_X20511I, ID5_2103, PSdZData 4.61.20, F32 assets (upstream reference) |

`python3 tools/buildinfo.py list` prints the registered builds;
`python3 tools/buildinfo.py detect /path/psdzdata` tells which one your PSdZData is.

## What is shared and what is per build

```
tools/shaders/native-reconstructions/hmi-{vertex,fragment}-library.json   SHARED, versioned
    GLSL reconstructions of BMW's native SGX shaders, keyed by asset path + program fingerprint.
    A shader program rarely changes between builds; only its container hash and a compiler field
    do (tools/buildinfo.py PROGRAM_MASK), so one reconstruction serves every build.
    "library_version" is bumped when existing entries change meaning; git history keeps old ones.

builds/<id>/                                                               PER BUILD
    build.json         packages, binary hashes, patch sites, controller hook addresses, vehicle
    profiles/*.json    emulator profiles (variants: vehicle, coding switches, comm modules ...)
    shader-pins.json   for each library entry: this build's native file hash + program fingerprint
    signatures.json    masked byte patterns of every site, used to port the build to new firmware
    PORT-REPORT.md     (new builds) what tools/port-build.py ported and how
```

At start-up the launcher composes the runtime shader maps from library + pins
(`tools/shader-library.py compose`) into `~/.cache/idrive6/shader-maps/<id>/` and validates them
against the staged firmware.

## build.json fields

| Field | Meaning |
|---|---|
| `id` | folder name, `hu-<HU version>` (add a suffix such as `-f20` for variants of the same HU version) |
| `status` | `draft` (ported, not booted) → `boots` → `verified` (fill `verified` with what you checked) |
| `packages` | head-unit packages and their SHA-256 (detection key) |
| `asset_package`, `assetdb_domains` | package and widget hashes of the eight firmware-matched assetDB domains |
| `release` | cache folder name of the staged firmware |
| `vehicle`, `theme` | 3D vehicle body and HMI theme staged from the firmware |
| `default_profile` | profile in `profiles/` used unless `profile = "..."` is set in `idrive6.toml` |
| `binaries` | SHA-256 of HmiMain3D, libhmicom, libhmicoding, libhmidb, variantregistry — every patch checks these first |
| `coding.defaults_index` | file offset of libhmicoding's built-in defaults index (17 entries: key, size, page offset) |
| `coding.expected_pages` | key → [page size, page offset] for the pages the emulator patches |
| `coding.code_patches` | force CHmiCodingService to use the built-in defaults (no QNX setpage in QEMU) |
| `coding.id6l_patches` | ID6 Light menu (HMI_ID_VERSION), BAUREIHE/productline, master language, 10.25" 1440x540 display |
| `coding.developer_menu_patch`, `cid_1440_patch`, `cid_touch_patches`, `camera_rvc` | developer menu, CID resolution, CID touch, reversing camera |
| `variantregistry_paths` | retarget the G11 placeholder vehicle to the staged body |
| `bench_input_patches` | HmiMain3D: enable home input subscription and seed the touch handler during the bench boot |
| `resource_language_sites` | libhmidb CHmiResourceManager C1/C2 `mvn r0,#0` sites (start language) |
| `controller` | HmiMain3D addresses used by the native controller hook (`tools/qnx-hmi-controller.c`) |

All patch entries are `[file offset, original bytes, replacement bytes]`; a mismatch of the
original bytes stops the build instead of patching blindly.

## Add your build

1. Put your PSdZData somewhere inside WSL and run the porter against a verified build:

   ```bash
   python3 tools/port-build.py new --from hu-006.027.001 --id hu-006.030.002 --psdzdata ~/psdzdata --vehicle F30
   ```

   It extracts your head-unit packages, ports every value with `signatures.json`, pins the shader
   library by program fingerprint and writes `builds/<id>/` with `status: "draft"` and
   `PORT-REPORT.md`. Nothing in your PSdZData is modified. Ported in both directions between
   006.027.001 and 007.030.001, the tool reproduces every known value exactly.
2. Check `PORT-REPORT.md`. Items marked **FAILED** need manual work (see
   [docs/PORTING.md](../docs/PORTING.md)); `python3 tools/port-build.py verify --build <id> --rootfs <extracted rootfs>`
   must say OK.
3. Boot it: `bash wsl/emulator.sh prepare`, `bash wsl/overlay.sh`, `bash wsl/emulator.sh snapshot`.
   Fix what does not render or respond (missing shader reconstructions are listed in the report).
4. Fill in `title`, `psdzdata`, `i_level`, `hmi_version`, `maintainer`, `status` and `verified`,
   then generate signatures from your own build so others can port from it:

   ```bash
   python3 tools/port-build.py signatures --build <id> --rootfs ~/.cache/idrive6/firmware/<release>/rootfs
   ```

5. Open a pull request with **only** `builds/<id>/` plus any new library entries / tool fixes.
   Never commit firmware files, extracted rootfs content, VINs or coding backups.

## Rules for shared files

- Change a library entry only if the fix is right for every build that pins it; otherwise add a
  new entry for your program fingerprint (`tools/shader-library.py sync` after a generator run).
- Bump `library_version` in the library file when an entry's meaning changes, and re-run
  `tools/shader-library.py pin --build <id> --rootfs <rootfs> --write` for builds you can test.
- Keep tools build-agnostic: read values through `tools/buildinfo.py current_build()`.
