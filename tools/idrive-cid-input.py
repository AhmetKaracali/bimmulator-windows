#!/usr/bin/env python3
"""Send native CID touch reports to a loopback-forwarded iDrive emulator."""

import argparse
from contextlib import nullcontext
from pathlib import Path
import re
import signal
import socket
import struct
import time


ABSOLUTE_MAX = 0x7FFF
TRACE_AXIS = re.compile(r"input_event_abs con -?\d+, axis ([xy]), value 0x([0-9a-f]+)")
TRACE_BUTTON = re.compile(r"input_event_btn con -?\d+, button (left), down ([01])")
TRACE_SELECT_KEY = re.compile(r"input_event_key_qcode con -?\d+, key qcode (ret|spc), down ([01])")
TRACE_CONTROLLER_KEY = re.compile(
    r"input_event_key_qcode con -?\d+, key qcode ([\w-]+), down ([01])"
)
TRACE_WHEEL = re.compile(r"input_event_btn con -?\d+, button (wheel-up|wheel-down), down ([01])")
CONTROLLER_KEYS = {
    "m": 1, "esc": 2, "backspace": 2, "o": 3,
    "c": 4, "r": 4, "t": 6, "n": 7, "v": 17,
    "ret": 8, "spc": 8,
    "up": 9, "down": 10, "left": 11, "right": 12,
    "pgup": 14, "pgdn": 13, "wheel-up": 14, "wheel-down": 13,
}


class CidTouch:
    def __init__(self, sock, port):
        self.sock = sock
        self.port = port
        self.sequence = 0
        self.contact = None

    def report(self, position, state):
        x, y = position
        self.sequence = self.sequence % 0xFFFF + 1
        payload = bytearray(96)
        # One finger, followed by the first record's position and contact state.
        struct.pack_into(">I", payload, 36, (1 << 16) | x)
        struct.pack_into(">I", payload, 44, (y << 16) | (64 << 8) | (1 << 6) | (state << 4))
        header = struct.pack(">4I", 0xB0048002, len(payload) + 8, self.sequence, 0x01010200)
        self.sock.sendto(header + payload, ("127.0.0.1", self.port))
        self.contact = position if state != 3 else None

    def release(self):
        if self.contact is not None:
            self.report(self.contact, 3)


def interrupted(_signal, _frame):
    raise KeyboardInterrupt


def relay_input(trace, touch, width, height, controller=None):
    position = [None, None]
    pending = []
    pressed = set()
    controller_pressed = set()
    with trace.open(errors="replace") as stream:
        stream.seek(0, 2)
        if controller:
            print("Listening for mouse and native controller keys in the QEMU window.", flush=True)
        else:
            print("Listening for mouse clicks, Return and Space in the QEMU window.", flush=True)
        while True:
            offset = stream.tell()
            line = stream.readline()
            if not line.endswith("\n"):
                stream.seek(offset)
                time.sleep(0.01)
                continue
            line = line.strip()
            if match := TRACE_AXIS.fullmatch(line):
                index = 0 if match[1] == "x" else 1
                extent = width if index == 0 else height
                value = min(int(match[2], 16), ABSOLUTE_MAX)
                position[index] = round(value * (extent - 1) / ABSOLUTE_MAX)
            elif (controller and
                  (match := TRACE_CONTROLLER_KEY.fullmatch(line) or TRACE_WHEEL.fullmatch(line)) and
                  match[1] in CONTROLLER_KEYS):
                key, state = match.groups()
                if state == "0":
                    controller_pressed.discard(key)
                elif key not in controller_pressed:
                    if not key.startswith("wheel-"):
                        controller_pressed.add(key)
                    controller(CONTROLLER_KEYS[key])
            elif match := TRACE_BUTTON.fullmatch(line) or (
                None if controller else TRACE_SELECT_KEY.fullmatch(line)
            ):
                pending.append((match[1], match[2] == "1"))
            elif line.startswith("input_event_sync"):
                if None not in position:
                    point = tuple(position)
                    for control, down in pending:
                        if down:
                            pressed.add(control)
                        else:
                            pressed.discard(control)
                        if pressed and touch.contact is None:
                            touch.report(point, 1)
                        elif not pressed and touch.contact is not None:
                            touch.report(point, 3)
                    if touch.contact is not None and point != touch.contact:
                        touch.report(point, 2)
                pending.clear()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=43567, help="loopback UDP forwarding port")
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--controller-socket", type=Path)
    modes = parser.add_subparsers(dest="mode", required=True)
    tap = modes.add_parser("tap", help="tap a point in guest display pixels")
    tap.add_argument("x", type=int)
    tap.add_argument("y", type=int)
    relay = modes.add_parser("relay", help="relay QEMU mouse and selection key events")
    relay.add_argument("trace", type=Path)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    if not (1 <= args.width <= 65536 and 1 <= args.height <= 65536):
        parser.error("display dimensions must be between 1 and 65536")
    if args.mode == "tap" and not (0 <= args.x < args.width and 0 <= args.y < args.height):
        parser.error("tap must be inside the guest display")

    signal.signal(signal.SIGTERM, interrupted)
    controller = (socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
                  if args.controller_socket else nullcontext())
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock, controller as keys:
        touch = CidTouch(sock, args.port)
        try:
            if args.mode == "tap":
                touch.report((args.x, args.y), 1)
                time.sleep(0.15)
            else:
                def send_key(code):
                    keys.sendto(bytes((code,)), str(args.controller_socket))

                relay_input(args.trace, touch, args.width, args.height,
                            send_key if args.controller_socket else None)
        except KeyboardInterrupt:
            pass
        finally:
            touch.release()


if __name__ == "__main__":
    main()
