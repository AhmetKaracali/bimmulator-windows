#!/usr/bin/env python3
"""HSFZ diagnostic-gateway simulator for the emulator (the car's ZGM on TCP 6801).

The OEM+ app workers in the emulated head unit connect to 160.48.199.253:6801, which QEMU's user
network maps to this host's loopback. Answers come from a built-in synthetic engine model, or - with --record DIR - from your own
read-only IDriveReader capture (never written to a car):
  22 <DID>        DME 0x12: replays the captured live rounds (live/DME_0x12.jsonl) in a loop
                  (plus didscan values); other ECUs: F190 VIN-style data only if captured
  19 02 <mask>    DTCs per ECU from dtcs.json
  14 FF FF FF     clears the simulated fault memory of that ECU (in memory only)
  2F 01 <n>       MHD+ map slot request  -> echo 6F 01 <n>   (only if MHD_TUNED)
  2F 03 <0|1>     MHD max cooling        -> echo 6F 03 <n>
  2F 60 FD ...    exhaust flap job       -> 6F 60 FD ...      (MG1 job; F30 MEVD17 untested)
  01 0C / 01 0D   OBD rpm / speed from the live replay (4807 / 4AB1)
Usage: diag_sim.py [--port 6801] [--record DIR]
"""
import os
import argparse
import json
import socket
import struct
import threading
import time
from pathlib import Path

HOME = Path(os.environ.get("IDRIVE_HOME", Path.home() / "idrive"))   # flag files: dragsim, engineoff, mhdslot
MHD_TUNED = os.environ.get("DIAG_SIM_MHD", "1") == "1"   # answer MHD+ 2F jobs (map switch echo)
TESTER = 0xF4


class Car:
    def __init__(self, record):
        self.rounds = []          # list of {did: bytes}
        self.static = {}
        self.dtcs = {}
        self.start = time.time()
        self.lock = threading.Lock()
        if record is None:
            self.rounds = synthetic_rounds()
            self.dtcs = {0x12: [], 0x18: [], 0x40: []}
            return
        cur, last_t = {}, None
        for line in (record / "live" / "DME_0x12.jsonl").read_text().splitlines():
            m = json.loads(line)
            if not m.get("hex") or not m.get("did"):
                continue                       # rejected / failed reads in the capture
            if m["did"].upper() in cur:
                self.rounds.append(cur)
                cur = {}
            cur[m["did"].upper()] = bytes.fromhex(m["hex"])
        if cur:
            self.rounds.append(cur)
        for f in (record / "didscan").glob("*.jsonl"):
            ecu = int(f.name.split("_0x")[1][:2], 16)
            for line in f.read_text().splitlines():
                try:
                    m = json.loads(line)
                    if m.get("hex"):
                        self.static[(ecu, m["did"].upper())] = bytes.fromhex(m["hex"])
                except (ValueError, KeyError):
                    pass
        for addr, ecu in json.loads((record / "dtcs.json").read_text()).items():
            codes = []
            for mem in (ecu.get("reading") or {}).values():
                if isinstance(mem, dict):
                    for d in mem.get("dtcs", []):
                        codes.append((bytes.fromhex(d["code"]), int(d["status"], 16)))
            self.dtcs[int(addr, 16)] = codes

    def live(self, did: str):
        if not self.rounds:
            return None
        i = int((time.time() - self.start) * 2) % len(self.rounds)   # ~2 rounds/s
        for k in range(len(self.rounds)):
            v = self.rounds[(i + k) % len(self.rounds)].get(did)
            if v is not None:
                return v
        return None

    def drag_speed(self):
        """Drag-run test: touch $IDRIVE_HOME/dragsim -> 3 s standstill, then v = 260(1-e^(-t/9.5))
        (0-100 4.6 s, 0-200 13.9 s, 200-250 ~17 s), then braking at 1 g; None when off."""
        flag = HOME / "dragsim"
        if not flag.exists():
            return None
        t = time.time() - flag.stat().st_mtime - 3.0
        if t < 0:
            return 0.0
        import math
        if t < 32:
            return 260 * (1 - math.exp(-t / 9.5))
        return max(0.0, 260 * (1 - math.exp(-32 / 9.5)) - (t - 32) * 35)

    def answer(self, ecu: int, req: bytes) -> bytes:
        sid = req[0]
        self.requests = getattr(self, "requests", 0) + 1     # power-policy tests: total requests
        (HOME / "diag_sim.count").write_text(str(self.requests)) if HOME.is_dir() else None
        # engine-off test: touch $IDRIVE_HOME/engineoff -> rpm 0
        if (HOME / "engineoff").exists() and ecu == 0x12 and (
                req[:3] == b"\x22\x48\x07" or req[:2] == b"\x01\x0c"):
            return bytes([0x62, 0x48, 0x07, 0, 0]) if sid == 0x22 else bytes([0x41, 0x0C, 0, 0])
        if sid == 0x22 and len(req) == 3 and ecu == 0x12 and req[1:3] == b"\x4a\xb1":
            v = self.drag_speed()
            if v is not None:
                return bytes([0x62, 0x4A, 0xB1]) + struct.pack(">h", int(v * 100) if v < 327 else 32700)
        # TEST ONLY: pretend MHD exposes its active slot (0-based) in 62C1, to exercise the OEM+ MHD
        # worker's read-back learning. Nothing says the real car does this.
        if sid == 0x22 and ecu == 0x12 and req[1:3] == b"\x62\xc1" and MHD_TUNED:
            f = HOME / "mhdslot"        # TEST: map changed "in the MHD app"
            if f.exists():
                self.mhd_slot = int(f.read_text().strip() or 0)
                f.unlink()
            return bytes([0x62, 0x62, 0xC1, 0x00, getattr(self, "mhd_slot", 0)])
        if sid == 0x22 and len(req) >= 3:
            did = req[1:3].hex().upper()
            v = self.live(did) if ecu == 0x12 else None
            if v is None:
                v = self.static.get((ecu, did))
            return bytes([0x62]) + req[1:3] + v if v is not None else bytes([0x7F, 0x22, 0x31])
        if sid == 0x19 and len(req) >= 3 and req[1] == 0x02:
            if ecu not in self.dtcs:
                return bytes([0x7F, 0x19, 0x11])
            with self.lock:
                body = b"".join(code + bytes([st]) for code, st in self.dtcs[ecu] if st & req[2])
            return bytes([0x59, 0x02, 0xFF]) + body
        if sid == 0x14:
            with self.lock:
                if ecu in self.dtcs:
                    self.dtcs[ecu] = []
            return bytes([0x54])
        if sid == 0x2F and ecu == 0x12 and MHD_TUNED:
            if req[1:2] == b"\x01" and len(req) >= 3:
                self.mhd_slot = req[2]
            if req[1:2] in (b"\x01", b"\x02", b"\x03") or req[1:3] == b"\x60\xfd":
                return bytes([0x6F]) + req[1:]
        if sid == 0x01 and ecu == 0x12 and len(req) == 2:
            if req[1] == 0x0C:
                rpm = self.live("4807")
                r = int.from_bytes(rpm, "big") * 4 if rpm else 3200
                return bytes([0x41, 0x0C]) + struct.pack(">H", min(0xFFFF, r))
            if req[1] == 0x0D:
                return bytes([0x41, 0x0D, 0])
            if req[1] == 0x42:              # control module voltage, mV (simulated: idle, charging)
                return bytes([0x41, 0x42]) + struct.pack(">H", 14100)
        if sid == 0x10:
            return bytes([0x50, req[1], 0x00, 0x32, 0x01, 0xF4])
        if sid == 0x3E:
            return bytes([0x7E, 0x00])
        return bytes([0x7F, sid, 0x11])


