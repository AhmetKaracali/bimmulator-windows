#!/usr/bin/env python3
"""Host side of the Jacinto MOSTSubSystemServer stand-in (see bimmulator tools/qnx-j5-bridge.c).

Listens on 127.0.0.1:5600 (QEMU user networking maps the guest's 160.48.199.253 to host
loopback). Every DSYSMOSTServer request from the HU's MOST client arrives here; behaviour lives
in j5_rules.py, reloaded whenever the file changes, so replies can be developed while the
emulator keeps running. Everything is logged as JSON lines to $IDRIVE_HOME/j5.jsonl.
"""
import os
import importlib
import json
import socket
import struct
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dsys  # noqa: E402  (codec for the DSYSMOSTServer payloads)

HELLO, REQUEST, END = 1, 2, 12
RESPONSE, ATTRIBUTE = 10, 11


class Link:
    def __init__(self, conn, log):
        self.conn, self.log = conn, log
        self.lock = threading.Lock()
        self.t0 = time.time()
        self.state = {}

    def record(self, **entry):
        entry["t"] = round(time.time() - self.t0, 3)
        self.log.write(json.dumps(entry) + "\n")
        self.log.flush()

    def frame(self, kind, ident, arg, payload=b""):
        with self.lock:
            self.conn.sendall(struct.pack("<IIII", 12 + len(payload), kind, ident, arg) + payload)

    def response(self, ident, payload=b"", rtype=0x200):
        self.record(dir="j5", kind="response", id=hex(ident), name=dsys.name(ident),
                    payload=payload.hex(), decoded=dsys.decode(ident, payload))
        self.frame(RESPONSE, ident, rtype, payload)

    def attribute(self, ident, payload):
        self.record(dir="j5", kind="attribute", id=hex(ident), name=dsys.name(ident),
                    payload=payload.hex(), decoded=dsys.decode(ident, payload))
        self.frame(ATTRIBUTE, ident, 0, payload)


def read_exact(conn, size):
    data = b""
    while len(data) < size:
        chunk = conn.recv(size - len(data))
        if not chunk:
            return None
        data += chunk
    return data


def load_rules(current):
    try:
        import j5_rules
        return importlib.reload(j5_rules)
    except Exception as error:
        print(f"j5_rules.py not loaded: {error!r}", flush=True)
        return current


def serve(conn, log):
    link = Link(conn, log)
    rules_path = HERE / "j5_rules.py"
    holder = {"rules": load_rules(None), "mtime": rules_path.stat().st_mtime if rules_path.exists() else 0,
              "alive": True}

    def watch():  # hot reload; j5_rules.on_reload(link) may push replies right away
        while holder["alive"]:
            time.sleep(1)
            mtime = rules_path.stat().st_mtime if rules_path.exists() else 0
            if mtime != holder["mtime"]:
                holder["rules"], holder["mtime"] = load_rules(holder["rules"]), mtime
                print("j5_rules.py reloaded", flush=True)
                if holder["rules"] and hasattr(holder["rules"], "on_reload"):
                    safe(holder["rules"].on_reload, link)

    threading.Thread(target=watch, daemon=True).start()
    try:
        _serve(conn, link, holder)
    finally:
        holder["alive"] = False


def _serve(conn, link, holder):
    while True:
        head = read_exact(conn, 16)
        if head is None:
            return
        size, kind, ident, arg = struct.unpack("<IIII", head)
        payload = read_exact(conn, size - 12) if size > 12 else b""
        rules = holder["rules"]
        if kind == 5:   # DSI notification table dump: count + 24-byte entries
            entries = [struct.unpack_from("<6i", payload, 4 + 24 * i) for i in range(arg)] if payload else []
            subs = [f"{e[2] & 0xffffffff:#x}/s{e[3]}" for e in entries]
            link.record(dir="bridge", kind="notification_table", count=arg, entries=[list(e) for e in entries])
            print(f"subscriptions ({arg}): {' '.join(subs)}", flush=True)
            continue
        if kind == 6:   # result of a response / notification send
            link.record(dir="bridge", kind="send_result", id=hex(ident), rc=arg if arg < 0x80000000 else arg - (1 << 32))
            continue
        if kind == HELLO:
            link.record(dir="hu", kind="hello", version=hex(ident), text=payload.decode("latin-1"))
            print(f"bridge up: {payload.decode('latin-1')} v{ident >> 16}.{ident & 0xffff}", flush=True)
            if rules and hasattr(rules, "on_hello"):
                threading.Thread(target=safe, args=(rules.on_hello, link), daemon=True).start()
            continue
        if kind == REQUEST:
            link.record(dir="hu", kind="request", id=hex(ident), name=dsys.name(ident), session=arg,
                        payload=payload.hex(), decoded=dsys.decode(ident, payload))
            if rules and hasattr(rules, "on_request"):
                safe(rules.on_request, link, ident, payload)
            link.frame(END, ident, 0)


def safe(fn, *args):
    try:
        fn(*args)
    except Exception as error:
        print(f"rule error in {getattr(fn, '__name__', fn)}: {error!r}", flush=True)


def main():
    log_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.environ.get("IDRIVE_HOME", os.path.expanduser("~/idrive")), "j5.jsonl")
    server = socket.create_server(("127.0.0.1", 5600), reuse_port=True)
    print("j5_server listening on 127.0.0.1:5600", flush=True)
    with open(log_path, "a") as log:
        while True:
            conn, _ = server.accept()
            print("bridge connected", flush=True)
            try:
                serve(conn, log)
            except OSError as error:
                print(f"link error: {error}", flush=True)
            finally:
                conn.close()
                print("bridge disconnected", flush=True)


if __name__ == "__main__":
    main()
