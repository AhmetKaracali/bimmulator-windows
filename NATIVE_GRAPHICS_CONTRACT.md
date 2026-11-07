# Native BMW graphics contract

Updated 2026-11-02. Target: staged X20511I ARM/QNX runtime and F32/id6l HMI.
The findings below are static unless a runtime capture is named. No native BMW
frame has been observed. This document records the interface being implemented;
it does not claim a completed EGL/GLES replacement.

## Reproducible baseline

The selected source IFS is `build/idrive6-cache/boot1-x20511i.ifs`, SHA-256
`92ab3d44bdd039bb27639029dc9245d3a5e8b7cbea872c8784653cf34acdc173`.
The root is `build/idrive6-cache/rootfs-x20511i`. The cached evidence file
`build/idrive6-cache/evidence/baseline-2026-11-01.json` records the IFS module
identities, selected root files, QEMU binary and launch-recipe hashes.

Comparing normalized IFS contents establishes that the historical patched dump
and matching IFS contain identical `procnto-smp-instr`, `libc.so.3`, SD driver
and serial driver binaries. Eleven common modules differ, including startup
scripts, BMW utilities and the OMAP starter plugin; the matching image also
contains `boot/bin/login`. This rules out different kernel/libc bytes in these
two images, not every possible userspace/configuration mismatch. Future runs
use the matching image and record the generated IFS/config separately.

## Native windows: KD is a Screen adapter

`lib/libKD.so.1`, SHA-256
`0143ec0ffd77a9712e9944275da3ea5933d3482b3441fad9859612942eef6959`,
was queried and decompiled successfully with Ghidra 12.1.4 after recovery.
Raw shared-library VAs below map to Ghidra addresses by adding `0x10000`.

| Operation | Observed behavior | Consequence |
| --- | --- | --- |
| `kdCreateWindow`, raw `0x456c` | Creates a Screen context/window. Reads EGL buffer size, alpha size, renderable type and native-renderable config attributes. Uses them to set Screen format and usage, applies configured properties, and returns the Screen window handle. | KD does not introduce a separate native-window wrapper in this path. A provider must return config attributes compatible with Screen buffer allocation. |
| `kdRealizeWindow`, raw `0x3d84` | Calls `screen_create_window_buffers(window, 2)`, writes that same window handle to the native-window output and returns zero. | Native window identity remains the Screen handle. The implementation ignores the allocation result, so its zero result alone cannot validate buffer creation. |
| `kdDestroyWindow`, raw `0x4544` | Validates a non-null handle and calls `screen_destroy_window`. | Window ownership/lifetime must remain with the guest. |
| Property adapter | Maps KD size/buffer-size/z-order and other properties to Screen setters/getters. | Do not infer a host pointer layout from a KD handle. |

Evidence bundle: `build/idrive6-cache/evidence/ghidra-kd-window-contract-2026-11-01.json`.
Creation evidence: `ev_883a69da701cde0bc17a1784808ae1740835d9ed7d90158236c6ef0de1f4841a`.
Realization evidence: `ev_a05744b1706752f43f0c0432020d1a59214a56fd6ed92f8b9979fb436d66e4ed`.

The HMI defines `kdMain` but directly imports 19 Screen functions and ten EGL
functions; it does not import `kdCreateWindow`. The native HMI path below is a
separate direct Screen implementation, not the KD adapter. Decompiler
omissions of forwarded tail-call arguments are not ABI facts.

## HmiMain3D direct Screen window path

The realized `HmiMain3D` executable has SHA-256
`418906bf10aeebcee6a02b8687b63a6c6e530a9263dc7171892c568e4d86845e` and
matches the Ghidra snapshot used for this trace. `CWal3dNBTevo::createWindow`
creates its Screen context (`FUN_0289ed24`, call path at `0x289f744`), then a
Screen window (`FUN_0289ee4c`) and its EGL surface. The Screen context is stored
on the HMI instance; the Screen window and EGL surface are kept in the HMI's
surface record. This is HmiMain3D-owned state; it is not the independent test
client or LayerManager's `RemoteEGLImageSource` path.

The recovered creation sequence is:

1. Resolve the native window ID string from the HMI's logical-to-native ID map.
   If there is no map entry, the helper returns `0xffff`; the resulting decimal
   string is assigned through `SCREEN_PROPERTY_ID_STRING`. The HMI passes the
   string length and pointer as the third and fourth arguments to
   `screen_set_window_property_cv`.
2. Set `SCREEN_PROPERTY_FORMAT=8` (RGBA8888),
   `SCREEN_PROPERTY_USAGE=0x20` (OpenGL ES 2), and
   `SCREEN_PROPERTY_VISIBLE=0`.
3. Set both `SCREEN_PROPERTY_BUFFER_SIZE` and `SCREEN_PROPERTY_SIZE` to the
   requested width/height, and set `SCREEN_PROPERTY_POSITION=(0,0)`.
4. Call `screen_create_window_buffers(window, 2)`.
5. Call `eglCreateWindowSurface` with `EGL_RENDER_BUFFER=EGL_BACK_BUFFER`; the
   observed present call later is `eglSwapBuffers(display, surface)`.

