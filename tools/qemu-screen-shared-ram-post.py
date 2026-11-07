#!/usr/bin/env python3
"""Write host frames into live QNX Screen buffers and verify QNX posts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import socket
import struct
import time

RAM_BASE = 0x80000000
BUFFER_RE = re.compile(
    r"SCREEN_RAM_BUFFER index=(\d+) pa=0x([0-9a-fA-F]+) "
    r"stride=(\d+) width=(\d+) height=(\d+) format=(\d+) contiguous=(\d+)"
)
LAYOUT_RE = re.compile(
    r"SCREEN_RAM_LAYOUT mode=([a-z0-9-]+) width=(\d+) height=(\d+) "
    r"usage=(\d+) visible=(\d+)"
)
COLOR_WORDS = (0xFF0000FF, 0xFF00FF00, 0xFFFF0000)


def qmp_command(socket_path: Path, command: str) -> str:
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.settimeout(5)
    connection.connect(str(socket_path))
    stream = connection.makefile("rwb", buffering=0)

    def read_message() -> dict[str, object]:
        while True:
            line = stream.readline()
            if not line:
                raise ConnectionError("QEMU closed its QMP socket")
            message = json.loads(line)
            if "event" not in message:
                return message

    try:
        read_message()  # QMP greeting
        stream.write(b'{"execute":"qmp_capabilities","id":"caps"}\r\n')
        while read_message().get("id") != "caps":
            pass
        request = {
            "execute": "human-monitor-command",
            "arguments": {"command-line": command},
            "id": "hmp-command",
        }
        stream.write((json.dumps(request) + "\r\n").encode("utf-8"))
        while True:
            response = read_message()
            if response.get("id") == "hmp-command":
                if "error" in response:
                    raise RuntimeError(f"QMP command failed: {response['error']}")
                return str(response.get("return", ""))
    finally:
        connection.close()


def read_physical(socket_path: Path, address: int, size: int) -> tuple[str, bytes]:
    output = qmp_command(socket_path, f"xp/{size}xb 0x{address:x}")
    data = bytes(int(value, 16) for value in re.findall(r"0x([0-9a-fA-F]{2})", output))
    if len(data) != size:
        raise RuntimeError(f"QMP returned {len(data)} bytes for a {size}-byte read: {output}")
    return output.strip(), data


def save_physical(socket_path: Path, address: int, size: int, path: Path) -> bytes:
    """Use QEMU's HMP binary dump to verify a full Screen buffer."""
    if path.exists():
        raise RuntimeError(f"refusing to overwrite QMP memory dump {path}")
    destination = str(path.resolve())
    if '"' in destination:
        raise RuntimeError("QMP pmemsave output path cannot contain a double quote")
    result = qmp_command(
        socket_path, f'pmemsave 0x{address:x} {size} "{destination}"'
    )
    if not path.is_file():
        raise RuntimeError(f"QMP pmemsave did not create {path}: {result}")
    data = path.read_bytes()
    if len(data) != size:
        raise RuntimeError(f"QMP pmemsave wrote {len(data)} bytes, expected {size}")
    return data


