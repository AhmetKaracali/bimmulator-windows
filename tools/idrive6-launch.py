#!/usr/bin/env python3
"""Read the local TOML configuration, stage verified firmware and launch IDrive."""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid


from kombi_firmware import stage_kombi
from kombi_rpm import RAM_SIZE


PACKAGES = {
    "swfl_00002719.bin.007_030_001": "270957bf46bbdb21262c20068cd9c53e329c5ab6ff60a9e397aaea9a8f47cd31",
    "swfl_0000271a.bin.007_030_001": "c313315a499b2c0d49b90e541e74295cb45aebd46b6552a72afbe1dcdc06188d",
    "swfl_00002720.bin.007_030_001": "a9222a2432f5318f06aec563321832a3ba41fde60a4692cbb0cf34317b2f37e1",
}
MODULES = ("head-unit", "6wb")
EXPECTED = {"psdzdata", "cacheDir", "display", "cpuCount", "modules"}
RELEASE = "x20511i-007_030_001-v1"
STAGING_SCHEMA = 2


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(4 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def checked_config(project: Path, file: Path, nix: str) -> dict:
    if not file.is_file():
        raise ValueError(f"Configuration not found: {file}\nCopy idrive6.example.toml to idrive6.toml and set psdzdata.")
    environment = os.environ.copy()
    environment["IDRIVE_CONFIG_FILE"] = str(file)
    result = subprocess.run(
        [nix, "eval", "--impure", "--json", "--file", str(project / "nix/config.nix")],
        cwd=project, env=environment, text=True, capture_output=True,
    )
    if result.returncode:
        raise ValueError(f"Nix could not read {file}:\n{result.stderr.strip()}")
    config = json.loads(result.stdout)
    if not isinstance(config, dict):
        raise ValueError("The TOML configuration must contain key/value settings.")
    extra = set(config) - EXPECTED
    if extra:
        raise ValueError(f"Unknown configuration keys: {', '.join(sorted(extra))}")
    modules = config.setdefault("modules", list(MODULES))
    if (not isinstance(modules, list) or not modules
            or any(module not in MODULES for module in modules)
            or len(set(modules)) != len(modules)):
        raise ValueError('modules must select "head-unit", "6wb", or both without duplicates.')
    psdz = config.get("psdzdata")
    if not isinstance(psdz, str) or not Path(psdz).is_absolute():
        raise ValueError("Set psdzdata to an absolute path to the extracted PSdZData directory.")
    config["psdzdata"] = str(external_path(project, Path(psdz), "psdzdata"))
    config.setdefault("display", "cocoa")
    config.setdefault("cpuCount", 2)
    if config["display"] not in {"cocoa", "none"}:
        raise ValueError("display must be 'cocoa' or 'none'.")
    if type(config["cpuCount"]) is not int or config["cpuCount"] not in {1, 2}:
        raise ValueError("cpuCount must be the integer 1 or 2.")
    cache = config.get("cacheDir")
    if cache is None:
        cache = os.environ.get("XDG_CACHE_HOME")
        cache = Path(cache) / "idrive6" if cache else Path.home() / ".cache/idrive6"
    elif not isinstance(cache, str) or not Path(cache).is_absolute():
        raise ValueError("cacheDir, when set, must be an absolute path.")
    config["cacheDir"] = str(external_path(project, Path(cache), "cacheDir"))
    return config


def external_path(project: Path, path: Path, setting: str) -> Path:
    """Keep firmware and mutable caches out of the Nix source tree."""
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(project)
    except ValueError:
        return resolved
    raise ValueError(
        f"{setting} must be outside the repository ({project}) so firmware and local cache data stay out of the Nix store."
    )


def verify_packages(psdzdata: Path) -> tuple[dict[str, Path], dict[str, str]]:
    root = psdzdata / "swe/swfl"
    paths, digests = {}, {}
    for name, expected in PACKAGES.items():
        path = root / name
        if not path.is_file():
            raise ValueError(
                f"Missing required PSdZData package: {path}\n"
                "Install or extract the matching 4.61.20 HU_NBTEVO packages "
                "00002719, 0000271a and 00002720 (branch 007_030_001)."
            )
        actual = sha256(path)
        if actual != expected:
            raise ValueError(
                f"Unsupported PSdZData package {name}: expected SHA-256 {expected}, got {actual}.\n"
                "This release uses the verified NBTevo_X20511I firmware; use the matching PSdZData extraction."
            )
        paths[name] = path
        digests[name] = actual
    return paths, digests


def stage(project: Path, cache: Path, package_paths: dict[str, Path], digests: dict[str, str]) -> Path:
    final = cache / "firmware" / RELEASE
    marker = final / ".complete.json"
    cache.mkdir(parents=True, exist_ok=True)
    expected_marker = {
        "release": RELEASE,
        "stagingSchema": STAGING_SCHEMA,
        "packages": digests,
    }
    try:
        cached_marker = json.loads(marker.read_text()) if marker.is_file() else None
    except (OSError, json.JSONDecodeError):
        cached_marker = None
    if cached_marker == expected_marker:
        print(f"Using staged firmware: {final}", flush=True)
        return final

    generations = final.parent / ".generations"
    generations.mkdir(parents=True, exist_ok=True)
    fingerprint = hashlib.sha256(json.dumps(expected_marker, sort_keys=True).encode()).hexdigest()[:16]
    generation = generations / f"{RELEASE}-{fingerprint}"
    generation_marker = generation / ".complete.json"
    try:
        staged_marker = json.loads(generation_marker.read_text()) if generation_marker.is_file() else None
    except (OSError, json.JSONDecodeError):
        staged_marker = None
    if staged_marker == expected_marker:
        return publish_generation(final, generation)

    temp = generations / f".staging-{uuid.uuid4().hex}"
    temp.mkdir()
    try:
        firmware = temp / "firmware"
        command = [sys.executable, str(project / "tools/extract-psdz-swfl.py")]
        command.extend(str(package_paths[name]) for name in PACKAGES)
        command.extend(["--output", str(firmware)])
        subprocess.run(command, cwd=project, check=True)

        root = temp / "rootfs"
        subprocess.run([
            sys.executable, str(project / "tools/stage-idrive-rootfs.py"),
            str(firmware / "rootfs"), str(root),
        ], cwd=project, check=True)
        subprocess.run([
            sys.executable, str(project / "tools/stage-psdz-hmi.py"),
            str(firmware / "rootfs"), str(root), "--vehicle", "F32", "--theme", "id6l",
        ], cwd=project, check=True)
        subprocess.run([
            sys.executable, str(project / "tools/materialize-hmi-assetdb.py"),
            str(firmware / "rootfs/opt/hmi/ID5/data/ro"),
            str(root / "opt/hmi/ID5/data/ro"),
            "--psdz-extraction-manifest", str(firmware / "extraction.json"),
            "--manifest", str(temp / "hmi-assetdb-overlay.json"),
        ], cwd=project, check=True)

        required = [
            firmware / "sda2/boot1.ifs",
            root / "bin/mkqnx6fs", root / "bin/devb-loopback", root / "bin/bsdtar",
            root / "opt/sys/etc/starter.cfg", root / "opt/hmi/ID5/bin/HmiMain3D",
            root / "opt/hmi/ID5/lib/libhmicoding.so",
            root / "opt/hmi/ID5/data/ro/bmw/widgetasset/vehicles/F32",
        ]
        absent = [str(path.relative_to(temp)) for path in required if not path.exists()]
        if absent:
            raise ValueError("The firmware extraction is incomplete; missing: " + ", ".join(absent))

        for shader_map in ("hmi-vertex-map-v67.json", "hmi-fragment-map-v112.json"):
            subprocess.run([
                sys.executable, str(project / "tools/prepare-hmi-native-essl-map.py"),
                str(project / "tools/shaders/native-reconstructions" / shader_map),
                str(root), str(project),
            ], cwd=project, stdout=subprocess.DEVNULL, check=True)

        (temp / ".complete.json").write_text(json.dumps(expected_marker, indent=2) + "\n")
        try:
            temp.rename(generation)
        except OSError:
            # A concurrent launch may have published the same immutable generation.
            try:
                concurrent_marker = json.loads(generation_marker.read_text())
            except (OSError, json.JSONDecodeError):
                raise
            if concurrent_marker != expected_marker:
                raise
            shutil.rmtree(temp)
    except BaseException:
        shutil.rmtree(temp, ignore_errors=True)
        raise
    publish_generation(final, generation)
    print(f"Prepared verified firmware cache: {final}", flush=True)
    return final


def publish_generation(final: Path, generation: Path) -> Path:
    """Atomically switch the public cache path to a complete immutable generation."""
    final.parent.mkdir(parents=True, exist_ok=True)
    if final.exists() and not final.is_symlink():
        raise ValueError(
            f"Cache path {final} is an older directory layout. Move it aside or remove it, then retry."
        )
    link = final.parent / f".{RELEASE}-{uuid.uuid4().hex}.link"
    target = os.path.relpath(generation, final.parent)
    os.symlink(target, link)
    try:
        os.replace(link, final)
    finally:
        link.unlink(missing_ok=True)
    return final


def head_unit_command(project, config, firmware):
    environment = os.environ.copy()
    environment.update({
        "IDRIVE_CACHE_DIR": config["cacheDir"],
        "IDRIVE_BOOT_IMAGE": str(firmware / "firmware/sda2/boot1.ifs"),
        "IDRIVE_ROOTFS_TREE": str(firmware / "rootfs"),
        "IDRIVE_REALIZED_ROOTFS": str(firmware / "rootfs"),
        "IDRIVE_QEMU_CPUS": str(config["cpuCount"]),
        "IDRIVE_TCG_THREAD": "single" if config["cpuCount"] == 1 else "multi",
        "IDRIVE_DISPLAY": config["display"],
        "IDRIVE_ANGLE_EGL_SERVER_BIN": os.environ.get("IDRIVE_ANGLE_SERVER", ""),
        "IDRIVE_OTF_CAPTURE": "0",
        "IDRIVE_QNX_PDEBUG": "0",
        "IDRIVE_QNX_HMI_WEB_INSPECTOR": "0",
    })
    profile = project / "profiles/f32-x20511i-id6-light.json"
    command = [sys.executable, str(project / "tools/run-hmi-profile.py"), str(profile),
               "--set", f"IDRIVE_QEMU_CPUS={config['cpuCount']}",
               "--set", f"IDRIVE_TCG_THREAD={environment['IDRIVE_TCG_THREAD']}"]
    return command, environment


def stop_process(process):
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=5)
    except ProcessLookupError:
        process.wait()
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def run_kombi_session(project, cache, config, images, head_unit):
    kombi_qemu = os.environ.get("IDRIVE_KOMBI_QEMU", "qemu-system-mips64el")
    runs = cache / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix="6wb-", dir=runs))
    ram = run / "vehicle.ram"
    gss, flash_config, graphics = map(str, images)
    display = "sdl" if config["display"] == "cocoa" else "none"

    with ExitStack() as cleanup:
        qmp = run / "qmp.sock"
        if len(os.fsencode(qmp)) >= 104:
            sockets = cleanup.enter_context(tempfile.TemporaryDirectory(prefix="idrive6-6wb-", dir="/tmp"))
            qmp = Path(sockets) / "qmp.sock"
        print(f"6WB run artifacts: {run}", flush=True)
        print(f"6WB QEMU management socket: {qmp}", flush=True)

        def start(command, env=None):
            process = subprocess.Popen(command, env=env, start_new_session=True)
            cleanup.callback(stop_process, process)
            return process

        kombi = start([sys.executable, str(project / "tools/kombi-gss-probe.py"), gss,
                       "--config", flash_config, "--graphics-data", graphics, "--qemu", kombi_qemu,
                       "--kss-replay", "--log", str(run / "qemu.log"), "--vehicle-ram", str(ram),
                       "--display", display, "--qmp-socket", str(qmp)])

        deadline = time.monotonic() + 20
        while not (ram.is_file() and ram.stat().st_size == RAM_SIZE and qmp.is_socket()):
            if kombi.poll() is not None or time.monotonic() >= deadline:
                raise RuntimeError(f"6WB failed to start; see {run / 'qemu.log'}")
            time.sleep(0.05)

        simulator = start([sys.executable, str(project / "tools/kombi-sim.py"), "--port", "0",
                           "--vehicle-ram", str(ram)])
        processes = {"6WB": kombi, "vehicle simulator": simulator}
        if head_unit:
            command, env = head_unit
            processes["head unit"] = start(command, env)
        while True:
            for module, process in processes.items():
                if (status := process.poll()) is not None:
                    if status:
                        raise RuntimeError(f"{module} exited with status {status}")
                    if process is simulator:
                        raise RuntimeError("vehicle simulator exited")
                    return 0
            time.sleep(0.1)


