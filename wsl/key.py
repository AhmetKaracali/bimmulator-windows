#!/usr/bin/env python3
"""Send iDrive controller keys to the running emulator through QMP, then optionally screenshot.

Usage: wsl-key.py <qmp.sock> <step> [<step> ...]
  steps: next / prev   (turn knob: Page Down / Page Up)
         left right up down (tilt), press (Return), back (Escape), menu (m), option (o)
         wait:<seconds>, shot:<file.png>  (screenshot of the head-unit display)
"""
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

KEYS = {"next": "pgdn", "prev": "pgup", "press": "ret", "back": "esc", "menu": "m", "option": "o",
        "left": "left", "right": "right", "up": "up", "down": "down"}


def qmp(sock_path, command, **arguments):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(sock_path)
        stream = sock.makefile("rwb")
        stream.readline()
        for message in ({"execute": "qmp_capabilities"}, {"execute": command, "arguments": arguments}):
            stream.write((json.dumps(message) + "\n").encode())
            stream.flush()
            while True:
                reply = json.loads(stream.readline())
                if "return" in reply or "error" in reply:
                    break
        return reply


def main():
    sock = sys.argv[1]
    for step in sys.argv[2:]:
        if step.startswith("wait:"):
            time.sleep(float(step[5:]))
        elif step.startswith("shot:"):
            subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "screendump.py"), sock,
                            step[5:]], check=False)
        else:
            reply = qmp(sock, "send-key", keys=[{"type": "qcode", "data": KEYS[step]}], **{"hold-time": 120})
            print(step, "error" if "error" in reply else "ok", flush=True)
            time.sleep(1.2)


if __name__ == "__main__":
    main()
