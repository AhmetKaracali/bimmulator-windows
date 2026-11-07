"""Check that suppressing the hardware DSP logger preserves IFS argument layout."""

import importlib.util
from pathlib import Path
import struct
import unittest


SPEC = importlib.util.spec_from_file_location(
    "embed_root", Path(__file__).parents[1] / "tools" / "embed-qnx6-rootfs.py"
)
embed_root = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(embed_root)


class BootstrapTests(unittest.TestCase):
    def test_debug_shell_preserves_login_process_layout(self):
        marker = b"/boot/bin/login\0login\0"
        script = bytearray(b"prefix" + marker + b"PATH=/boot/bin:\0")
        original_size = len(script)
        embed_root.enable_debug_shell(script)
        self.assertEqual(len(script), original_size)
        args = bytes(script[6:6 + len(marker)]).split(b"\0")
        self.assertEqual(len(args), 3)
        self.assertEqual(args[0], b"/boot/bin/ksh")
        self.assertTrue(args[1].startswith(b"ksh"))
        self.assertEqual(script[-len(b"PATH=/boot/bin:\0"):], b"PATH=/boot/bin:\0")

    def test_elf_library_dependencies(self):
        elf = bytearray(512)
        elf[:6] = b"\x7fELF\x01\x01"
        struct.pack_into("<I", elf, 28, 52)
        struct.pack_into("<HH", elf, 42, 32, 2)
        struct.pack_into("<IIIIIIII", elf, 52, 1, 0, 0x1000, 0, 512, 512, 4, 4096)
        struct.pack_into("<IIIIIIII", elf, 84, 2, 128, 0x1080, 0, 32, 32, 4, 4)
        names = b"\0libc.so.3\0libxml2.so.1\0"
        elf[256:256 + len(names)] = names
        struct.pack_into("<IIIIIIII", elf, 128, 5, 0x1100, 1, 1,
                         1, names.index(b"libxml2"), 0, 0)
        self.assertEqual(embed_root.elf_needed(bytes(elf)), ["libc.so.3", "libxml2.so.1"])

    def test_truncated_elf_is_rejected(self):
        with self.assertRaises(RuntimeError):
            embed_root.elf_needed(b"\x7fELF\x01\x01")

    def test_dsp_logger_replacement_preserves_layout(self):
        label = b"starting DSP register logger...\n\0"
        args = b"/boot/bin/gs\0gs\0/boot/bin/memcpy_utility.out\0"
        environment = b"PATH=/boot/bin:/bin\0LD_LIBRARY_PATH=/boot/lib\0"
        script = bytearray(label + args + environment)
        original_size = len(script)
        embed_root.disable_dsp_logger(script)
        self.assertEqual(len(script), original_size)
        self.assertEqual(script[-len(environment):], environment)
        replacement = bytes(script[len(label):-len(environment)]).split(b"\0")
        self.assertEqual(len(replacement), 4)
        self.assertEqual(replacement[:2], [b"/boot/bin/sleep", b"sleep"])
        self.assertEqual(int(replacement[2]), 0)
        self.assertNotIn(b"memcpy_utility.out", script)

    def test_unknown_logger_layout_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "DSP logger"):
            embed_root.disable_dsp_logger(bytearray(b"unrelated boot script"))


if __name__ == "__main__":
    unittest.main()
