#!/usr/bin/env python3
"""Exercise OMAP timers, GPU MMU events, and display/SDMA snapshots via qtest.

Run inside `nix develop path:.`; no firmware, extracted root, or GUI is needed.
"""
import json
import socket
import subprocess
import tempfile
import time
from pathlib import Path


def connect(path, process):
    for _ in range(300):
        if process.poll() is not None:
            raise RuntimeError(f"QEMU exited with {process.returncode}")
        try:
            sock = socket.socket(socket.AF_UNIX)
            sock.connect(str(path))
            sock.settimeout(30)
            return sock.makefile("rwb", buffering=0)
        except (FileNotFoundError, ConnectionRefusedError):
            sock.close()
            time.sleep(0.05)
    raise RuntimeError(f"Timed out connecting to {path}")


def main():
    with tempfile.TemporaryDirectory(prefix="idrive-qtest-") as directory:
        root = Path(directory)
        disk = root / "state.qcow2"
        mailbox = root / "mailbox.bin"
        with mailbox.open("wb") as stream:
            stream.truncate(17 * 1024 * 1024)
            stream.write(b"I6MB")
        subprocess.run(["qemu-img", "create", "-q", "-f", "qcow2", str(disk), "8M"], check=True)
        with (root / "stderr").open("w+") as error:
            process = subprocess.Popen([
                "qemu-system-arm", "-M", "omap5430,graphics-mailbox=mailbox",
                "-object", f"memory-backend-file,id=mailbox,mem-path={mailbox},size=17M,share=on",
                "-m", "1024", "-S",
                "-display", "none", "-serial", "null", "-monitor", "none",
                "-nic", "none", "-drive", f"if=none,id=state,file={disk},format=qcow2",
                "-qmp", f"unix:{root / 'qmp'},server=on,wait=off",
                "-qtest", f"unix:{root / 'qtest'},server=on,wait=off",
                "-d", "unimp", "-D", str(root / "gpu.log"),
            ], stderr=error, stdout=subprocess.DEVNULL)
            try:
                qmp = connect(root / "qmp", process)
                json.loads(qmp.readline())

                def command(name, arguments=None):
                    qmp.write((json.dumps({"execute": name, "arguments": arguments or {}}) + "\n").encode())
                    while True:
                        reply = json.loads(qmp.readline())
                        if "error" in reply:
                            raise RuntimeError(reply)
                        if "return" in reply:
                            return reply["return"]

                command("qmp_capabilities")
                assert command("qom-get", {"path": "/machine/unattached/device[0]",
                                            "property": "cntfrq"}) == 6144000
                qt = connect(root / "qtest", process)

                def test(text):
                    qt.write((text + "\n").encode())
                    while True:
                        reply = qt.readline().decode().strip()
                        if not reply:
                            raise RuntimeError("QEMU closed qtest")
                        if reply.startswith("IRQ "):
                            continue
                        if not reply.startswith("OK"):
                            raise RuntimeError(reply)
                        return reply.split()[1:]

                def write(address, value):
                    test(f"writel {address:#x} {value:#x}")

                def read(address):
                    return int(test(f"readl {address:#x}")[0], 0)

                def hmp(text):
                    result = command("human-monitor-command", {"command-line": text})
                    if result:
                        raise RuntimeError(result)

                # The file is shared both ways outside the main DDR bank.
                assert read(0x70000000) == int.from_bytes(b"I6MB", "little")
                write(0x70000004, 2)
                with mailbox.open("rb") as stream:
                    assert stream.read(8) == b"I6MB" + (2).to_bytes(4, "little")
                assert read(0x80000004) == 0

                # The native QNX driver requires all three clock-activity bits.
                write(0x4A009500, 2)
                assert read(0x4A009500) == 2
                write(0x4A009520, 2)
                assert read(0x4A009500) == 0x702
                assert read(0x4A009520) & (3 << 16) == 0
                write(0x4A009500, 0)
                assert read(0x4A009500) == 0x700

                # Translate an actual SGX-format page directory and two GPU
                # virtual mappings when the guest submits a firmware event.
                write(0x80003000 + (0xF4002010 >> 22) * 4, 0x80004001)
                write(0x80004000 + 2 * 4, 0x80005019)
                write(0x80005010, 0x87654321)
                write(0x80003000 + (0xF2010000 >> 22) * 4, 0x80007001)
                write(0x80007000 + 16 * 4, 0x80006019)
                write(0x80006000, 0xDEADBEEF)
                write(0x56000C50, 0x80003000)
                write(0x56000AC4, 0xF4002010)
                write(0x56008A68, 0xF2010000)
                write(0x56008AC0, 1)
                assert read(0x56008AC0) == 0
                trace = (root / "gpu.log").read_text()
                assert "pa=0x80005010 word=0x87654321" in trace
                assert "pa=0x80006000 word=0xdeadbeef" in trace

                # Save an in-flight SDMA copy and a real DISPC overlay register.
                write(0x80001000, 0xA1B2C3D4)
                write(0x58001080, 0x81234000)
                write(0x4A056018, 1)
                channel = 0x4A056080
                for offset, value in [(8, 32), (16, 2), (20, 1), (24, 1),
                                      (28, 0x80001000), (32, 0x80002000), (0, 0x5080)]:
                    write(channel + offset, value)
                hmp("savevm omap-state")
                write(0x58001080, 0)
                write(0x4A009520, 0)
                write(0x56008A68, 0)
                write(0x4A056018, 0)
                write(channel, 0)
                hmp("loadvm omap-state")
                assert read(0x58001080) == 0x81234000
                assert read(0x56008A68) == 0xF2010000
                assert read(0x4A009500) == 0x700
                assert read(0x4A056018) == 1
                assert read(channel) & 0x80
                # Packaged QEMU exposes qtest MMIO but not the test-only clock
                # accelerator. Let TCG advance virtual time for the DMA timer.
                command("cont")
                deadline = time.monotonic() + 5
                while read(0x80002000) != 0xA1B2C3D4 and time.monotonic() < deadline:
                    time.sleep(0.02)
                command("stop")
                assert read(0x80002000) == 0xA1B2C3D4
                assert read(0x4A056008) & 1
                assert read(channel + 12) & 32
                assert not read(channel) & 0x80
                print("PASS: shared mailbox, timer frequency, GPU clocks/MMU, display/GPU restore, and pending SDMA")
                command("quit")
            except BaseException:
                error.seek(0)
                print(error.read()[-4000:])
                raise
            finally:
                if process.poll() is None:
                    process.terminate()
                process.wait(timeout=10)


if __name__ == "__main__":
    main()
