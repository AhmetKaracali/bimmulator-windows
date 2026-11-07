# QEMU patch workflow

The flake pins QEMU through its locked Nixpkgs revision and checks the QEMU
release before applying the local patch series. The series is four Git format
patches in `nix/patches/qemu/`:

1. OMAP5430 board, DSS, and SDMA.
2. SGX diagnostics and bounded USSE probes.
3. High-speed CDC networking and EHCI diagnostics.
4. The graphics mailbox used by the ANGLE bridge.

To update QEMU, change the Nixpkgs lock deliberately, inspect the QEMU source
version and source changes, then rebase the topic commits. Preserve one
commit per topic and regenerate the patches with `git format-patch`; keep the
order in `nix/qemu-patches.nix` synchronized. Do not edit generated patch
hunks by hand.

To regenerate after rebasing, start from the exact pinned QEMU source, apply
the four patches with `git am`, amend the topic commits, then export the
ordered series again:

```sh
git worktree add /tmp/qemu-patch-work <qemu-base>
cd /tmp/qemu-patch-work
git am /path/to/idrive6-share/nix/patches/qemu/*.patch
# Rebase or amend the four topic commits here.
git format-patch --no-signature --output-directory /tmp/idrive6-patches \
  <qemu-base>..HEAD
```

During a behavior-preserving rebase, retain the previous series temporarily
and apply both versions to the same QEMU base. Compare the resulting Git tree
IDs and require an exact match before replacing the checked-in patches. The
release cleanup compared the original 28 patches and the four topic patches
against QEMU base `16b98b5957d957c7052afb55c5524c49e8022f29`; both produced
tree `e98667aea063c96bae2046f44dfa2e2fc775cc53`.

After the tree comparison, run the QEMU SDMA and VSYNC tests and build the
patched package with `nix build .#qemu-omap5`. A behavioral change needs a
focused test and a description in the corresponding patch commit.

The machine only implements the modeled registers and transfer paths covered
by the tests. Probe options must remain explicit about assumptions and must
not suggest full PowerVR execution.


## Capricorn-M

The Bosch 6WB graphics processor uses the separate `qemu-capricorn-m`
package. Apply the patch in `nix/patches/capricorn-m/` to the pinned QEMU
base on its own. The OMAP5430 series and the head-unit launcher use their
existing package. [6WB launch instructions](../README.md#experimental-6wb-cluster-and-hud)
