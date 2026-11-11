#!/usr/bin/env bash
# One-time setup inside WSL2 (Ubuntu): packages, Nix with flakes, the patched QEMU/ANGLE launcher,
# Mesa lavapipe (software Vulkan for ANGLE) and an idrive6.toml.
#
#   wsl/setup.sh /path/to/psdzdata      # folder that contains swe/swfl
#
# The first build compiles QEMU with the OMAP5/SGX patches and can take 30-90 minutes.
set -euo pipefail
source "$(dirname "$0")/env.sh"
PSDZ="${1:-}"

echo "[1/6] Ubuntu packages"
as_root apt-get update -qq
as_root env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git curl xz-utils python3 ca-certificates >/dev/null

echo "[2/6] systemd (needed by the Nix daemon)"
if [ "$(cat /proc/1/comm)" != "systemd" ]; then
    cat >&2 <<'MSG'
systemd is not running in this WSL distribution. Add this to /etc/wsl.conf:
    [boot]
    systemd=true
then run `wsl --shutdown` in Windows and start this script again.
MSG
    exit 1
fi

echo "[3/6] Nix (multi-user, flakes)"
nix_env
if ! command -v nix >/dev/null 2>&1; then
    curl -fsSL https://nixos.org/nix/install -o /tmp/nix-install.sh
    sh /tmp/nix-install.sh --daemon --yes
    nix_env
fi
if ! grep -qs "flakes" /etc/nix/nix.conf; then
    echo "experimental-features = nix-command flakes" | as_root tee -a /etc/nix/nix.conf >/dev/null
    as_root systemctl restart nix-daemon || true
fi
nix --version

echo "[4/6] Build the launcher (QEMU OMAP5 + Capricorn-M, ANGLE RPC server)"
mkdir -p "$IDRIVE_HOME" "$OVERLAY_DIR"
cd "$REPO"
nix build .#default --out-link "$IDRIVE_HOME/launcher" -L

echo "[5/6] Mesa lavapipe (WSL2 offers ANGLE no usable Vulkan GPU driver)"
nix build .#mesa --out-link "$MESA_LINK"
ls "$MESA_LINK"/share/vulkan/icd.d/lvp_icd.*.json

echo "[6/6] idrive6.toml"
if [ ! -f "$IDRIVE_CONFIG" ]; then
    cat > "$IDRIVE_CONFIG" <<TOML
# Extracted PSdZData folder (must contain swe/swfl with the HU 006.027.001 packages).
psdzdata = "${PSDZ:-/path/to/psdzdata}"
modules = ["head-unit"]
display = "gtk"
cpuCount = 2
TOML
fi
cat "$IDRIVE_CONFIG"
if grep -q "/path/to/psdzdata" "$IDRIVE_CONFIG"; then
    echo "Edit psdzdata in $IDRIVE_CONFIG before the first start." >&2
fi
echo
echo "Done. Next: wsl/emulator.sh snapshot   (first boot, ~7 min, saves a snapshot)"
