"""Exercise SWFL reconstruction and rejection of incomplete/unsafe containers."""

import hashlib
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
import zlib


SPEC = importlib.util.spec_from_file_location(
    "extract_swfl", Path(__file__).parents[1] / "tools" / "extract-psdz-swfl.py"
)
swfl = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(swfl)


def record(kind, ident, part, data):
    return struct.pack("<BHIH", kind, ident, len(data), part) + data


def metadata(ident, count, name, append=False):
    text = f"TargetPath=/fs/sda0/repository/istep/lib/;Name={name};Tag=FIL;CPU=Omap;"
    if append:
        text += "Append=On;"
    return record(2, ident, count, text.encode())


class ExtractSWFLTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.package = self.base / "firmware.bin"
        self.output = self.base / "output"
        self.output.mkdir()
        self.inventory = {"packages": [], "files": {}, "skipped_targets": []}

    def extract(self, records):
        self.package.write_bytes(swfl.HEADER + records)
        swfl.extract(self.package, self.output, self.inventory)

    def test_multipart_and_append_reconstruct_one_file(self):
        self.extract(
            metadata(1, 2, "driver.so", append=True)
            + record(4, 1, 1, b"first") + record(4, 1, 2, b"second")
            + metadata(2, 1, "driver.so", append=True) + record(4, 2, 1, b"third")
        )
        self.assertEqual((self.output / "rootfs/lib/driver.so").read_bytes(), b"firstsecondthird")

    def test_no_payload_update_command_is_ignored(self):
        self.extract(record(2, 1, 0, b"Tag=NOR_ERASE;CPU=Jacinto;Address=00100000;"))
        self.assertEqual(self.inventory["files"], {})

    def test_incomplete_payload_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "incomplete payload"):
            self.extract(metadata(1, 2, "driver.so") + record(4, 1, 1, b"first"))

    def test_truncated_record_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "truncated record"):
            self.extract(record(4, 1, 1, b"payload")[:-1])

    def test_parent_path_is_rejected(self):
        with self.assertRaises(ValueError):
            self.extract(metadata(1, 1, "../outside") + record(4, 1, 1, b"data"))

    def test_manifest_sha1_crc_and_permissions(self):
        self.extract(metadata(1, 1, "driver.so") + record(4, 1, 1, b"driver"))
        info = self.output / "rootfs/info"
        info.mkdir()
        info.joinpath("manifest_system.xml").write_text(
            '<LinkManifest><LinkData root="/fs/sda0/repository/istep">'
            '<dir name="lib" mod="775"><file name="driver.so" mod="775" '
            f'md5="{hashlib.sha1(b"driver").hexdigest()}" '
            f'crc="{zlib.crc32(b"driver"):08x}" /></dir></LinkData></LinkManifest>'
        )
        result = swfl.verify_manifests(self.output)
        self.assertEqual(result["verified_files"], 1)
        self.assertEqual(result["missing_files"], [])
        self.assertEqual((self.output / "rootfs/lib/driver.so").stat().st_mode & 0o777, 0o775)
        (self.output / "rootfs/lib/driver.so").write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            swfl.verify_manifests(self.output)


if __name__ == "__main__":
    unittest.main()