def synthetic_rounds():
    """Idle engine, warm: DME DIDs used by the OEM+ style apps (raw big-endian bytes)."""
    import math
    rounds = []
    for k in range(120):
        w = math.sin(k / 6.0)
        rpm = int((760 + 25 * w) * 2)                       # 4807: s16 x 0.5 rpm
        rounds.append({
            "4807": struct.pack(">h", rpm),
            "4300": struct.pack(">h", int((90.5 + 273.14) * 10)),   # coolant 0.1 K
            "4402": struct.pack(">H", int((95 + 48) / 0.75)),       # oil temperature
            "580F": bytes([int((32 + 48) / 0.75)]),                 # intake air
            "5512": bytes([int((18 + 40) / 0.5)]),                  # outside air
            "4201": struct.pack(">H", int(1013 * 256 / 10)),        # ambient pressure
            "4205": struct.pack(">H", int((1013 - 300 + 40 * w) * 256 / 20)),  # manifold (vacuum)
            "4AB0": struct.pack(">H", int(1013 * 256 / 10)),
            "56D7": struct.pack(">H", int(98 / 0.02)),              # rail pressure
            "4436": struct.pack(">H", int(1013 + 1600 + 50 * w)),   # oil pressure abs hPa
            "5640": struct.pack(">H", 4096 + int(30 * w)),          # lambda
            "4A49": struct.pack(">h", int(80 + 10 * w)),            # ignition 0.1 deg
            "4AB1": struct.pack(">h", 0),                           # vehicle speed
            "4502": bytes([6]),                                     # cylinders
        })
    return rounds


def frame(ctrl: int, payload: bytes) -> bytes:
    return struct.pack(">IH", len(payload), ctrl) + payload


def serve(conn: socket.socket, car: Car):
    buf = b""
    with conn:
        while True:
            data = conn.recv(4096)
            if not data:
                return
            buf += data
            while len(buf) >= 6:
                length, ctrl = struct.unpack(">IH", buf[:6])
                if len(buf) < 6 + length:
                    break
                payload, buf = buf[6:6 + length], buf[6 + length:]
                if ctrl == 0x0011:                       # vehicle ident request
                    conn.sendall(frame(0x0011, b"DIAGADR10BMWMAC000000000000BMWVINSIMULATED00000000"))
                    continue
                if ctrl != 0x0001 or len(payload) < 3:
                    continue
                src, dst, req = payload[0], payload[1], payload[2:]
                conn.sendall(frame(0x0002, payload[:2] + req[:5]))      # ack
                time.sleep(0.01)
                resp = car.answer(dst, req)
                conn.sendall(frame(0x0001, bytes([dst, src]) + resp))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=6801)
    ap.add_argument("--record", type=Path, default=None,
                    help="IDriveReader record folder (live/DME_0x12.jsonl, didscan/, dtcs.json); default: synthetic")
    args = ap.parse_args()
    car = Car(args.record)
    print(f"diag_sim: {len(car.rounds)} live rounds, {len(car.static)} static DIDs, "
          f"{sum(len(v) for v in car.dtcs.values())} DTCs in {len(car.dtcs)} ECUs, port {args.port}", flush=True)
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", args.port))
    srv.listen(8)
    while True:
        conn, peer = srv.accept()
        print(f"diag_sim: connection from {peer}", flush=True)
        threading.Thread(target=serve, args=(conn, car), daemon=True).start()


if __name__ == "__main__":
    main()
