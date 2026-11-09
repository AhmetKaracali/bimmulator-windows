{
  description = "F32 BMW iDrive 6 emulator with user-supplied PSdZData";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs, ... }:
    let
      # WSL2 port (branch wsl-linux): upstream's verified host is aarch64-darwin;
      # this branch builds for x86_64-linux under WSL2 on Windows (display via WSLg).
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        overlays = [ self.overlays.default ];
      };
      source = pkgs.lib.cleanSourceWith {
        src = ./.;
        filter = path: _type:
          let
            name = baseNameOf path;
            localData = [
              ".git"
              "build"
              "captures"
              "firmware"
              "idrive6-cache"
              "idrive6.toml"
              "psdzdata"
            ];
          in !(builtins.elem name localData);
      };
      qemuPatches = {
        omap5-core = ./nix/patches/qemu/0001-omap5-core.patch;
        sgx-diagnostics = ./nix/patches/qemu/0002-sgx-diagnostics.patch;
        usb-network = ./nix/patches/qemu/0003-usb-network.patch;
        graphics-mailbox = ./nix/patches/qemu/0004-graphics-mailbox.patch;
      };
      qemuPatchSeries = import ./nix/qemu-patches.nix { inherit qemuPatches; };
      qemu = pkgs.qemu-omap5;
      shaderPython = pkgs.python3.withPackages (pythonPackages: [
        pythonPackages.capstone
        pythonPackages.pyyaml
      ]);
      # Match the pinned Vita3K translator's private builder API used by the
      # optional, host-side shader arithmetic diagnostics.
      glslangBuilder = pkgs.fetchFromGitHub {
        owner = "KhronosGroup";
        repo = "glslang";
        rev = "fc9889c889561c5882e83819dcaffef5ed45529b";
        hash = "sha256-HwFP4KJuA+BMQVvBWV0BCRj9U5I3CLEU+5bBtde2f6w=";
      };
      vitaShaderSource = pkgs.fetchFromGitHub {
        owner = "Vita3K";
        repo = "Vita3K";
        rev = "62727b58322ea7be10aaade575ac9ef82c58f5e8";
        hash = "sha256-iZoBhLMQy6k9u7ww7XPe3youFeWFUa3Wvv2gDjsobPo=";
      };
      angleServer = pkgs.stdenv.mkDerivation {
        pname = "idrive6-angle-rpc-server";
        version = "1";
        src = source;
        nativeBuildInputs = [ pkgs.clang ];
        buildInputs = [ pkgs.angle ];
        buildPhase = ''
          runHook preBuild
          clang++ -std=c++17 -O2 -Wall -Wextra -Werror \
            -I${pkgs.angle}/include -I$src/tools \
            $src/tools/angle-egl-rpc-server.cpp \
            -L${pkgs.angle}/lib -Wl,-rpath,${pkgs.angle}/lib -lEGL -lGLESv2 \
            -o angle-egl-rpc-server
          runHook postBuild
        '';
        installPhase = ''
          mkdir -p $out/bin
          install -m755 angle-egl-rpc-server $out/bin/angle-egl-rpc-server
        '';
      };
      launcher = pkgs.writeShellApplication {
        name = "idrive6";
        runtimeInputs = [
          pkgs.python3
          pkgs.nix
          pkgs.coreutils
          pkgs.findutils
          pkgs.gnugrep
          pkgs.gawk
          pkgs.gnused
          pkgs.gnutar
          pkgs.gzip
          pkgs.bash
          pkgs.lzo
          pkgs.llvmPackages.lld
          pkgs.llvmPackages.llvm
          pkgs.clang
          qemu
          angleServer
        ];
        text = ''
          export IDRIVE_SOURCE_ROOT="$PWD"
          export IDRIVE_QEMU="${qemu}/bin/qemu-system-arm"
          export IDRIVE_KOMBI_QEMU="${pkgs.qemu-capricorn-m}/bin/qemu-system-mips64el"
          export IDRIVE_QNX_CLANG="${pkgs.llvmPackages.clang-unwrapped}/bin/clang"
          export IDRIVE_ANGLE_ROOT="${pkgs.angle}"
          export IDRIVE_LZO_LIBRARY="${pkgs.lzo}/lib/liblzo2${pkgs.stdenv.hostPlatform.extensions.sharedLibrary}"
          export IDRIVE_HOST_CXX="${pkgs.clang}/bin/clang++"
          export IDRIVE_ANGLE_SERVER="${angleServer}/bin/angle-egl-rpc-server"
          export IDRIVE_NIX="${pkgs.nix}/bin/nix"
          exec ${pkgs.python3}/bin/python3 ${source}/tools/idrive6-launch.py "$@"
        '';
      };
    in
    {
      overlays.default = final: prev: {
        qemu-capricorn-m =
          assert prev.qemu.version == "11.1.2";
          (prev.qemu.override {
            # Darwin's qemu-kvm alias requires the native ARM64 target.
            hostCpuTargets = [ "mips64el-softmmu" "aarch64-softmmu" ];
            sdlSupport = true;
            openGLSupport = false;
          }).overrideAttrs (old: {
            patches = (old.patches or [ ]) ++ [
              ./nix/patches/capricorn-m/0001-add-capricorn-m-machine.patch
            ];
            # WSL2 port: on x86_64-linux the qemu-kvm alias points at the absent x86_64 target.
            postInstall = (old.postInstall or "") + "\nrm -f $out/bin/qemu-kvm\n";
          });

        qemu-omap5 =
          assert prev.qemu.version == "11.1.2";
          (prev.qemu.override {
            # The app needs ARMv7, and nixpkgs' Darwin package creates qemu-kvm
            # as an alias for the host's aarch64 emulator.
            hostCpuTargets = [ "arm-softmmu" "aarch64-softmmu" ];
          }).overrideAttrs (old: {
            patches = (old.patches or [ ]) ++ qemuPatchSeries;
            # WSL2 port: on x86_64-linux the qemu-kvm alias points at the absent x86_64 target.
            postInstall = (old.postInstall or "") + "\nrm -f $out/bin/qemu-kvm\n";
          });
      };

      packages.${system} = {
        default = launcher;
        idrive6 = launcher;
        qemu-omap5 = qemu;
        qemu-capricorn-m = pkgs.qemu-capricorn-m;
        angle-egl-rpc-server = angleServer;
      };

      apps.${system}.idrive6 = {
        type = "app";
        program = "${launcher}/bin/idrive6";
      };

      devShells.${system} = {
        default = pkgs.mkShell {
          packages = [
            qemu
            angleServer
            pkgs.angle
            pkgs.lzo
            pkgs.python3Packages.capstone
            pkgs.python3Packages.pyyaml
            pkgs.clang
            pkgs.llvmPackages.clang-unwrapped
            pkgs.llvmPackages.llvm
            pkgs.llvmPackages.lld
            pkgs.git
          ];
          IDRIVE_QEMU = "${qemu}/bin/qemu-system-arm";
          IDRIVE_ANGLE_SERVER = "${angleServer}/bin/angle-egl-rpc-server";
          IDRIVE_ANGLE_ROOT = "${pkgs.angle}";
          IDRIVE_HOST_CXX = "${pkgs.clang}/bin/clang++";
        };

        shader = pkgs.mkShell {
          packages = with pkgs; [
            shaderPython
            clang
            lld
            cmake
            ninja
            spirv-tools
            spirv-cross
            vulkan-tools
          ];
          buildInputs = with pkgs; [ fmt vulkan-loader vulkan-headers ]
            ++ pkgs.lib.optionals pkgs.stdenv.hostPlatform.isDarwin [ pkgs.moltenvk ];
          IDRIVE_QNX_CLANG = "${pkgs.llvmPackages.clang-unwrapped}/bin/clang";
          IDRIVE_GLSLANG_INCLUDE = "${glslangBuilder}";
          IDRIVE_VITA3K_SOURCE = "${vitaShaderSource}";
          shellHook = pkgs.lib.optionalString pkgs.stdenv.hostPlatform.isDarwin ''
            export VK_DRIVER_FILES="${pkgs.moltenvk}/share/vulkan/icd.d/MoltenVK_icd.json"
          '';
        };
      };
    };
}
