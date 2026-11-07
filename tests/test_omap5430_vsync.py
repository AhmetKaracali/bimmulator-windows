"""Check DISPC frame timing, W1C status, and interrupt masking."""
import os
import shutil
import socket
import tempfile
import time
from pathlib import Path
import unittest
from test_omap5430_sdma import QTest


DISPC = 0x58001000
FRAME_NS = 16666667


class OMAP5430VsyncTests(unittest.TestCase):
    def setUp(self):
        qemu = os.environ.get("IDRIVE_QEMU") or shutil.which("qemu-system-arm")
        if not qemu:
            self.skipTest("patched QEMU is available in the Nix development shell")
        self.q = QTest(qemu)
        self.addCleanup(self.q.close)
        self.q.command("irq_intercept_out /machine/peripheral/omap5-dss sysbus-irq")

    def frame(self):
        self.q.command(f"clock_step {FRAME_NS}")

    def test_digital_vsync_latches_and_acknowledges(self):
        self.q.write(DISPC + 0x1c, 0x0c)
        self.q.write(DISPC + 0x40, 0x42)  # digital output + GO
        self.assertEqual(self.q.read(DISPC + 0x18), 0)
        self.frame()
        self.assertEqual(self.q.read(DISPC + 0x18), 4)
        self.assertEqual(self.q.read(DISPC + 0x40), 2)
        self.assertIn("IRQ raise 1", self.q.irqs)
        self.q.write(DISPC + 0x1c, 0)
        self.assertIn("IRQ lower 1", self.q.irqs)
        self.assertEqual(self.q.read(DISPC + 0x18), 4)
        self.q.write(DISPC + 0x18, 4)
        self.q.write(DISPC + 0x1c, 0x0c)
        self.frame()
        self.assertEqual(self.q.read(DISPC + 0x18), 8)
        self.q.write(DISPC + 0x18, 0xffffffff)
        self.assertEqual(self.q.read(DISPC + 0x18), 0)
        self.q.write(DISPC + 0x40, 0)
        self.frame()
        self.assertEqual(self.q.read(DISPC + 0x18), 0)

    def test_lcd_vsync_clears_go(self):
        self.q.write(DISPC + 0x1c, 2)
        self.q.write(DISPC + 0x40, 0x21)
        self.frame()
        self.assertEqual(self.q.read(DISPC + 0x40), 1)
        self.assertEqual(self.q.read(DISPC + 0x18), 2)
        self.assertIn("IRQ raise 1", self.q.irqs)


class OMAP5430ScanoutTests(unittest.TestCase):
    def test_graphics_plane_uses_rgb24_unpacked(self):
        qemu = os.environ.get("IDRIVE_QEMU") or shutil.which("qemu-system-arm")
        if not qemu:
            self.skipTest("patched QEMU is available in the Nix development shell")
        with tempfile.TemporaryDirectory(prefix="idrive-qtest-") as directory:
            monitor = str(Path(directory) / "monitor.sock")
            shot = str(Path(directory) / "screen.ppm")
            q = QTest(qemu, f"unix:{monitor},server=on,wait=off")
            self.addCleanup(q.close)
            q.write(0x80000000, 0xffff0000)  # unpacked red, unused high byte
            q.write(DISPC + 0x7c, (63 << 16) | 63)
            q.write(DISPC + 0x80, 0x80000000)
            q.write(DISPC + 0x8c, (63 << 16) | 63)
            q.write(DISPC + 0xa0, (8 << 1) | 1)
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(5)
                for attempt in range(50):
                    try:
                        client.connect(monitor)
                        break
                    except FileNotFoundError:
                        time.sleep(0.02)
                else:
                    self.fail("QEMU monitor socket did not appear")
                def read_prompt():
                    output = b""
                    while b"(qemu)" not in output:
                        chunk = client.recv(4096)
                        if not chunk:
                            self.fail("QEMU monitor closed unexpectedly")
                        output += chunk
                read_prompt()
                client.sendall(f"screendump {shot}\n".encode())
                read_prompt()
            image = Path(shot).read_bytes()
            magic, geometry, maximum, pixels = image.split(b"\n", 3)
            self.assertEqual((magic, geometry, maximum), (b"P6", b"64 64", b"255"))
            self.assertEqual(pixels[:3], bytes((255, 0, 0)))


if __name__ == "__main__":
    unittest.main()
