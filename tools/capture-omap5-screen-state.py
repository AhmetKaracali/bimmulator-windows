#!/usr/bin/env python3
"""Capture a live OMAP5 Screen bridge frame and DSS scanout registers."""

import argparse
import json
import re
import socket
import time
from pathlib import Path


QEMU_REGISTERS = {
    "dispc_control": 0x58001040,
    "dispc_irqstatus": 0x58001044,
    "dispc_irqenable": 0x58001048,
    "lcd_size": 0x5800107C,
    "lcd2_size": 0x580013CC,
    "lcd3_size": 0x58001834,
    "gfx_base": 0x58001080,
    "gfx_position": 0x58001088,
    "gfx_size": 0x5800108C,
    "gfx_attributes": 0x580010A0,
    "gfx_row_increment": 0x580010AC,
    "gfx_pixel_increment": 0x580010B0,
    "vid1_base": 0x580010BC,
    "vid1_position": 0x580010C4,
    "vid1_size": 0x580010C8,
    "vid1_attributes": 0x580010CC,
    "vid1_row_increment": 0x580010E8,
    "vid1_pixel_increment": 0x580010EC,
    "vid2_base": 0x5800114C,
    "vid2_position": 0x58001154,
    "vid2_size": 0x58001158,
    "vid2_attributes": 0x5800115C,
    "vid2_row_increment": 0x58001178,
    "vid2_pixel_increment": 0x5800117C,
    "vid3_base": 0x580011BC,
    "vid3_position": 0x580011C4,
    "vid3_size": 0x580011C8,
    "vid3_attributes": 0x580011CC,
    "vid3_row_increment": 0x580011E8,
    "vid3_pixel_increment": 0x580011EC,
}

FNV_OFFSET_BASIS = 1469598103934665603
FNV_PRIME = 1099511628211
GUEST_RAM_BASE = 0x80000000


