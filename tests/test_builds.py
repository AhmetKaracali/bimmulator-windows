"""Consistency of the build registry, shader library and pins (no firmware needed)."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import buildinfo  # noqa: E402

spec = importlib.util.spec_from_file_location("shader_library", REPO / "tools/shader-library.py")
shader_library = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shader_library)


class BuildRegistryTests(unittest.TestCase):
    def test_builds_load_and_are_unique(self):
        builds = buildinfo.all_builds()
        self.assertGreaterEqual(len(builds), 2)
        self.assertIn(buildinfo.DEFAULT_BUILD, [b.id for b in builds])
        packages = [name for b in builds for name in b["packages"]]
        self.assertEqual(len(packages), len(set(packages)), "a package belongs to two builds")
        self.assertEqual(len({b["release"] for b in builds}), len(builds), "release names must differ")

    def test_build_files_are_complete(self):
        for build in buildinfo.all_builds():
            with self.subTest(build=build.id):
                self.assertTrue(build.profile().is_file())
                self.assertTrue((build.dir / "shader-pins.json").is_file())
                if build["status"] != "draft":
                    self.assertTrue((build.dir / "signatures.json").is_file())
                for key in ("binaries", "coding", "bench_input_patches", "resource_language_sites",
                            "controller", "assetdb_domains", "variantregistry_paths"):
                    self.assertIn(key, build)
                for patch in build["coding"]["code_patches"] + build["bench_input_patches"]:
                    offset, expected, replacement = buildinfo.patch_triple(patch)
                    self.assertEqual(len(expected), len(replacement))
                self.assertEqual(len(build["controller"]["pop_callers"]), 3)

    def test_profiles_use_composed_shader_maps(self):
        for build in buildinfo.all_builds():
            for profile in (build.dir / "profiles").glob("*.json"):
                settings = json.loads(profile.read_text())["settings"]
                with self.subTest(profile=str(profile)):
                    self.assertEqual(settings["IDRIVE_HMI_VERTEX_SHADER_MAP_MANIFEST"],
                                     "{shader_maps_dir}/hmi-vertex-map.json")
                    self.assertIn(build["release"], json.dumps(json.loads(profile.read_text())["paths"]))

    def test_unknown_build_is_reported(self):
        with self.assertRaises(ValueError):
            buildinfo.get("hu-does-not-exist")


class ProgramFingerprintTests(unittest.TestCase):
    def test_container_hash_and_compiler_field_are_ignored(self):
        data = bytearray(bytes.fromhex("38b4fa10") + bytes(range(4, 120)))
        other = bytearray(data)
        other[4:8] = b"\xff\xff\xff\xff"
        other[60] ^= 0x55
        self.assertEqual(buildinfo.program_sha256(bytes(data)), buildinfo.program_sha256(bytes(other)))
        other[80] ^= 1   # program byte
        self.assertNotEqual(buildinfo.program_sha256(bytes(data)), buildinfo.program_sha256(bytes(other)))


class ShaderLibraryTests(unittest.TestCase):
    def test_library_entries_are_versioned_and_sources_exist(self):
        for stage in shader_library.STAGES:
            library = shader_library.load_library(stage)
            self.assertEqual(library["library_schema"], shader_library.LIBRARY_SCHEMA)
            self.assertIsInstance(library["library_version"], int)
            for entry in library["mappings"]:
                self.assertIn("program_sha256", entry)
                self.assertTrue((REPO / entry["source_path"]).is_file(), entry["source_path"])

    def test_pins_reference_library_programs(self):
        programs = {(s, e["asset_path"], e["program_sha256"]) for s in shader_library.STAGES
                    for e in shader_library.load_library(s)["mappings"]}
        for build in buildinfo.all_builds():
            pins = build.shader_pins()
            for stage in shader_library.STAGES:
                for asset, pin in pins[stage].items():
                    self.assertIn((stage, asset, pin["program_sha256"]), programs, f"{build.id} {asset}")

    def test_compose_uses_the_builds_native_hashes(self):
        build = buildinfo.get(buildinfo.DEFAULT_BUILD)
        with tempfile.TemporaryDirectory() as directory:
            args = type("Args", (), {"build": build.id, "out": Path(directory), "rootfs": None})
            shader_library.cmd_compose(args)
            pins = build.shader_pins()
            for stage in shader_library.STAGES:
                composed = json.loads((Path(directory) / f"hmi-{stage}-map.json").read_text())
                self.assertEqual(len(composed["mappings"]), len(pins[stage]))
                for entry in composed["mappings"]:
                    if "shader_sha256" in entry:
                        self.assertEqual(entry["shader_sha256"], pins[stage][entry["asset_path"]]["shader_sha256"])


if __name__ == "__main__":
    unittest.main()
