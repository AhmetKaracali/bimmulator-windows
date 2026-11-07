# Genuine BMW shader arithmetic and graphics probes

This standalone harness reuses Vita3K's USSE visitor and glslang's SPIR-V
builder. Nix pins both sources in `flake.nix`:

- Vita3K `62727b58322ea7be10aaade575ac9ef82c58f5e8` (GPL-2.0-or-later).
- Its matching glslang submodule `fc9889c889561c5882e83819dcaffef5ed45529b`.

The build uses the same compiler source as the existing comparison grammar.
No files from the temporary source inspection cache are needed. The upstream
GXP parser/renderer is not the input adapter: finalized BMW instructions feed
the existing recompiler below that layer. A zeroed GXP metadata object supplies
no literals or texture bindings; operations needing those remain unsupported.

At configure time, a checked copy of the upstream dispatch function makes
unknown and rejected instructions throw. The local diagnostic adapter also
throws for upstream warnings/errors, and assertions remain enabled.
Only the examined operation families (VMOV, VMAD2, VPCK, V32NMAD, V16NMAD,
VMAD, SOP2, SOP2M, NOP, VBW) are admitted before CFG analysis. VBW uses the
pinned Vita3K visitor's typed integer operations; unsupported rotate-left still
fails explicitly. VMAD2 and SOP2 use their existing visitor implementations;
SOP2 selectors not covered by that implementation fail through its diagnostics.
The visitor routes V16NMAD through the V32NMAD decoder but marks that path TODO,
so generated half-precision shaders remain translation candidates pending a
discriminating native result. Memory, texture and task instructions cannot
consume absent metadata or silently expand coverage.
Original upstream source stays immutable in the Nix store. No shader arithmetic is
replaced with a hand-written shader.

```sh
nix develop .#shader --command ./tools/build-usse-recompiler.sh
```

Starting with the validated output directory from
`tools/extract-unipatch-capture.py`, generate computational probes for each
stage:

```sh
nix develop path:.#shader
build/idrive6-cache/usse-recompiler/idrive-usse-recompile FIXTURE_DIR vertex FIXTURE_DIR/vertex.compute.spv
build/idrive6-cache/usse-recompiler/idrive-usse-recompile FIXTURE_DIR fragment FIXTURE_DIR/fragment.compute.spv
python3 tools/check-usse-arithmetic.py FIXTURE_DIR --output NEW_EVIDENCE_DIR
```

The compute wrapper exposes 132 vec4 entries in a storage buffer: 32 primary
attribute, 32 secondary attribute, 32 temporary, four internal and 32 output
entries. Vertex constants are copied according to the extracted native table.
Only the verified leading scheduling-placeholder layout is accepted. This
wrapper does not implement native task scheduling or attribute fetch code.

On 2026-11-01 the genuine cover pair produced valid Vulkan SPIR-V and executed
through Nix MoltenVK 1.4.2 on an Apple M4 Max. Three vertex matrix/UV controls
and three fragment-register controls passed. Fragment arithmetic consumes PA1
and the recovered SA9 opacity value; the relationship between PA1 and the
native texture sampler's channel layout is not established. An initial test
assuming ordinary RGBA-to-register order did not match its assumed alpha
result. The register controls deliberately make no texture-channel claim.

Initial pipeline creation emitted a MoltenVK Cereal serialization diagnostic
about four missing bytes in `CompilerMSL::Options`; Vulkan calls succeeded and
the numerical controls passed. Retain this backend issue for the rendering
gate rather than treating compute success as production-backend validation.

## Candidate graphics-stage raster

`idrive-usse-graphics` wraps the same finalized USSE code in candidate vertex
and fragment interfaces. It preserves the genuine arithmetic, but its current
bindings are named hypotheses: vertex location 0 is position, location 1 is
UV; the fragment receives the interpolated UV at location 0; a selected
sampled component is forwarded to PA0.y; and packed output MSB is treated as
red. Vertex and fragment secondary-attribute banks are separate Vulkan UBOs.
These assumptions let the pair execute as a host graphics pipeline; they are
not a recovered BMW GLES/SGX contract.

