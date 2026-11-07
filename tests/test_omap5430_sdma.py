"""Exercise OMAP5 SDMA transfers and IRQs using QEMU's qtest protocol."""

import os
import select
import shutil
import subprocess
import unittest


SDMA = 0x4A056000
RAM = 0x80000000


class QTest:
    def __init__(self, qemu, monitor="none"):
        self.process = subprocess.Popen(
            [qemu, "-machine", "omap5430", "-accel", "qtest", "-m", "256",
             "-smp", "1", "-display", "none", "-monitor", monitor,
             "-serial", "none", "-qtest", "stdio", "-qtest-log", "/dev/null"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            bufsize=0,
        )
        self.buffer = b""
        self.irqs = []

    def command(self, value):
        self.process.stdin.write((value + "\n").encode())
        while True:
            while b"\n" not in self.buffer:
                readable, _, _ = select.select([self.process.stdout], [], [], 10)
                if not readable:
                    raise AssertionError(f"qtest timed out on {value!r}")
                chunk = os.read(self.process.stdout.fileno(), 4096)
                if not chunk:
                    error = self.process.stderr.read().decode(errors="replace")
                    raise AssertionError(f"QEMU exited while running {value!r}: {error}")
                self.buffer += chunk
            line, self.buffer = self.buffer.split(b"\n", 1)
            line = line.decode().strip()
            if line.startswith("IRQ "):
                self.irqs.append(line)
            elif line.startswith("OK"):
                return line
            else:
                raise AssertionError(f"qtest {value!r}: {line}")

    def write(self, addr, value):
        self.command(f"writel {addr:#x} {value:#x}")

    def read(self, addr):
        return int(self.command(f"readl {addr:#x}").split()[1], 0)

    def advance(self):
        self.command("clock_step 10000000")

    def close(self):
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            stream.close()


class OMAP5430SDMATests(unittest.TestCase):
    def setUp(self):
        qemu = os.environ.get("IDRIVE_QEMU") or shutil.which("qemu-system-arm")
        if not qemu:
            self.skipTest("patched QEMU is available in the Nix development shell")
        self.q = QTest(qemu)
        self.addCleanup(self.q.close)
        self.q.command("irq_intercept_out /machine/sdma sysbus-irq")
        self.assertEqual(self.q.read(SDMA), 0x40)

    def setup_channel(self, channel, src, dst, elements=1, cicr=8):
        base = SDMA + 0x80 + channel * 0x60
        for offset, value in ((0x08, cicr), (0x10, 2), (0x14, elements),
                              (0x18, 1), (0x1c, src), (0x20, dst)):
            self.q.write(base + offset, value)
        return base

    def test_copy_status_and_irq_acknowledgement(self):
        words = [0x12345678, 0xCAFEBABE, 0x5A00FF00]
        for i, value in enumerate(words):
            self.q.write(RAM + 4 * i, value)
        self.q.write(SDMA + 0x18, 1 << 2)
        base = self.setup_channel(2, RAM, RAM + 0x1000, len(words))
        self.q.write(base, 0x01005080)
        self.q.advance()
        self.assertEqual([self.q.read(RAM + 0x1000 + 4 * i) for i in range(3)], words)
        self.assertEqual(self.q.read(base + 0x0c) & 0x28, 0x28)
        self.assertEqual(self.q.read(SDMA + 0x08), 1 << 2)
        self.assertIn("IRQ raise 0", self.q.irqs)
        self.q.write(SDMA + 0x18, 0)
        self.assertEqual(self.q.read(SDMA + 0x08), 1 << 2)
        self.assertIn("IRQ lower 0", self.q.irqs)
        self.q.write(SDMA + 0x18, 1 << 2)
        self.assertEqual(self.q.irqs.count("IRQ raise 0"), 2)
        self.q.write(base + 0x0c, 0x28)
        self.assertEqual(self.q.read(base + 0x0c), 0)
        self.assertEqual(self.q.read(SDMA + 0x08), 1 << 2)
        self.q.write(SDMA + 0x08, 1 << 2)
        self.assertEqual(self.q.read(SDMA + 0x08), 0)
        self.assertIn("IRQ lower 0", self.q.irqs)

    def test_dma_writes_to_dmm_registers(self):
        self.q.write(RAM, 0x88888888)
        base = self.setup_channel(0, RAM, 0x4E000420)
        self.q.write(base, 0x01005080)
        self.q.advance()
        self.assertEqual(self.q.read(0x4E000420), 0x88888888)
        self.assertEqual(self.q.read(base + 0x0c) & 0x28, 0x28)

    def test_dmm_manual_refill_status_and_write_one_to_clear(self):
        dmm = 0x4E000000
        self.q.write(dmm + 0x4A0, 1)
        self.q.write(dmm + 0x4A0, 2)
        self.assertEqual(self.q.read(dmm + 0x4A0), 3)
        self.q.write(dmm + 0x4B0, 1)
        self.assertEqual(self.q.read(dmm + 0x4A0), 2)
        self.q.write(dmm + 0x508, 1)
        self.assertEqual(self.q.read(dmm + 0x480) & 3, 3)
        self.assertEqual(self.q.read(dmm + 0x490) & 3, 3)
        self.q.write(dmm + 0x490, 1)
        self.assertEqual(self.q.read(dmm + 0x480) & 3, 2)
        self.assertEqual(self.q.read(dmm + 0x490) & 3, 2)
        self.q.write(dmm + 0x490, 2)
        self.assertEqual(self.q.read(dmm + 0x480) & 3, 0)
        self.assertEqual(self.q.read(dmm + 0x490) & 3, 0)

    def test_unsupported_indexed_mode_reports_error_without_copy(self):
        self.q.write(RAM, 0xDEADBEEF)
        self.q.write(SDMA + 0x1c, 1 << 1)
        base = self.setup_channel(1, RAM, RAM + 0x1000, cicr=0x100)
        self.q.write(base, 0x6080)  # indexed source, incrementing destination
        self.q.advance()
        self.assertEqual(self.q.read(RAM + 0x1000), 0)
        self.assertEqual(self.q.read(base + 0x0c), 0x100)
        self.assertEqual(self.q.read(SDMA + 0x0c), 1 << 1)
        self.assertIn("IRQ raise 1", self.q.irqs)

    def test_external_request_waits_instead_of_faking_completion(self):
        self.q.write(RAM, 0x11223344)
        base = self.setup_channel(0, RAM, RAM + 0x1000)
        self.q.write(base, 0x5081)  # external request 1
        self.q.advance()
        self.assertEqual(self.q.read(base) & 0x80, 0x80)
        self.assertEqual(self.q.read(base + 0x0c), 0)
        self.assertEqual(self.q.read(RAM + 0x1000), 0)

    def test_interrupt_can_be_registered_before_transfer_completes(self):
        self.q.write(RAM, 0xAABBCCDD)
        base = self.setup_channel(0, RAM, RAM + 0x1000)
        self.q.write(base, 0x5080)
        self.assertEqual(self.q.read(RAM + 0x1000), 0)
        self.q.write(SDMA + 0x08, 1)
        self.q.write(SDMA + 0x18, 1)
        self.q.advance()
        self.assertEqual(self.q.read(RAM + 0x1000), 0xAABBCCDD)
        self.assertEqual(self.q.read(SDMA + 0x08), 1)
        self.assertIn("IRQ raise 0", self.q.irqs)

    def test_reset_cancels_pending_transfer(self):
        self.q.write(RAM, 0x12345678)
        self.q.write(SDMA + 0x18, 1)
        base = self.setup_channel(0, RAM, RAM + 0x1000)
        self.q.write(base, 0x5080)
        self.q.write(SDMA + 0x2c, 2)
        self.q.advance()
        self.assertEqual(self.q.read(RAM + 0x1000), 0)
        self.assertEqual(self.q.read(base + 0x0c), 0)
        self.assertNotIn("IRQ raise 0", self.q.irqs)

    def test_misalignment_and_soft_reset(self):
        self.q.write(SDMA + 0x18, 1)
        base = self.setup_channel(0, RAM + 1, RAM + 0x1000, cicr=0x800)
        self.q.write(base, 0x5080)
        self.q.advance()
        self.assertEqual(self.q.read(base + 0x0c), 0x800)
        self.assertIn("IRQ raise 0", self.q.irqs)
        self.q.write(SDMA + 0x2c, 2)
        self.assertEqual(self.q.read(SDMA + 0x08), 0)
        self.assertEqual(self.q.read(base + 0x0c), 0)
        self.assertIn("IRQ lower 0", self.q.irqs)


if __name__ == "__main__":
    unittest.main()