def interrupt_session(_signum, _frame):
    raise KeyboardInterrupt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="TOML config; defaults to ./idrive6.toml")
    parser.add_argument("--prepare-only", action="store_true", help="validate and stage firmware without starting QEMU")
    args = parser.parse_args()
    project = Path(os.environ.get("IDRIVE_SOURCE_ROOT", Path.cwd())).resolve()
    config_file = args.config or (project / "idrive6.toml")
    if not config_file.is_absolute():
        config_file = Path.cwd() / config_file
    nix = os.environ.get("IDRIVE_NIX", "nix")
    try:
        config = checked_config(project, config_file.resolve(), nix)
        modules = config["modules"]
        cache = Path(config["cacheDir"])
        psdzdata = Path(config["psdzdata"])
        head_unit = None
        kombi_images = None
        if "head-unit" in modules:
            package_paths, digests = verify_packages(psdzdata)
            firmware = stage(project, cache, package_paths, digests)
            head_unit = head_unit_command(project, config, firmware)
        if "6wb" in modules:
            kombi_images = stage_kombi(psdzdata, cache)
        if args.prepare_only:
            print(f"Firmware verified and staged for {', '.join(modules)}.")
            return 0
        if kombi_images:
            signal.signal(signal.SIGTERM, interrupt_session)
            return run_kombi_session(project, cache, config, kombi_images, head_unit)
        command, env = head_unit
        os.execvpe(command[0], command, env)
    except KeyboardInterrupt:
        return 130
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"idrive6: {error}", file=sys.stderr)
        return 1
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