def current_log(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_bytes().replace(b"\0", b"").decode("utf-8", "replace")


def parse_buffers(log: str) -> dict[int, dict[str, int]]:
    result: dict[int, dict[str, int]] = {}
    for match in BUFFER_RE.finditer(log):
        index, address, stride, width, height, pixel_format, contiguous = match.groups()
        result[int(index)] = {
            "physical_address": int(address, 16),
            "stride": int(stride),
            "width": int(width),
            "height": int(height),
            "format": int(pixel_format),
            "contiguous": int(contiguous),
        }
    return result


def wait_for_text(log_path: Path, needle: str, timeout: int) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() <= deadline:
        log = current_log(log_path)
        if needle in log:
            return log
        if ("SCREEN_RAM_SETUP_ERROR" in log or
                "SCREEN_RAM_UNSUPPORTED" in log or
                "SCREEN_RAM_POST_ERROR" in log or
                "SCREEN_RAM_POSTED frame=0 rc=-1" in log or
                "SCREEN_RAM_POSTED frame=1 rc=-1" in log):
            raise RuntimeError("QNX Screen probe rejected the buffer; inspect the serial log")
        time.sleep(0.05)
    raise TimeoutError(f"timed out waiting for {needle!r} in {log_path}")


def pixel_bytes(word: int) -> bytes:
    # Match the exact 32-bit color words used by the known working Screen test.
    return struct.pack("<I", word)


def make_frame(width: int, height: int, stride: int, sequence: int) -> bytes:
    if sequence == 0:
        left = width // 3
        middle = width // 3
        right = width - left - middle
        row = (pixel_bytes(COLOR_WORDS[0]) * left +
               pixel_bytes(COLOR_WORDS[1]) * middle +
               pixel_bytes(COLOR_WORDS[2]) * right)
        row += bytes(stride - len(row))
        return row * height
    rows = bytearray(stride * height)
    reversed_colors = COLOR_WORDS[::-1]
    for y in range(height):
        band = min(2, y * 3 // height)
        color = pixel_bytes(reversed_colors[band])
        start = y * stride
        rows[start:start + width * 4] = color * width
    return bytes(rows)


def load_bmp_frame(path: Path, width: int, height: int, stride: int) -> tuple[bytes, dict[str, object]]:
    """Convert the Vulkan runner's uncompressed 32-bit BMP into Screen RGBA8888."""
    data = path.read_bytes()
    if len(data) < 54 or data[:2] != b"BM":
        raise RuntimeError(f"{path} is not a BMP image")
    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    dib_size = struct.unpack_from("<I", data, 14)[0]
    if dib_size < 40 or 14 + dib_size > len(data):
        raise RuntimeError(f"{path} has an unsupported BMP header")
    source_width, signed_height = struct.unpack_from("<ii", data, 18)
    planes, bits_per_pixel = struct.unpack_from("<HH", data, 26)
    compression = struct.unpack_from("<I", data, 30)[0]
    source_height = abs(signed_height)
    source_stride = ((source_width * 4 + 3) // 4) * 4
    if (source_width <= 0 or source_height <= 0 or planes != 1 or
            bits_per_pixel != 32 or compression != 0):
        raise RuntimeError(f"{path} must be an uncompressed 32-bit BMP")
    source_end = pixel_offset + source_stride * source_height
    if pixel_offset < 14 + dib_size or source_end > len(data):
        raise RuntimeError(f"{path} pixel array is truncated or overlaps its header")

    # The candidate raster is a square. Contain it without stretching and keep
    # the source alpha byte so this remains a transport of the Vulkan output.
    scale = min(width / source_width, height / source_height)
    draw_width = max(1, min(width, round(source_width * scale)))
    draw_height = max(1, min(height, round(source_height * scale)))
    origin_x = (width - draw_width) // 2
    origin_y = (height - draw_height) // 2
    output = bytearray(stride * height)
    for y in range(draw_height):
        src_y = y * source_height // draw_height
        if signed_height > 0:
            src_y = source_height - 1 - src_y
        row_start = pixel_offset + src_y * source_stride
        dst_start = (origin_y + y) * stride + origin_x * 4
        for x in range(draw_width):
            src_x = x * source_width // draw_width
            src = row_start + src_x * 4
            dst = dst_start + x * 4
            # BMP stores BGRA; Screen format 8 is bytewise RGBA8888 here.
            output[dst:dst + 4] = bytes((data[src + 2], data[src + 1],
                                         data[src], data[src + 3]))
    metadata: dict[str, object] = {
        "path": str(path.resolve()),
        "sha256": hashlib.sha256(data).hexdigest(),
        "width": source_width,
        "height": source_height,
        "bits_per_pixel": bits_per_pixel,
        "source_channel_order": "BGRA",
        "target_channel_order": "RGBA8888",
        "target_content_rect": [origin_x, origin_y, draw_width, draw_height],
        "fit": "nearest-neighbor contain, centered; source alpha preserved",
    }
    return bytes(output), metadata


def frame_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def capture_screenshot(socket_path: Path, path: Path) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise RuntimeError(f"refusing to overwrite screenshot {path}")
    result = qmp_command(socket_path, f"screendump {path.resolve()}")
    time.sleep(0.5)
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"QEMU screendump did not create {path}: {result}")
    screenshot_bytes = path.read_bytes()
    if not screenshot_bytes.startswith(b"P6"):
        raise RuntimeError("QEMU screendump output is not a raw Netpbm P6 PPM image")
    return {
        "path": str(path.resolve()),
        "format": "ppm-p6",
        "sha256": hashlib.sha256(screenshot_bytes).hexdigest(),
        "byte_length": path.stat().st_size,
        "qmp_result": result.strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ram-file", type=Path, required=True)
    parser.add_argument("--serial-log", type=Path, required=True)
    parser.add_argument("--qmp-socket", type=Path, required=True)
    parser.add_argument("--wait-seconds", type=int, default=600)
    parser.add_argument("--post-timeout-seconds", type=int, default=90)
    parser.add_argument("--evidence-output", type=Path, required=True)
    parser.add_argument("--screenshot", type=Path)
    parser.add_argument(
        "--screenshot-each-frame", action="store_true",
        help="capture each buffer after its Screen post; derives -frame0/-frame1 PPM paths from --screenshot",
    )
    parser.add_argument("--expected-width", type=int, default=1280)
    parser.add_argument("--expected-height", type=int, default=480)
    parser.add_argument(
        "--expected-usage", type=int,
        help="require a matching SCREEN_RAM_LAYOUT usage value (6 for read-write, 32 for GLES2)",
    )
    parser.add_argument(
        "--full-qmp-verify", action="store_true",
        help="dump each complete guest physical buffer through QMP and compare it byte for byte",
    )
    parser.add_argument(
        "--bmp-frame", type=Path, action="append", default=[], metavar="PATH",
        help="repeat twice to post two host-renderer BMP outputs instead of the synthetic color control",
    )
    parser.add_argument(
        "--frame-label",
        help="describe the host-rendered candidate and its remaining assumptions for the evidence record",
    )
    parser.add_argument(
        "--resume-posted",
        action="store_true",
        help="verify a run whose host frames were already written and Screen already posted them",
    )
    args = parser.parse_args()

    for path in (args.evidence_output, args.screenshot):
        if path is not None and path.exists():
            parser.error(f"refusing to overwrite existing output: {path}")
    if args.wait_seconds < 0 or args.post_timeout_seconds < 0:
        parser.error("wait timeouts cannot be negative")
    if args.screenshot is not None and args.screenshot.suffix.lower() != ".ppm":
        parser.error("QEMU's screendump command writes PPM files; use a .ppm screenshot path")
    if args.screenshot_each_frame and args.screenshot is None:
        parser.error("--screenshot-each-frame requires --screenshot")
    if args.expected_width <= 0 or args.expected_height <= 0:
        parser.error("expected frame dimensions must be positive")
    if len(args.bmp_frame) not in (0, 2):
        parser.error("supply exactly two --bmp-frame paths, or neither")
    if bool(args.bmp_frame) != bool(args.frame_label):
        parser.error("--bmp-frame requires --frame-label, and --frame-label requires two BMP frames")
    initial_log = current_log(args.serial_log)
    if "SCREEN_RAM_READY" in initial_log and not args.resume_posted:
        parser.error("serial log already contains this probe's ready marker; select a fresh log")

    log = initial_log if args.resume_posted else wait_for_text(
        args.serial_log, "SCREEN_RAM_READY", args.wait_seconds
    )
    if "SCREEN_RAM_READY" not in log:
        raise RuntimeError("resume-posted requires an existing SCREEN_RAM_READY marker")
    if not args.ram_file.is_file():
        raise RuntimeError(f"QEMU reported ready before its shared RAM file appeared: {args.ram_file}")
    buffers = parse_buffers(log)
    if sorted(buffers) != [0, 1]:
        raise RuntimeError(f"expected exactly two Screen buffer records, got {sorted(buffers)}")
    if "SCREEN_RAM_READY" not in log:
        raise RuntimeError("Screen ready marker disappeared from the serial log")
    if args.expected_usage is not None:
        layouts = LAYOUT_RE.findall(log)
        expected_layout = (
            str(args.expected_width), str(args.expected_height),
            str(args.expected_usage), "1",
        )
        if not layouts or any(layout[1:] != expected_layout for layout in layouts):
            raise RuntimeError(
                f"Screen layout did not match expected dimensions/usage/visibility: {layouts}"
            )

    file_size = args.ram_file.stat().st_size
    ranges: list[tuple[int, int]] = []
    frames: list[dict[str, object]] = []
    frame_sources: list[dict[str, object] | None] = []
    qmp_full_reads: list[dict[str, object]] = []
    qmp_samples: list[tuple[int, bytes]] = []
    for sequence, index in enumerate((0, 1)):
        buffer = buffers[index]
        if buffer["format"] != 8 or buffer["contiguous"] != 1:
            raise RuntimeError(f"buffer {index} is not contiguous Screen RGBA8888")
        width, height, stride = buffer["width"], buffer["height"], buffer["stride"]
        if (width, height) != (args.expected_width, args.expected_height) or stride < width * 4:
            raise RuntimeError(f"buffer {index} has unsupported layout: {buffer}")
        address = buffer["physical_address"]
        offset = address - RAM_BASE
        size = stride * height
        if offset < 0 or offset + size > file_size:
            raise RuntimeError(f"buffer {index} falls outside the shared RAM file")
        if any(offset < end and start < offset + size for start, end in ranges):
            raise RuntimeError("Screen buffer physical ranges overlap")
        ranges.append((offset, offset + size))
        if args.bmp_frame:
            payload, source_record = load_bmp_frame(
                args.bmp_frame[sequence], width, height, stride
            )
            rect_x, rect_y, rect_width, rect_height = source_record["target_content_rect"]
            sample_offset = ((rect_y + rect_height // 2) * stride +
                             (rect_x + rect_width // 2) * 4)
        else:
            payload = make_frame(width, height, stride, sequence)
            source_record = None
            sample_offset = 0
        if len(payload) != size:
            raise RuntimeError("generated host frame does not match the Screen allocation")
        if sample_offset + 16 > len(payload):
            raise RuntimeError("QMP verification sample falls outside the Screen frame")
        with args.ram_file.open("r+b" if not args.resume_posted else "rb", buffering=0) as ram:
            ram.seek(offset)
            if args.resume_posted:
                file_readback = ram.read(size)
                if file_readback != payload:
                    raise RuntimeError(
                        f"existing shared RAM bytes do not match expected frame {sequence}"
                    )
            else:
                ram.write(payload)
                ram.flush()
                ram.seek(offset)
                file_readback = ram.read(size)
                if file_readback != payload:
                    raise RuntimeError(
                        f"shared RAM file readback did not match written frame {sequence}"
                    )
        frames.append({
            "sequence": sequence,
            "buffer_index": index,
            "physical_address": f"0x{address:x}",
            "ram_file_offset": f"0x{offset:x}",
            "byte_length": size,
            "sha256": frame_digest(payload),
            "shared_file_readback_sha256": frame_digest(file_readback),
            "qmp_sample_offset": sample_offset,
            "qmp_sample_bytes": payload[sample_offset:sample_offset + 16].hex(),
        })
        frame_sources.append(source_record)
        qmp_samples.append((sample_offset, payload[sample_offset:sample_offset + 16]))

    qmp_reads = []
    for index in (0, 1):
        address = buffers[index]["physical_address"]
        sample_offset, expected = qmp_samples[index]
        hmp, observed = read_physical(args.qmp_socket, address + sample_offset, 16)
        if observed != expected:
            raise RuntimeError(
                f"QEMU physical read for Screen buffer {index} did not match host bytes: {hmp}"
            )
        qmp_reads.append({
            "buffer_index": index,
            "guest_buffer_offset": sample_offset,
            "hmp": hmp,
            "bytes": observed.hex(),
        })
        if args.full_qmp_verify:
            dump_path = args.evidence_output.with_name(
                f".{args.evidence_output.stem}.qmp-buffer-{index}.bin"
            )
            full_bytes = save_physical(
                args.qmp_socket, address, stride * buffers[index]["height"], dump_path
            )
            expected_frame = make_frame(
                buffers[index]["width"], buffers[index]["height"],
                buffers[index]["stride"], index,
            ) if not args.bmp_frame else load_bmp_frame(
                args.bmp_frame[index], buffers[index]["width"],
                buffers[index]["height"], buffers[index]["stride"],
            )[0]
            if full_bytes != expected_frame:
                dump_path.unlink(missing_ok=True)
                raise RuntimeError(
                    f"full QMP physical read for Screen buffer {index} differs from the expected frame"
                )
            qmp_full_reads.append({
                "buffer_index": index,
                "byte_length": len(full_bytes),
                "sha256": frame_digest(full_bytes),
                "matches_frame": True,
            })
            dump_path.unlink()

    screenshot_records: list[dict[str, object]] = []
    if args.screenshot_each_frame:
        screenshot_paths = [
            args.screenshot.with_name(f"{args.screenshot.stem}-frame{index}{args.screenshot.suffix}")
            for index in (0, 1)
        ]
        for path in screenshot_paths:
            if path.exists():
                raise RuntimeError(f"refusing to overwrite screenshot {path}")
        for index, path in enumerate(screenshot_paths):
            wait_for_text(
                args.serial_log, f"SCREEN_RAM_POSTED frame={index} rc=0",
                args.post_timeout_seconds,
            )
            screenshot_records.append(capture_screenshot(args.qmp_socket, path))
        log = current_log(args.serial_log)
    else:
        log = wait_for_text(args.serial_log, "SCREEN_RAM_POSTED frame=1 rc=0",
                            args.post_timeout_seconds)
    post_records = re.findall(r"SCREEN_RAM_POSTED frame=\d+ rc=[^\r\n]+", log)
    if ("SCREEN_RAM_POSTED frame=0 rc=0" not in post_records or
            "SCREEN_RAM_POSTED frame=1 rc=0" not in post_records):
        raise RuntimeError(f"QNX did not report successful posts for both frames: {post_records}")

    screenshot_record = None
    if args.screenshot is not None and not args.screenshot_each_frame:
        screenshot_record = capture_screenshot(args.qmp_socket, args.screenshot)

    evidence = {
        "probe": "host-shared-ram-to-qnx-screen-post-v1",
        "claim_scope": (
            "host Vulkan shader-candidate BMPs posted by a standalone QNX Screen window; not HMI output"
            if args.bmp_frame else
            "synthetic host frames posted by a standalone QNX Screen window; not HMI output"
        ),
        "frame_label": args.frame_label,
        "ram_file": str(args.ram_file.resolve()),
        "ram_file_size": file_size,
        "ram_base_guest_physical": f"0x{RAM_BASE:x}",
        "buffers": buffers,
        "frames": frames,
        "frame_sources": frame_sources,
        "host_write_mode": "verify-existing" if args.resume_posted else "write-and-verify",
        "qmp_reads": qmp_reads,
        "qmp_full_reads": qmp_full_reads,
        "successful_posts": post_records,
        "screenshot": screenshot_record,
        "screenshots": screenshot_records,
    }
    args.evidence_output.parent.mkdir(parents=True, exist_ok=True)
    args.evidence_output.write_text(json.dumps(evidence, indent=2) + "\n")
    print(
        f"Observed {len(buffers)} contiguous QNX Screen buffers at "
        f"{args.expected_width}x{args.expected_height}."
    )
    if args.resume_posted:
        print("Verified both host frames already present in shared guest RAM.")
    else:
        print("Wrote and read back both host frames in shared guest RAM.")
    print("QEMU physical-memory reads matched each Screen buffer's host-written bytes.")
    if args.full_qmp_verify:
        print("QMP full-buffer dumps matched both complete frame byte arrays.")
    print("QNX Screen reported successful posts for frames 0 and 1.")
    if screenshot_record:
        print(f"QEMU screenshot: {screenshot_record['path']}")
    print(f"Evidence: {args.evidence_output.resolve()}")
    print("This confirms the host→QEMU RAM→QNX Screen post path, not BMW HMI rendering.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