def fnv1a64(data):
    value = FNV_OFFSET_BASIS
    for byte in data:
        value = ((value ^ byte) * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
    return f"{value:016x}"


def ppm_dimensions(path):
    data = path.read_bytes()[:4096]
    tokens = []
    index = 0
    while index < len(data) and len(tokens) < 4:
        if data[index] in b" \t\r\n\v\f":
            index += 1
            continue
        if data[index] == ord("#"):
            newline = data.find(b"\n", index)
            if newline < 0:
                break
            index = newline + 1
            continue
        start = index
        while index < len(data) and data[index] not in b" \t\r\n\v\f#":
            index += 1
        tokens.append(data[start:index])
    if len(tokens) < 4 or tokens[0] != b"P6":
        raise RuntimeError(f"unsupported or malformed QMP PPM screenshot: {path}")
    return int(tokens[1]), int(tokens[2])


def qmp_command(stream, name, arguments=None):
    request = {"execute": name}
    if arguments is not None:
        request["arguments"] = arguments
    stream.write((json.dumps(request) + "\r\n").encode())
    while True:
        line = stream.readline()
        if not line:
            raise RuntimeError(f"QMP closed while executing {name}")
        response = json.loads(line)
        if "return" not in response and "error" not in response:
            continue
        if "error" in response:
            raise RuntimeError(f"QMP {name}: {response['error']}")
        return response["return"]


def wait_for_marker(serial_log, marker, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if marker in serial_log.read_text(errors="replace"):
                return
        except FileNotFoundError:
            pass
        time.sleep(0.25)
    raise TimeoutError(f"did not see {marker!r} in {serial_log} within {timeout}s")


def parse_host_frames(host_log):
    frames = []
    for line in host_log.read_text(errors="replace").splitlines():
        if not line.startswith("ANGLE_SCREEN_FRAME "):
            continue
        record = dict(re.findall(r"([a-zA-Z0-9_]+)=([^\s]+)", line))
        required = {"physical", "stride", "width", "height", "bytes", "fnv1a64"}
        if required <= record.keys():
            frames.append(record)
    return frames


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ram-file", type=Path, required=True)
    parser.add_argument("--serial-log", type=Path, required=True)
    parser.add_argument("--host-log", type=Path, required=True)
    parser.add_argument("--qmp-socket", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--marker", default="ANGLE_SCREEN_SMOKE_HOLD")
    parser.add_argument("--wait-seconds", type=float, default=900)
    args = parser.parse_args()

    wait_for_marker(args.serial_log, args.marker, args.wait_seconds)
    frames = parse_host_frames(args.host_log)
    if len(frames) < 2:
        raise RuntimeError(f"expected two host Screen frames, found {len(frames)}")

    args.evidence_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "serial_log": str(args.serial_log.resolve()),
        "host_log": str(args.host_log.resolve()),
        "ram_file": str(args.ram_file.resolve()),
        "qmp_socket": str(args.qmp_socket.resolve()),
        "marker": args.marker,
        "hash_algorithm": {
            "name": "FNV-1a 64-bit as implemented by tools/angle-egl-rpc-server.cpp",
            "offset_basis": FNV_OFFSET_BASIS,
            "prime": FNV_PRIME,
        },
        "qemu_dss_registers": {},
        "frames": [],
        "display_capture": "display.ppm",
        "visible_scanout": "requires visual inspection of display.ppm",
    }

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as qmp:
        qmp.settimeout(20)
        qmp.connect(str(args.qmp_socket))
        stream = qmp.makefile("rwb", buffering=0)
        manifest["qmp_greeting"] = json.loads(stream.readline())
        qmp_command(stream, "qmp_capabilities")
        qmp_command(stream, "screendump", {
            "filename": str(args.evidence_dir / "display.ppm")
        })

        for name, address in QEMU_REGISTERS.items():
            reply = qmp_command(stream, "human-monitor-command", {
                "command-line": f"xp /1wx 0x{address:08x}"
            })
            match = re.search(r":\s*(0x[0-9a-fA-F]+)", reply)
            manifest["qemu_dss_registers"][name] = {
                "address": f"0x{address:08x}",
                "value": int(match.group(1), 16) if match else None,
                "monitor_output": reply.strip(),
            }

        for index, record in enumerate(frames[:2]):
            physical = int(record["physical"], 16)
            byte_count = int(record["bytes"])
            dump_path = args.evidence_dir / f"frame{index}-qmp.bin"
            qmp_command(stream, "pmemsave", {
                "val": physical,
                "size": byte_count,
                "filename": str(dump_path),
            })
            qmp_bytes = dump_path.read_bytes()
            offset = physical - GUEST_RAM_BASE
            with args.ram_file.open("rb") as ram:
                ram.seek(offset)
                shared_bytes = ram.read(byte_count)
            frame_result = {
                "index": index,
                "physical_address": record["physical"],
                "offset": hex(offset),
                "stride": int(record["stride"]),
                "width": int(record["width"]),
                "height": int(record["height"]),
                "bytes": byte_count,
                "host_fnv1a64": record["fnv1a64"],
                "qmp_fnv1a64": fnv1a64(qmp_bytes),
                "shared_ram_fnv1a64": fnv1a64(shared_bytes),
                "qmp_equals_shared_ram": qmp_bytes == shared_bytes,
                "qmp_matches_host": fnv1a64(qmp_bytes) == record["fnv1a64"],
                "shared_ram_matches_host": fnv1a64(shared_bytes) == record["fnv1a64"],
                "qmp_dump": dump_path.name,
            }
            manifest["frames"].append(frame_result)

    manifest["display_size_px"] = list(
        ppm_dimensions(args.evidence_dir / "display.ppm")
    )
    registers = {
        name: item["value"] for name, item in manifest["qemu_dss_registers"].items()
    }
    gfx_size = registers.get("gfx_size")
    gfx_attributes = registers.get("gfx_attributes")
    manifest["dss_interpretation"] = {
        "dispc_control": registers.get("dispc_control"),
        "digital_output_enabled": bool((registers.get("dispc_control") or 0) & 0x2),
        "gfx_base": registers.get("gfx_base"),
        "gfx_enabled": bool((gfx_attributes or 0) & 0x1),
        "gfx_format_field": ((gfx_attributes or 0) >> 1) & 0xf,
        "gfx_size_px": [
            (gfx_size & 0x7ff) + 1 if gfx_size is not None else None,
            ((gfx_size >> 16) & 0x7ff) + 1 if gfx_size is not None else None,
        ],
        "lcd_size_registers": [
            registers.get("lcd_size"),
            registers.get("lcd2_size"),
            registers.get("lcd3_size"),
        ],
    }

    manifest_path = args.evidence_dir / "omap5-screen-state.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({
        "manifest": str(manifest_path),
        "display_capture": str(args.evidence_dir / "display.ppm"),
        "dss": {name: item["value"] for name, item in manifest["qemu_dss_registers"].items()},
        "frames": manifest["frames"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
