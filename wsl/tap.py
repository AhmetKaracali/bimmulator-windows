#!/usr/bin/env python3
"""Tap the emulated CID touch screen via QMP: wsl-tap.py <qmp.sock> x y [x y ...]  (1440x540 pixels)."""
import json, socket, sys, time

def qmp(sock_path, command, **arguments):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(sock_path)
        stream = sock.makefile("rwb")
        stream.readline()
        for message in ({"execute": "qmp_capabilities"}, {"execute": command, "arguments": arguments}):
            stream.write((json.dumps(message) + "\n").encode()); stream.flush()
            while True:
                reply = json.loads(stream.readline())
                if "return" in reply or "error" in reply:
                    break
        return reply

def abs_events(x, y):
    return [{"type": "abs", "data": {"axis": "x", "value": int(x * 32767 / 1439)}},
            {"type": "abs", "data": {"axis": "y", "value": int(y * 32767 / 539)}}]

sock = sys.argv[1]
coords = list(map(float, sys.argv[2:]))
for x, y in zip(coords[::2], coords[1::2]):
    print(qmp(sock, "input-send-event", events=abs_events(x, y)))
    time.sleep(0.15)
    print(qmp(sock, "input-send-event", events=[{"type": "btn", "data": {"down": True, "button": "left"}}]))
    time.sleep(0.15)
    print(qmp(sock, "input-send-event", events=[{"type": "btn", "data": {"down": False, "button": "left"}}]))
    time.sleep(1.0)
