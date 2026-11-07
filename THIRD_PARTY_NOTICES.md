# Third-party notices

## QEMU

The OMAP5430 and Capricorn-M patches under `nix/patches/` modify QEMU
11.1.2 source fetched by the pinned Nix package. QEMU is distributed under GPL-2.0-or-later. The upstream
source and its notices are not copied into this repository. The license text
is included in [`licenses/GPL-2.0.txt`](licenses/GPL-2.0.txt).

## Vita3K USSE visitor

The optional shader arithmetic diagnostics in `tools/usse-recompiler/` reuse
the Vita3K USSE visitor from revision
`62727b58322ea7be10aaade575ac9ef82c58f5e8`, fetched by the `shader` Nix
development shell. Vita3K is distributed under GPL-2.0-or-later. Its license
text is included in [`licenses/GPL-2.0.txt`](licenses/GPL-2.0.txt); the upstream
source itself remains external to this repository.

The launcher also depends on QEMU, ANGLE, and other packages built from the
pinned Nixpkgs revision. Their source licenses and notices remain with those
upstream packages; this repository does not vendor their source.
