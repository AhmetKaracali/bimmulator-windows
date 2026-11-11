#!/usr/bin/env python3
"""Grab the emulator's head-unit display through QEMU's QMP socket and save it as PNG.

Usage (inside WSL): python3 wsl/screendump.py <qmp.sock> <out.png>
"""
import json
import socket
import struct
import sys
import time
import zlib


def qmp(sock_path: str, ppm_path: str) -> None:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(sock_path)
        f = s.makefile("rwb")
        f.readline()  # greeting
        for cmd in ({"execute": "qmp_capabilities"},
                    {"execute": "screendump", "arguments": {"filename": ppm_path}}):
            f.write((json.dumps(cmd) + "\n").encode())
            f.flush()
            while True:
                reply = json.loads(f.readline())
                if "return" in reply or "error" in reply:
                    if "error" in reply:
                        raise SystemExit(f"QMP error: {reply['error']}")
                    break


def ppm_to_png(ppm_path: str, png_path: str) -> None:
    data = open(ppm_path, "rb").read()
    parts = data.split(maxsplit=4)
    assert parts[0] == b"P6", parts[0]
    width, height, pixels = int(parts[1]), int(parts[2]), parts[4]
    rows = b"".join(b"\x00" + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))

    def chunk(tag: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body))

    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b""))
    open(png_path, "wb").write(png)
    print(f"{width}x{height} -> {png_path}")


def lit_samples(ppm_path: str) -> int:
    pixels = open(ppm_path, "rb").read().split(maxsplit=4)[4]
    return sum(1 for i in range(0, len(pixels) - 2, 3 * 97) if pixels[i] or pixels[i + 1] or pixels[i + 2])


if __name__ == "__main__":
    args = sys.argv[1:]
    wait = 0.0
    if args and args[0] == "--wait":     # --wait SECONDS: poll until the display is not black
        wait, args = float(args[1]), args[2:]
    ppm = f"/tmp/idrive6-shot-{int(time.time() * 1000)}.ppm"
    deadline = time.time() + wait
    while True:
        qmp(args[0], ppm)
        time.sleep(0.5)
        if wait <= 0 or lit_samples(ppm) > 20 or time.time() >= deadline:
            break
        time.sleep(10)
    if wait > 0 and lit_samples(ppm) <= 20:
        print("display still black", file=sys.stderr)
    ppm_to_png(ppm, args[1])