Run the reproducible synthetic channel control from the pinned Nix shell:

```sh
nix develop .#shader --command sh -c '
  ./tools/build-usse-recompiler.sh && \
  python3 tools/run-usse-graphics-candidates.py \
    ./build/idrive6-cache/evidence/unipatch-cover-finalized-2026-11-01 \
    --output ./build/idrive6-cache/evidence/usse-graphics-candidates-NEW
'
```

The helper maps the captured `table_54` records into an identity vertex
transform and fragment SA9=0.5, generates all four PA1 component candidates,
validates their SPIR-V, then draws each through the Vulkan runner using a 2×2
red/green/blue/white RGBA8 texture. Each BMP is checked against independent
pixel-count and quadrant expectations. For the recorded run on 2026-11-01,
each R/G/B candidate produced 32,768 candidate red pixels and 32,768 clear
pixels; A produced 65,536 candidate red pixels. Quadrant samples verify the
host Vulkan image-origin result. The exact expected/actual BGRA samples,
shader/uniform/texture/runner hashes and MoltenVK output are retained in
`usse-graphics-candidates-2026-11-01-v4/report.json` under the ignored evidence
cache. Each case also writes and reloads a 22,197-byte Vulkan pipeline cache;
the fresh and cached BMP files are byte-identical. The synthetic texture is a
harness control, not a BMW material image. A second control uses a non-symmetric
vertex matrix and repeats the G-channel draw with SA9 opacity 0, 0.5 and 1. Its
24,082-pixel candidate mask remains fixed while the packed red value scales
from 128 to 255; zero opacity clears the whole image. Per-pixel comparisons
and quadrant samples are included in the report.

Initial graphics pipeline creation still emits MoltenVK's Cereal serialization
diagnostic about four missing bytes in `CompilerMSL::Options`; draw/readback
and the default-option pipeline-cache round trip complete. Nix combines
MoltenVK 1.4.2 with SPIRV-Cross 1.4.363.0, whose MSL options add depth-clip
fields absent from MoltenVK 1.4.2's cache archive. The tested default options
are retained across the round trip; depth-clip emulation cache behavior remains
unqualified. The Vulkan harness does not create Screen buffers, implement the
guest's EGL/GLES API, or present an HMI frame. Native sampled-component and
output packing remain unresolved. The next renderer gates are a justified
native/reference draw contract, a structurally different genuine shader pair,
and backend diagnosis, as laid out in `IMPLEMENTATION_PLAN.md`.

## Export the native pair interface

After `tools/extract-unipatch-capture.py` has validated a native finalizer
capture, join its source containers, capture manifest and Ghidra Evidence into
a versioned typed interface JSON:

```sh
python3 tools/export-unipatch-interface.py \
  --project-root "$PWD" \
  --run-manifest build/idrive6-cache/evidence/unipatch-finalizer-run-2026-11-01.json \
  --capture-dir build/idrive6-cache/evidence/unipatch-cover-finalized-2026-11-01 \
  --capture-log build/idrive6-cache/evidence/unipatch-finalizer-native-2026-11-01.log \
  --ghidra-evidence build/idrive6-cache/evidence/libimg-glesv2-sampler-contract-2026-11-01.evidence.json \
  --vertex-shd build/idrive6-cache/rootfs-x20511i/opt/hmi/ID5/data/ro/common/widgetasset/cover/shaders/mat_cover_bg.vert.shd \
  --fragment-shd build/idrive6-cache/rootfs-x20511i/opt/hmi/ID5/data/ro/common/widgetasset/cover/shaders/mat_cover_bg.frag.shd \
  --output build/idrive6-cache/evidence/NEW-pair-interface.json
```

The exporter verifies driver/source/capture hashes, count/stride/pointer ranges
and required Ghidra queries. It keeps opaque records and unresolved fields
explicit. Its result is a static/native-CPU interface artifact, not a graphics
pipeline or frame; host candidate draws do not settle the BMW sampler mapping.
Outputs under `build/idrive6-cache/` are generated and ignored by Git.