The import/call trace found no `screen_post_window` import in HmiMain3D. This
means its observed present boundary is EGL swap, not the CPU test client's
explicit Screen post. The Screen window is initially invisible. Its ILM
visibility callback updates an internal ID map but does not directly set
`SCREEN_PROPERTY_VISIBLE`; LayerManager/display-manager visibility and final
composition remain external or unresolved. Static tracing also did not
establish resize, destroy, Screen buffer reuse or EGL failure-cleanup behavior.

Evidence bundle: `build/idrive6-cache/evidence/ghidra-hmi-screen-window-2026-11-01.json`.
The focused context-creation assembly is `ev_af8a7b9313478cb66fdfc2077c559bb147fce68c544a0ac5137cda83a2213ece`.
The Screen allocation probe is `tools/qnx-screen-hmi-contract.c`; it creates
the same hidden RGBA8888/GLES2 window and correctly sizes the render-buffer
handle array from `SCREEN_PROPERTY_RENDER_BUFFER_COUNT` before querying buffer
format, dimensions, stride, CPU pointer availability and physical metadata.
It is a diagnostic client, not an EGL surface or HMI frame. The staged QNX
6.5 API defines the property IDs, requires the character setter's length
argument, and requires enough output storage for every render buffer
([property types](https://www.qnx.com/developers/docs/6.5.0SP1.update/com.qnx.doc.screen/topic/screen_8h_1Screen_Property_Types.html),
[character-property setter](https://www.qnx.com/developers/docs/6.5.0SP1.update/com.qnx.doc.screen/topic/screen_set_window_property_cv.html),
[window property query](https://www.qnx.com/developers/docs/6.5.0SP1.update/com.qnx.doc.screen/topic/screen_get_window_property_pv.html)).

The exact second argument to the HMI's Screen-context creation call is
resolved: the HMI loads its zero-initialized context-state byte into `r1` and
immediately calls `screen_create_context`, so its flags are `0`
(`SCREEN_APPLICATION_CONTEXT`). The corrected runtime probe uses the QNX 6.5
four-argument `screen_set_window_property_cv(window, property, length, text)`
ABI. In the warm QNX guest, context creation, window creation, ID-string setup,
all six window-property setters and two-buffer creation returned success. The
queried render-buffer count and general buffer count were both `2`. Each
buffer reported format `8` (RGBA8888), dimensions `1440×540`, stride `5760`,
physically-contiguous `1`, and a non-null guest-process pointer. QNX returned
physical addresses `0xd4e00000` and `0xd3c00000`. Querying
`SCREEN_PROPERTY_USAGE` on a buffer returned `-1`; setting GLES2 usage on the
window returned `0`. The full output is preserved at
`build/idrive6-cache/evidence/screen-hmi-contract-2026-11-01.txt`.

The earlier three-argument probe build failed at the ID-string setter and is
discarded. The successful output validates Screen allocation, but the returned
pointers are guest virtual addresses and do not establish host visibility of
the pages or interoperability with a host renderer. An optional write check
through the non-null pointer faulted for this GLES2-only window; the runtime did
not demonstrate CPU-writable guest access. The probe output is at
`build/idrive6-cache/evidence/screen-hmi-pointer-write-fault-2026-11-01.txt`.

QEMU now supports an opt-in file-backed shared OMAP5 RAM region. With it
enabled, the Screen buffer's reported physical address `0xe2200000` maps to
file offset `0x62200000`. While the hidden buffer was still allocated, the host
wrote the eight-byte marker `ID6RAM!!` to the shared file and QEMU's physical
read returned the same bytes. The repeatable capture helper is
`tools/qemu-screen-buffer-ram-probe.py`; output is preserved at
`build/idrive6-cache/evidence/screen-hmi-shared-ram-write-2026-11-01.txt`.
This proves host-to-QEMU access to the live buffer pages. The diagnostic
window remains hidden, so the result does not show Screen composition, EGLImage
handoff, or a displayed frame. The expected logical HMI layer is 1440×540.
Most importantly, the real HMI currently fails at `eglInitialize` before
reaching this window path, so this contract does not establish EGL startup or
render BMW pixels.

## EGL provider loading: use the existing dispatcher

`lib/libEGL.so.1`, SHA-256
`54ad4bb53ef21d9b4ca61aacccd10749e0b1c897d4388132deef26661e6e6e24`,
selects its provider from the active Khronos display's `egl-dlls` setting.
The original configuration uses
`[IMG%s] libusc.so libsrv_um.so libpvr2d.so libIMGegl.so`.

The loader at raw `0x3e00`:

1. Reads `egl-dlls` through `__khrGetDisplayConfigValue` and loads the list with
   `__khrLoadLibraryString`.
2. Expands the optional prefix pattern for `eglQueryString`, not
   `eglGetProcAddress`, and calls the result as `QueryString(NULL, 0x6000)`.
3. If that returns a table, uses it directly. Otherwise allocates a 34-pointer
   core table and resolves the corresponding prefixed names individually.
4. Resolves eleven optional extension functions separately by prefixed name.
5. Calls the provider's `eglGetError` once to clear the loader probe's error.

The exact core-name table is at raw ELF VA `0xa6c8`; optional names start at
`0xa750`. Core slots relevant to this capture are:

| Slot | Function |
| --- | --- |
| 0 / 1 / 2 | `eglGetError` / `eglGetDisplay` / `eglInitialize` |
| 4 / 5 / 6 / 7 | `eglQueryString` / `eglGetConfigs` / `eglChooseConfig` / `eglGetConfigAttrib` |
| 8 / 22 / 24 / 31 | `eglCreateWindowSurface` / `eglCreateContext` / `eglMakeCurrent` / `eglSwapBuffers` |
| 33 | `eglGetProcAddress` |

The public dispatcher forwards `eglInitialize` through table offset `8` and
`eglChooseConfig` through offset `0x18`. The display helper at raw `0x41ec`
caches native-display/provider-display associations. This supports selecting a
provider through configuration while retaining the BMW preload wrappers and
QNX EGL dispatcher, rather than replacing the front-end shared library.

Targeted Ghidra decompilation of the exported `eglQueryString` wrapper at raw
ELF VA `0x3160` confirms that it calls through the table at offset `0x10`, the
fourth function pointer. The `eglInitialize` wrapper at raw ELF VA `0x3134`
uses offset `8`. This matches the provider's 34-slot table ordering. Ghidra
Evidence: `ev_6c52e5c00a1acedad7bf06299c870471fef753244eae9f4f088d64699bf74fd3`.

Evidence: `build/idrive6-cache/evidence/ghidra-egl-dispatch-contract-2026-11-01.json`;
loader `ev_1a8c76b71b35e7549f501523fb6fb973b1f8706d1ce0cc9baeb11a291d127452`;
display mapping `ev_c4c829da1d4cd7571c6ffc8f56695dcaf2dc95b15bbd70601a27f599114fee73`.

## Vendor failure ordering

`libIMGegl.so`, SHA-256
`9dc7179f7515f63b2ff9c5422c8292af73c3263bcc0a3d85ce15ca181f10f762`,
provides all 34 core symbols and eight of the eleven optional symbols.
`IMGeglQueryString(NULL, 0x6000)` returns null after setting `EGL_BAD_DISPLAY`;
the dispatcher then resolves names and clears that expected probe error.

`IMGeglInitialize` initializes vendor state, then the platform/native-display
backend. Several platform failure branches return false and set `0x3001`.
`IMGeglChooseConfig` checks the display initialization flag before reading the
attribute list; an unset flag returns false with `0x3001`. Thus the observed
later config failure does not establish an unsatisfiable pixel-format request.

Evidence: `build/idrive6-cache/evidence/ghidra-img-egl-startup-2026-11-01.json`;
query `ev_01d403acb3f72f86a32af5293fa058eb86bcc7ba20bd837fd2418fd4f8588bbe`;
initialize `ev_b7b574c479f08c29c8f56cd2ef827e2affb64e431f32e93983ff16eba1eb8b21`;
choose `ev_46f2fc1fe530652b68b95a9f65cc48f0e827c549734b96d52e636423701488a0`.

## Controlled capture: resolve the actual application requests

`IDRIVE_EGL_PROVIDER_TRACE=1` selects an instrumentation provider using the
verified table handshake. Its core table forwards the real IMG functions and
wraps only selected operations. Optional exports use ARM tail branches to the
same vendor symbols, preserving register/stack arguments. The three absent
optional vendor exports remain absent. No EGL success or configuration is
invented, and error queries occur only when the dispatcher/application asks.

Before booting, the host harness checks the actual staged table order, argument
and output forwarding, failed-output safety, and absence of extra error reads.
The ARM build is audited against exports from the matching IFS libc and vendor
EGL library. Those checks do not validate the guest loader; the capture must
first show `ID6EGL ... provider-table ... slots=0x00000022`.

The completed capture used the matching IFS/root, no CDC NIC and no frame
bridge. `egl-contract-run-2026-11-01.json` records the generated IFS, embedded
configuration/helper hashes and immutable serial capture. Both native HMI
instances (PIDs 180239 and 340014) reached the forwarding provider:

| Question | Required observation | Decision |
| --- | --- | --- |
| Did the instrumentation attach at the intended boundary? | 34-slot provider marker followed by per-PID native calls | Passed; the initial `0x3008` is the expected private-query error cleared by the dispatcher. |
| Does initialization or config filtering fail? | Both HMI instances get false from `eglInitialize`, then false/`0x3001` from `eglChooseConfig` | Initialization fails first. Config filtering is not reached in the vendor implementation. |
| What does the HMI request? | Window surface, ES2, RGBA8, depth24, no sample buffers/samples; context client version2 | Preserve these exact requests in the replacement provider. |
| Which window/context calls are reached? | `eglCreateContext` with null config returns null/`0x3001`; no create-window-surface or make-current call | Actual HMI native-window argument and buffer lifecycle remain unobserved. |

LayerManagerService (PID 213029) reads `0x3003` (`EGL_BAD_ALLOC`) immediately
after its own failed initialization. The HMI does not query the error at that
point: its observed `0x3001` follows config selection and must not be reported
as the HMI's initial initialization error. Native slog also records
`PVRSRVConnect: Unable to open connection` for HMI PID 180239. No successful
provider/context/draw has been fabricated by this instrumentation.

This failure is specific to the software-Screen configuration:
`tools/graphics-omap5-software.conf` leaves out `gpu-dlls`, and the associated
warm-guest check confirms `/dev/pvrsrv` is absent. Do not generalize that
observation to the native-PVR probe. With the recovered native GPU libraries
loaded, QNX logs show the PVRSRV device driver, SGX MMU setup and firmware
command submission. That path stops at microkernel command execution, before
the real GETMISCINFO response completes.

Ghidra analysis of the matching `pvrsrv.so`
(`a72cf24321b8627578745273c89d30a6f8539c8a70f5f27c23d304f5d2cd899b`)
locates `SGXDevInitCompatCheck` at `0x3b628`. Its call at `0x3b704` to
`FUN_0003b4c0` submits GETMISCINFO and waits for the microkernel ready bit;
the failure string is emitted when that operation returns an error. Evidence
is in `pvrsrv-ddk-init-boundary-2026-11-01.evidence.json` and snapshot
`pvrsrv-ddk-init-boundary-2026-11-01.snapshot.json`. The native-PVR runtime
logs are in `sgx-usse-audit-2026-10-30/` and
`native-sgx-revision-probe-2026-10-31/`. A diagnostic reply with synthesized
GETMISCINFO fields is not a firmware response and does not clear the
PROCESS_QUEUES blocker.

The registered ILM surface is logical ID256, 1440×540. Its native surface ID
is `4294967295`, visibility is zero and frame/draw/update counts are zero.
That is not evidence of a created native Screen buffer or HMI frame.

The no-NIC guest was saved as `egl-contract-ready` in
`build/idrive6-cache/egl-contract-v1.qcow2`. A verified restore took 1.45s and
preserved the extracted root/debug shell. The snapshot embeds its original
helper/configuration bytes; rebuilding a helper does not update a saved guest.
Small new helpers can be serial-uploaded with full readback verification.

## LayerManager remote shared-image contract

`LayerManagerService` (`43aa0a17ad0d700eee6d4f7b60d3fbad7beab75d5f6cfadfc895a7569aae0019`)
initializes EGL, then its renderer creates a `RemoteEGLImageSource` for a client
Screen window. Static Ghidra evidence identifies the startup call at
`FUN_00124e50` (`ev_27028de42501d04c2438a3ffaf30e303e44a058c1262bb3c2117b7c0b89aa4e4`)
and the forward-update thread at `FUN_00123a40`
(`ev_2754e3ab3161af442bd8b82b1890eb63dced3f1f5e3edd67a8de37b2d8b58d5d`).
The constructor's EGL path is `FUN_00124364`
(`ev_fe867c94671bd9843d2eab8d7860b43a9d2d7c776a3f6fee4ea76048ccb7e454`).
These are static call-path facts. The runtime capture separately shows the
service failing its own `eglInitialize`.

The implementation is in `libcommunication_graphics.cpp-ne.so`, SHA-256
`a4e433b18f9f2c8ef9286d598d4e15105f4b37c58e520d63effec9f52ff8e4c9`. Its
Ghidra image coordinates for this library map to raw ELF VAs by subtracting
`0x10000`. The forwarding stubs are at lower addresses; the following Evidence
records target the actual function bodies:

| Function | Ghidra address | Evidence | Observed behavior |
| --- | --- | --- | --- |
| `SimpleSharedMem::open` | `0x13bf0` | `ev_3338004a21a87f9d315c93c068ae87cc5750605b911441b9760ca6c8e917d694` | Creates or opens the named pixel shared-memory object. On a new object it calls `shm_ctl(fd, SHMCTL_ANON|SHMCTL_PHYS, 0, size)`, then `ftruncate`, maps with protection `0xB00` and `MAP_SHARED`, and calls `mlock`. If creation returns `EACCES`, it retries opening the existing object read/write. |
| `RemoteEGLImageSource::init` | `0x14088` | `ev_88c63d4f2b2dcf6f0b80b2b60ab7b6dc26259fef699e1d2fcce304dfd1b75e76` | Gets window buffer dimensions and sets stride to width×4. `SimpleSharedMem::open` creates the pixel object, calls `shm_ctl(fd, 3, 0, width×height×4)` (`SHMCTL_ANON|SHMCTL_PHYS`), `ftruncate`, maps with protection `0xB00` (`READ|WRITE|NOCACHE`) and locks it. `PlainSharedMem` separately creates/maps/locks the 0x48-byte metadata block before calling `createImage`. |
| `RemoteEGLImageSource::createImage` | `0x13768` | `ev_0089e01ca337812fff6a3823dcfb43a8db17609f270c9613f144fca4c1ed2c1c` | Requires `mem_offset64` to succeed for width×height×4 bytes; sets Screen buffer format/size/stride/pointer/physical-address/contiguous properties, attaches it to a pixmap with usage value `14`, calls `update`, then notifies the window. The returned contiguous-byte count is not checked before the Screen buffer is marked contiguous. |
| `RemoteEGLImageSource::update` | `0x13334` | `ev_646307835409b0d9ebb72947643174c591c6057559d16f6874e4ee640cbeb6a7` | Calls `screen_read_window`; after a successful read, queues signal 17 with `sigqueue` to the target PID. On failure it logs both window and shared-buffer sizes. |
| `RemoteEGLImage::init` | `0x12db4` | `ev_d3fa404c886ab30864b4e200cc49cb1d1b88c735fc2016625f20d23584d33d96` | Opens and maps the named metadata block, locks it, then creates the peer image. |
| `RemoteEGLImage::shareMem` | `0x1247c` | `ev_acb6c864cf8823fe904ae44422b190b17265fd9d9db70155faffcdddc6355dd5` | Polls `stat` every 10 ms until the named shared-memory object appears, opens it, then maps width×height×4 bytes. |
| `RemoteEGLImage::createImage` | `0x127d4` | `ev_5ac0163d6afa99e7e6e0b07f2fa24e910dddaa4b29f4fc4c7183f3cca03b1dd8` | Checks metadata byte size against dimensions/stride, requires `mem_offset64`, creates a Screen buffer/pixmap and native-pixmap EGLImage, then binds it to `GL_TEXTURE_EXTERNAL_OES`. Ghidra reports two indirect calls without resolved targets; these remain unknown. |
| `RemoteEGLImage::waitForUpdate` / signal setup | `0x12c74` / `0x12d10` | `ev_c4d47794abea796c09e9348422e1c7211defef0af1b04194b8b34c099702c65a` / `ev_0df6586cd2a8df1a86c8275a7dc34ebab4863e3883ed7fe7084157e971879232` | Waits for and blocks signal 17, then wakes a condition-variable collector. |

LayerManager constructs names with `dev/layermanager_<pid>_img` and
`dev/layermanager_<pid>_cmd`; the shared-memory implementation prefixes these
with `/` for `shm_open`. The receiver polls `stat` every 10 ms until the pixel
block exists, then maps the byte count from its metadata. Its helper has a
local shared-memory, Screen and signal path. These findings provide no
evidence that IP networking is required for this graphics handoff.

The path has not succeeded in QEMU. In particular, static `mem_offset64` calls
do not prove that the emulator can provide the physical-address and
physically-contiguous buffer behavior the native Screen code requests. The
client-side EGLImage functions are present in the shipped helper; this does not
prove HmiMain3D reaches each function. The focused 2026-11-01 Ghidra follow-up
bundle is
`build/idrive6-cache/evidence/libcommunication-graphics-shared-image-2026-11-01-v2.evidence.json`,
with reusable snapshot
`build/idrive6-cache/evidence/libcommunication-graphics-shared-image-2026-11-01.snapshot.json`.

## GLES binding after a successful make-current

The dispatcher first calls the provider's `eglMakeCurrent`. On success with a
non-null context it queries `EGL_CONTEXT_CLIENT_TYPE` (`0x3097`) and client
version (`0x3098`), selects `glesv2-dlls` for OpenGL ES/version2, then installs
per-thread dispatch tables. A provider must support this actual dispatcher
contract, not just return success to the HMI's EGL calls.

The actual GLES2 table loader is Ghidra `0x150a0` (the same named PLT thunk is
at `0x12f00`). It calls `glGetString(GL_VERSION)` and requires an `OpenGL ES `
prefix with major version at least2. It then resolves **142 mandatory exports**
(84 program, 10 query, 48 shared), plus 60 optional names. The HMI's 108 GL
imports therefore understate the symbols needed to load a provider, even
though many loaded functions may never be called by this application.

Evidence: `ghidra-gles-binding-2026-11-01.json` and
`graphics-dispatch-tables-2026-11-01.json` in the evidence cache. Make-current:
`ev_ee0c643d2cac3649a5c3544fde62766f7e7667c8148ac6bbfa0a457edbdb76ae`;
table loader: `ev_a71fe208b1bc2fc48c08e310dc24cb902e2375211ac009106595a26c44df5229`.

### Public GLESv2 frontend dispatch wrappers

A focused Ghidra read of the shipped ARM
`libGLESv2.so.1` (SHA-256
`b2d26ae652e9bd1bc62470dc6e529333b5adbeef3c6d79af9cea7357dc182a2d`)
confirms how the public GLES entry points consume those tables. The wrapper
`glClearColor` at `0x160a4` reads `_gles_overlap_cm_fntbl` from pthread TLS and
calls slot zero. `glShaderBinary` at `0x17d88` reads `_gles2_fntbl` and invokes
the function pointer at table offset `0xc4`. A missing table logs that
`eglMakeCurrent` was not called in the thread, then aborts. The frontend's
`__eglGLES2GetProcAddress` at `0x12924` handles the two `glMultiDraw*EXT`
functions through its separate extension table and otherwise returns the
provider-supplied pointer.

This confirms the integration boundary: preserve the public `libGLESv2.so.1`
and its thread-local wrappers; configure a replacement GLES provider that
supplies the table consumed after a successful make-current. A test that merely
returns a non-null EGL context without installing the correct per-thread GLES
table will abort at the first GLES call. `glShaderBinary` is present in the
native call surface, but this static wrapper does not establish that HmiMain3D
executes it or reveal the format of any uploaded shader. Ghidra Evidence and
snapshot: `ghidra-gles2-dispatcher-2026-11-01.json` and
`ghidra-gles2-dispatcher-2026-11-01.snapshot.json`.

## QNX-to-ANGLE provider draw result

The fresh-guest provider probe reached the ID6 34-slot table through the BMW
QNX EGL frontend, then passed display/config/context/pbuffer creation,
make-current, and QNX GLES TLS dispatch. `glViewport`, `glClearColor`,
`glClear` and `glReadPixels` produced a 2×2 RGBA8 clear readback. QNX checked
all 16 returned bytes; the first was `51,153,229,255`. ANGLE Metal reported
`OpenGL ES 3.0.0` after QNX requested client version2. All 26 EGL/GLES RPCs
completed without error, including swap and cleanup.

Evidence: `build/idrive6-cache/evidence/angle-egl-provider-2026-11-01/draw-run.json`,
`draw-serial.log`, and `draw-host.log`.

This proves the QNX frontend's provider table is live for these EGL/GLES
operations. The provider still has no QNX Screen window surface or post; only
six GLES functions are implemented. The HMI starter was stopped for this
isolated test. No BMW shader binary or BMW UI frame has been rendered.

## HMI link, reflection and first-draw RPC prefix

V31g provides the first runtime evidence for program link/reflection. HmiMain3D
creates program 11, attaches shaders 9 and 10, links it through ANGLE and reads
`GL_LINK_STATUS=1`, `GL_INFO_LOG_LENGTH=0`, `GL_ACTIVE_UNIFORMS=1`,
`GL_ACTIVE_UNIFORM_MAX_LENGTH=5`, `GL_ACTIVE_ATTRIBUTES=1` and
`GL_ACTIVE_ATTRIBUTE_MAX_LENGTH=11`. Its captured source shaders name sampler
`tex0` and attribute `a_Position`. The QMP display remains black because the
following calls still fail in the QNX provider.

The serialized protocol currently assigns these GLES operations:

| Opcode | Request fields / payload | Response or call |
| --- | --- | --- |
| 43 | `a=program`, `b=pname` | `value0=params` |
| 44 | `a=program`, `b=shader` | `glAttachShader` |
| 45 | `a=program` | `glLinkProgram` |
| 46 / 47 | `a=program`, `b=index`, `c=bufsize` | `value0=length`, `value1=size`, `value2=type`, payload=name bytes without NUL; active uniform / attribute |
| 48 / 49 | `a=program`, `b=name byte count`, payload=raw name | `value0=location`; attribute / uniform lookup |
| 50 | `a=program` | `glUseProgram` |
| 51 / 52 | `a=index` | enable / disable vertex attribute array |
| 53 | `a=index`, `b=size`, `c=type`, payload=normalized/stride/offset words | VBO-backed `glVertexAttribPointer` |
| 54 | `a=location`, `b=value` | `glUniform1i` |
| 55 | `a=texture enum` | `glActiveTexture` |
| 56 | `a=mode`, `b=first`, `c=count` | `glDrawArrays` |
| 57 | `a=mode`, `b=count`, `c=type`, payload=offset/client-byte-count and optional index bytes | `glDrawElements` |

Ops 43–45 were exercised successfully in V31g. Ops 46–57 build in both the
QNX provider and host ANGLE server for V31h, but have not yet been exercised by
the guest. The provider keeps client-side vertex arrays fail-fast because it
does not yet serialize those attribute ranges. The analyzed HMI draw helpers
use an array buffer, a bound element buffer, `GL_UNSIGNED_SHORT`, and index
offset0; the next run will verify the live arguments before treating those
static calls as equivalent.

V31h's first guest run omitted `-c=DSI,MOSTSubSystem`. It reached EGL window
and context creation and sent 58 state queries, but no shader, reflection,
attribute, draw or swap call followed; the app/platform threads were dead by
t+65. The new operations remain unvalidated. The comparison run restores the
original communication arguments while retaining the same V31h provider.

V31g evidence: `build/idrive6-cache/evidence/hmi-angle-v31g-capture-2026-11-02/`.
Focused Ghidra draw-helper decompilation:
`build/idrive6-cache/evidence/hmi-angle-v31g-capture-2026-11-02-ghidra-draw.log`.

## Genuine shader finalization boundary

`libImgGLESv2.so`, SHA-256
`d4776fc2f6cf01668ca21b326338960e14b6d69510ca2f0e6b37cf72269ccf69`,
contains a CPU-only UniPatch implementation. The previous parser probe exposed
reflection and opaque PSU roots, but did not establish executable ranges.
Ghidra now joins the parsed root at record `+0x88` to draw setup and finalization:

| Raw VA | Operation and observed contract |
| --- | --- |
| `0x52268` | Constructor allocates/zeros a `0x314`-byte context; installs allocate/free/diagnostic callbacks at offsets0/4/8. The old parser-only fake context is too short for finalization. |
| `0x51e40` | Void texture-format setter copies five words into sampler-specific context state; accepts sampler indices0..15. |
| `0x51f20` / `0x51f28` | Set fragment flags / output count. Native vertex setup requests count1; count setter returns whether the argument is below17. |
| `0x51f80` | Finalizes a parsed PSU root with that context and returns an allocated output object or null. |
| `0x576e8` | Constructs a `0xa4`-byte descriptor followed by instruction and binding arrays in one allocation. |

Native vertex/fragment draw setup reads a **u16 instruction count at output
`+0x0c` and code pointer at `+0x10`**, then copies `count*8` bytes. Secondary
code uses u16 count `+0x1c` and pointer `+0x20`. These are actual output bounds,
unlike opcode-pattern scanning of unfinalized PSU bytes. Register/interface
bindings and portable execution still require separate validation.

These buffers precede native GPU submission, not every final task instruction.
Vertex draw setup builds attribute conversion/fetch instructions, copies the
finalized primary bytes, patches the instruction indexed by descriptor u16
`+0x14` to `0xfa44070000000000`, and appends
`0xfb275000a0200000` through raw helper `0x51980`. Secondary upload prepends
the former word and may append `0xf800014000000000`, then sets a termination
bit on its last instruction. A host adapter must explicitly account for this
glue and recover register bindings; feeding an unannotated code slice to a
translator is insufficient. Evidence: vertex draw setup and
`ev_02730734617d5dc1045ea4f8e812ad336e78712e730e1fe3f4ec6cbb3002a63d`
(secondary upload), `ev_5c8b4f7a0d1208fb5abe65e988075ec626dcf9056234dfe4e559ba975eddefb5`
(append helper).

For a controlled RGBA8 fragment fixture, native `glTexImage2D` selects the
descriptor at raw `0x802b4` for `GL_RGBA`/`GL_UNSIGNED_BYTE`. Texture validation
places that descriptor in GLES context `+0xe6c` (sampler0); fragment setup
forwards descriptor words `+0x0c..+0x1c` = `{4,0,1,2,3}` to UniPatch. With a
full color mask and no alpha test, native fragment setup selects flag1.
This fixture state is explicit and is not a captured home-screen draw state.

The bounded CPU-only probe uses the actual constructor/parser/finalizer for
the packaged `mat_cover_bg` pair, validates that code lies within the returned
allocation, and emits descriptor/code bytes. It neither starts EGL nor
substitutes hand-written shaders. Evidence bundle:
`ghidra-unipatch-contract-2026-11-01.json`.

### CPU replay completed

The native probe exited0 after both stages passed. Its 13,148-byte executable
was read back completely from the guest before execution (SHA-256
`794f207996823452f0d0ed22bf21e974b9a7d29ee5b0c2181b00588a4c5cbf8c`).

| Stage | Returned allocation | Primary instructions | Secondary instructions | Other captured data |
| --- | --- | --- | --- | --- |
| Vertex | 564 bytes | 8 slots / 64 bytes | None | 16 20-byte constant records and 128-bit mask |
| Fragment | 320 bytes | 4 slots / 32 bytes | 3 / 24 bytes | One input record, one constant record, one texture-state record and 128-bit mask |

Both primary buffers start with a zero placeholder at the native patch index0;
it is not evidence of a real zero-word multiply-add operation. The driver adds
the scheduling/attribute glue described above. Field classification of the
remaining bytes succeeds with the pinned comparison grammar; that is still
not a portable execution or checked-pixel result.

`tools/extract-unipatch-capture.py` validates count/pointer bounds, complete
capture chunks, non-overlapping code/table ranges and agreement with the
independent primary-code dump before writing artifacts. It accepted this
capture and rejected five deliberately corrupted cases. Retained inputs:

- `unipatch-finalizer-native-2026-11-01.log`, SHA-256
  `d6700ecf699359dd655b43f78a518403134bc5c3391ec8aa9cd436fe00dd6638`.
- `unipatch-cover-finalized-2026-11-01/manifest.json`, code and opaque tables.
- `unipatch-finalizer-run-2026-11-01.json`, binary/source/driver/shader identities.
- `unipatch-cover-ready` snapshot in `egl-contract-v1.qcow2`, saved with the
  verified helper installed. No new root extraction is needed to repeat it.

These are evidence-cache paths under `build/idrive6-cache/evidence/`, except
the snapshot. Allocations contain process-local pointers and are not expected
to hash identically across boots. The original HMI has not yet drawn a frame.

## Fragment sampler mapping: resource routing known, sampled value unresolved

`libImgGLESv2.so`, SHA-256
`d4776fc2f6cf01668ca21b326338960e14b6d69510ca2f0e6b37cf72269ccf69`, provides
a partial native contract. `SetupUSEFragmentShader` (Ghidra `0x571c8`, raw VA
`0x471c8`) reads the finalized fragment-input descriptor at `+0x44/+0x48` and
texture-state descriptor at `+0x94/+0x98`:

- Input word0 selects the texture lookup path when nonzero.
- Input word2 supplies the lookup/unit index.
- The u16 at record byte `0x0e` selects a texture-state record.
- Input word1 bit0 changes a generated hardware flag; its semantic name remains
  unresolved.
- The setup path consumes fields from the texture state but does not expose a
  CPU-side mapping from returned sample components to shader register PA1.

The fixture's fragment input row is `[1,0,0,0,0,0,4]`, selecting unit0 and
texture-state record0. That state's first two u16 values are `{0,0}`. The
controlled native RGBA8/UNSIGNED_BYTE format descriptor at raw VA `0x802b4`
contains `{4,0,1,2,3}` and is copied into the native texture setup. This proves
the selected format and routing state; it does not prove R/G/B/A ordering into
PA1. The complete typed fixture and evidence links are retained in
`build/idrive6-cache/evidence/unipatch-cover-interface-2026-11-01-v2.json`.

For a native reference draw, a 1×1 texel with bytes `{28,94,158,226}` and
SA9=0.5 gives distinct candidate UNORM8 outputs `{14,47,79,113}` depending on
which sampled channel reaches the scalar consumed by PA1. The final packed lane
must also be read from the native output. A host render of each candidate only
validates that the harness distinguishes them; it cannot establish BMW's
native mapping. The next native observation must be a supported HU draw capture
or a bounded reconstruction of the actual SGX sampling path. Evidence:
`libimg-glesv2-sampler-contract-2026-11-01.evidence.json` and the generated
typed pair artifact.

## Portable arithmetic and candidate raster: host controls complete, native draw open

The standalone harness in `tools/usse-recompiler/` feeds these genuine bytes
to Vita3K's existing USSE visitor below its GXP input adapter. Nix pins the
same Vita3K revision as the grammar and its exact glslang submodule. It rejects
the verified phase placeholder as arithmetic, runs secondary instructions
before primary ones, and makes unknown/rejected instructions and unsupported
diagnostics fail. Upstream assertions stay enabled. No shader body is replaced.

The vertex's seven arithmetic instructions and fragment's three primary plus
three secondary instructions compile into 25,324-byte and 25,372-byte compute
SPIR-V modules. Both pass `spirv-val --target-env vulkan1.0`. A headless Vulkan
runner executes the register computation through MoltenVK 1.4.2 on the Apple
M4 Max. Identity, dense matrix and negative-position controls independently
match column-major matrix multiplication and UV forwarding.

Three fragment controls validate only the decoded PA1×SA9 operation and packed
UNORM8 output. The initial assumption that ordinary RGBA input register order
would make this an alpha×opacity test was not supported: inputs `{.2,.4,.6,.8}`
with opacity `.5` produced `0x33000000`, corresponding to `.4×.5`, rather than
the assumed `.8×.5`. Native sampler channel packing/selection remains to be
established; do not change its interpretation merely to call a texture test
passed. An unmatched instruction control fails before a module is written.

Evidence: `usse-arithmetic-checked-2026-11-01/report.json`, per-case inputs,
readbacks and backend logs; `usse-unmatched-control-2026-11-01/`; and
`vulkan-summary-2026-11-01.log`. These are under the evidence cache. Initial
pipeline creation also emitted a MoltenVK Cereal serialization diagnostic
about four missing bytes in `CompilerMSL::Options`.

The candidate graphics path is now implemented in `tools/usse-recompiler/`:
`idrive-usse-graphics` emits Vulkan vertex/fragment modules around the genuine
finalized instructions, and `idrive-vulkan-graphics` supplies separate stage
uniform banks, a sampled RGBA8 image, a six-vertex quad, an RGBA8 target and
readback. The wrapper assumes location0=position/location1=UV, forwards one
candidate sampled component into PA0.y, and maps the packed MSB to red. These
are adapter hypotheses, not BMW's native contract.

The reproducible four-component synthetic control is retained in
`usse-graphics-candidates-2026-11-01-v4/report.json`. It uses the genuine
`mat_cover_bg` stages, an identity transform, SA9=0.5 and a synthetic 2×2
red/green/blue/white texture. R/G/B each produce 32,768 candidate-red and
32,768 clear pixels; A produces 65,536 candidate-red pixels. Expected quadrant
samples show the host Vulkan vertical texture-origin behavior. For each channel,
a 22,197-byte pipeline cache is serialized and reloaded; fresh and cache-backed
BMP outputs are byte-identical on Apple M4 Max. This validates host raster,
interpolation, sampling, readback and default-option cache reuse for this
control. It does not validate a BMW material texture, native component/packing,
native origin, GLES replacement, Screen buffers or an HMI frame.

The same report includes a non-symmetric transform and SA9 values 0, 0.5 and 1.
The 0.5 case produces 24,082 red pixels and 41,454 clear pixels; the 1.0 case
preserves that mask and scales the red byte from 128 to 255; zero opacity leaves
all 65,536 pixels clear. This confirms the candidate wrapper carries the
genuine matrix and opacity arithmetic through rasterization. It does not settle
native input, varying, or render-target semantics.

The MoltenVK warning is traced to the Nix package pair: MoltenVK 1.4.2 is linked
to SPIRV-Cross 1.4.363.0, while upstream MoltenVK 1.4.2 pins SPIRV-Cross
`6c09849fe88c48eaed08413aa022aaa136a3a057`. The newer MSL options add
`depth_clip_state_buffer_index` and `emulate_depth_clip_enable`, which are not
in MoltenVK's 1.4.2 Cereal serialization list. The observed default-option
cache round trip is byte-identical; cache behavior when depth-clip emulation is
enabled remains open. Keep the diagnostic visible while deciding whether to
align the two Nix package revisions. Source references:
[MoltenVK 1.4.2 pin](https://raw.githubusercontent.com/KhronosGroup/MoltenVK/v1.4.2/ExternalRevisions/SPIRV-Cross_repo_revision),
[MoltenVK archive code](https://raw.githubusercontent.com/KhronosGroup/MoltenVK/v1.4.2/MoltenVK/MoltenVK/GPUObjects/MVKPipeline.mm),
[SPIRV-Cross 1.4.363 options](https://raw.githubusercontent.com/KhronosGroup/SPIRV-Cross/vulkan-sdk-1.4.363.0/spirv_msl.hpp).
