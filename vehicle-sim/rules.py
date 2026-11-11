"""NAL-SIPC (MOST data path) rules for ioc_sim.py — the 'external most' the OMAP talks to.

Two jobs:
1. Act as the Jacinto MSS server towards the OMAP `most` client: internal MSS messages (FBlock 0x02,
   tag 0xF0000000, src = J5 subnet 0x1000, dst = OMAP subnet 0x2000): 0xF00 = MOST communication
   state, 0xF02 = registry sync (u16 2 + (u16 device, u16 fblockKey) pairs, little-endian).
   Reversed from most!0x12c210 (RegSync TX) / 0x130a14 (processInternalMSSMessage).
2. Be the rest of the car: answer the HMI's Notification.Set (fn 0x001, payload 01|dev BE|fkt BE)
   with an ack + the property Status (big-endian MOST payloads).
   Property semantics/values follow herrbimmer/IDEmu docs/V850.md + idemu/most.py (verified there on
   HU 007.051.002): CTerminalStatus 05/0:0x21F first byte 12 (KL15) enables the My Vehicle items;
   SystemFunctionPowerMode D1/2: 0xC10 bit4 of byte 4 = key in car, 0x430 = 3, 0x434 = 0x63.

Reloaded on every incoming message (the HU sends FBlock CA.00 fn 0x247 Status every 10 s).
"""
import os
import json
import math
import struct
import sys
import threading
import time
from pathlib import Path

VEHICLE_NODE = 0x0200        # simulated ECUs
J5_SUBNET, OMAP_SUBNET = 0x1000, 0x2000
MSS_TAG = 0xF0000000
OP_SET, OP_GET, OP_STATUS = 0x0, 0x1, 0xC

# (fblock, instance) offered by the simulated car
EXTERNAL_FBLOCKS = [
    (0x05, 0x00),                                     # Vehicle
    (0xE0, 0x00), (0xE0, 0x01),                       # Kombi
    (0xD1, 0x02), (0xD1, 0x04), (0xD1, 0x10), (0xD1, 0x11),   # SystemFunctionPowerMode & co
    (0xE5, 0x01), (0xE5, 0x03), (0xE5, 0x0F),         # CentralControlSystem
    (0xC0, 0x03),                                     # CAN devices
    (0x03, 0x00), (0x71, 0x00),                       # ConnectionMaster?, Climate
    (0xE2, 0x02), (0xE2, 0x05), (0xE2, 0x06),
    # Jacinto-side / other-ECU devices of an NBT EVO car (IDEmu hmi_most_map device list);
    # the OMAP itself registers 07/11 D7/01 D8/01 D9/01 10/01 CF/01 CA/00 D1/26.
    (0x20, 0x00), (0x22, 0x02),                       # AudioMaster, amplifier
    (0x40, 0x00), (0x43, 0x02),                       # AM/FM tuner, DAB
    (0x24, 0x0C), (0x24, 0x0D), (0x24, 0x0E), (0x24, 0x0F), (0x24, 0x70),   # AUX/USB, CarPlay
    (0x32, 0x01),                                     # MultiMediaPlayer
    (0x54, 0x00), (0x50, 0x01), (0x50, 0x02), (0x51, 0x00),   # Bluetooth, telephone, phone book
    (0xE4, 0x00), (0xC9, 0x00), (0xED, 0x00),         # sound apps, services, PIM
    (0xD1, 0x00), (0xD1, 0x05), (0xD1, 0x09), (0xD1, 0xA0), (0xD1, 0x07),   # system functions
    (0xC0, 0x00), (0xC0, 0x04), (0xC0, 0x05), (0xC0, 0x07), (0xC0, 0x08), (0xC0, 0x09), (0xC0, 0x0A),
    (0xE2, 0x00), (0xE1, 0x00), (0x82, 0x00),         # night vision, HUD
    (0xDC, 0x01), (0xDE, 0x00), (0xDE, 0xEC), (0xA0, 0x01), (0xA0, 0x02),   # data/telematics/WLAN
    (0x15, 0x02), (0x15, 0x03), (0x15, 0x0C),         # steering-wheel / centre-stack controls
    (0xD3, 0x00), (0xD4, 0x00), (0xA2, 0x00),         # mass storage, SW update, NFC
]
ANNOUNCE_VERSION = 7      # bump to re-announce the registry to a running HU

# Our car (F30 340i), engine running, key in car, standing still in P.
CAR = {
    "terminal": 12,          # KL15
    "speed_kmh": 0.0,
    "gear": 0,
    "key": 1,
    "mileage_km": 85000,
    "oil_temp_c": 95,
    "tyres_kpa": (230, 230, 250, 250),     # FL FR RL RR
    "avg_speed_kmh": 48.5,
    "avg_cons_l100": 9.8,
    # Sport displays (B58 340i: 326 hp / 450 Nm). Gauge full scale = 80 * (index + 1):
    # power index 4 -> 0..400 hp, torque index 5 -> 0..480 Nm.
    "power_scale_index": 4,
    "torque_scale_index": 5,
    "peak_hp": 326,
    "peak_nm": 450,
    "idle_hp": 12,
    "idle_nm": 55,
    "pull_period_s": 12.0,   # idle, a 4 s full-throttle pull, back to idle
}

# Payload layouts read from the HmiMain3D 006.027.001 deserializers (vtable slot 6 of each
# CPxyVehicle::<Property> class, reader helpers u8 0x1f91e70 / u16 0x1f923b8 with their range
# arguments):
#   COilTemperature 0xCE8          u8 (0..255)           scaling assumed degC + 48
#   CVehicleDynamicEngine 0xC7B    u8, u8                power, torque in % of gauge full scale
#                                                        (verified on screen: 50 -> half scale)
#   CVehicleDynamicEngineScaling   u8<=15, u8<=15, u8, u8, u16, u16
#                                  byte0 = torque scale index, byte1 = power scale index,
#                                  full scale = 80 * (index + 1) in the display unit (scan
#                                  2026-11-10); the rest unknown, sent as 0
#   CTyrePressure 0xC02            4 x u16
#   COilDipstick2 0x22F            u8<=3, u16<=0xfff, u16<=0xfff, u8<=15
#   CMileageKM 0xCA0               u32 (helper 0x1f922c4)
LIVE = [(0x05, 0x00, 0xC7B), (0x05, 0x00, 0xCE8), (0x05, 0x00, 0xC01)]
WELCOME_SECONDS = 40.0        # PMD_Welcomescreen after the HU connects, then PMD_Fullon_useron
# Kept across hot reloads (a reload must not restart the welcome phase of a running HU).
_SESSION_START = getattr(sys.modules.get("rules"), "_SESSION_START", None) or [time.time()]


def welcome_phase():
    return time.time() - _SESSION_START[0] < WELCOME_SECONDS


TICK = 0.5    # LIVE values are pushed every TICK seconds to subscribers

# Optional: a local herrbimmer/IDEmu checkout (PolyForm Noncommercial; not included here).
IDEMU_DIR = Path(os.environ.get("IDRIVE_IDEMU_DIR", Path.home() / "IDEmu"))
DEFAULTS_FILE = IDEMU_DIR / "idemu" / "data" / "hmi_property_defaults.json"


def defaults():
    try:
        return json.loads(DEFAULTS_FILE.read_text())["defaults"]
    except (OSError, ValueError, KeyError):
        return {}


# Experiments: (fblock, inst, fkt) -> payload, pushed once to the HMI whenever this dict changes.
OVERRIDES = {
    (0xD1, 0x04, 0xC00): bytes([1]),
    (0xD1, 0x04, 0xC01): bytes([0, 1]),
}
HMI_DEV = 0x2007


PROBE_FILE = Path(os.environ.get("IDRIVE_HOME", Path.home() / "idrive")) / "probe.json"   # {"05:0:c01": "hex payload", ...} for live experiments


def probes():
    try:
        return {tuple(int(x, 16) for x in k.split(":")): bytes.fromhex(v)
                for k, v in json.loads(PROBE_FILE.read_text()).items()}
    except (OSError, ValueError):
        return {}


def status_for(fb, inst, fkt):
    probe = probes().get((fb, inst, fkt))
    if probe is not None:
        return probe
    if (fb, inst, fkt) in OVERRIDES:
        return OVERRIDES[(fb, inst, fkt)]
    if (fb, inst) == (0x05, 0x00):
        if fkt == 0x21F:     # CTerminalStatus: 3 x u8 <= 15
            return struct.pack(">BBB", CAR["terminal"], 1, 0)
        if fkt == 0x224:     # CIgnitionKey: u16 | u8 | u8 | u8 | u8
            k = CAR["key"]
            return struct.pack(">HBBBB", k, k, k, k, k)
        if fkt == 0x621:     # CCarSpeed2: u16, 0.01 km/h
            return struct.pack(">H", int(CAR["speed_kmh"] * 100))
        if fkt in (0x228, 0xCC2):   # CGearBox / CGearIndicator
            return struct.pack(">B", CAR["gear"])
        if fkt == 0x22C:     # CReverseGear
            return b"\x00"
        if fkt == 0xCA0:     # CMileageKM
            return struct.pack(">I", CAR["mileage_km"])
        if fkt == 0xCE8:     # COilTemperature
            return struct.pack(">B", max(0, min(255, int(CAR["oil_temp_c"]) + 48)))
        if fkt == 0xC02:     # CTyrePressure: 4 x u16, shown as raw x 0.1 (bar x 10), iocsim/TPM-RE.md
            return struct.pack(">4H", *(int(round(k / 10.0)) for k in CAR["tyres_kpa"]))
        if fkt == 0xC01:     # CTyresStatus (TPM-RE.md): byte2 0xA0 = RDC active (OK), byte3 0x80 = no
            # pressure loss; byte1 must change at least every 17.5 s or the HMI forces "failure".
            return bytes([0x00, int(time.time() / 2) % 15, 0xA0, 0x80, 0x00])
        if fkt == 0xC18:     # CTyreState: 12 bytes, byte0 0xFE = normal (no reset running)
            return bytes([0xFE] + [0x00] * 11)
        if fkt == 0x22F:     # COilDipstick2: status, level, ?, detail (semantics unverified)
            return struct.pack(">BHHB", 1, 0x800, 0x800, 0)
        if fkt == 0xC7A:     # CVehicleDynamicEngineScaling: units?, units?, ?, ?, max power, max torque
            return struct.pack(">BBBBHH", CAR["torque_scale_index"], CAR["power_scale_index"], 0, 0, 0, 0)
        if fkt == 0xC7B:     # CVehicleDynamicEngine: power, torque (0..255 share of max)
            hp, nm = engine_now()
            power_pct = 100.0 * hp / (80 * (CAR["power_scale_index"] + 1))
            torque_pct = 100.0 * nm / (80 * (CAR["torque_scale_index"] + 1))
            return struct.pack(">BB", int(min(100, power_pct)), int(min(100, torque_pct)))
    if (fb, inst) == (0xE0, 0x00):
        if fkt == 0x515:     # CShowTimeDate: u16 ?, status u8<=15 (1 = valid; 0 shows --:--), hour,
            # minute, second, day, weekday u8<=15 (1 = Monday), month u8<=15, year u16.
            # Verified on screen 2026-11-10 (status 1 -> clock shows the time). Minute resolution so
            # the once-per-change push fires once a minute.
            t = time.localtime()
            return struct.pack(">HBBBBBBBH", 0, 1, t.tm_hour, t.tm_min, 0, t.tm_mday, t.tm_wday + 1,
                               t.tm_mon, t.tm_year)
        if fkt == 0x509:    # CBordcomputerAverage: u16 A, B..E u16<=0xfff (0.1 units), unit u8<=3, u8<=7
            # Verified on screen 2026-11-10: Onboard info shows B = avg speed, D = avg consumption;
            # IDEmu's home tile reads C / E (second trip memory).
            speed, cons = int(CAR["avg_speed_kmh"] * 10), int(CAR["avg_cons_l100"] * 10)
            return struct.pack(">HHHHHBB", 0, speed, speed, cons, cons, 1, 1)
    if (fb, inst) == (0xD1, 0x02):
        if fkt == 0xC10:     # CSyncMarker: bit 4 of byte 4 = key in car
            return bytes((0, 0, 0, 0x10 if CAR["key"] else 0))
        if fkt == 0x430:     # power state: 3 = PM_fullon_useron
            return b"\x03"
        if fkt == 0x434:     # CPowerStateDetailed: 0x63 = PMD_Fullon_useron, 0x5A = PMD_Welcomescreen
            return bytes([0x5A if welcome_phase() else 0x63])
    if (fb, inst, fkt) in SPECIAL:
        return SPECIAL[(fb, inst, fkt)]
    d = defaults().get(f"{fb:02x}:{inst}:{fkt:03x}")
    if d:
        return bytes.fromhex(d)
    return neutral(fb, inst, fkt)


# Values where the minimum-valid payload would mean something visible.
SPECIAL = {
    (0xE0, 0x01, 0xC9A): bytes([1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),   # CWelcomeAnimation (statusX valid)
    (0xC0, 0x03, 0xC25): bytes([0xFF] * 6),     # CPDCDistanceFront: no obstacle
    (0xC0, 0x03, 0xC26): bytes([0xFF] * 6),     # CPDCDistanceRear: no obstacle
}


# Record/list properties whose all-zero record would show up as a real message.
NO_NEUTRAL = {(0xE0, 0x00, 0x200), (0xE0, 0x00, 0x303),   # CNewCCMessage, CCBSServiceHint
              (0xE0, 0x00, 0x506),    # Kombi CTimer: all-zero record opened an alarm/warning page
              (0xC0, 0x05, 0xC43)}    # CANDevicesHybrid ECOTip: not a hybrid
# Note 2026-11-10: the "Uyari - Akustik uyari yok" page (CEntNoWarningTonesActivity, the audio
# settings' empty warning-tone list) was NOT caused by these values: blind key presses had opened
# it and the HMI restores its last screen at boot. Leave the menu with the MENU key.


def neutral(fb, inst, fkt):
    """Minimum valid payload built from the HmiMain3D deserializer (vehicle-sim/hmi_neutral.py)."""
    if (fb, inst, fkt) in NO_NEUTRAL:
        return None
    try:
        here = str(Path(__file__).resolve().parent)
        if here not in sys.path:
            sys.path.insert(0, here)
        import importlib
        import hmi_neutral
        stamp = (Path(__file__).resolve().parent / "hmi_neutral.py").stat().st_mtime
        if getattr(hmi_neutral, "_stamp", None) != stamp:
            hmi_neutral = importlib.reload(hmi_neutral)
            hmi_neutral._stamp = stamp
        _name, reads = hmi_neutral.lookup(fb, inst, fkt)
        if reads:
            payload, _bad = hmi_neutral.enc(reads)
            return payload
    except Exception as error:   # never break the rules on a lookup problem
        print(f"ioc rules: neutral lookup failed {error!r}", flush=True)
    return None


def engine_now():
    """(hp, Nm) now: idle with a little wobble, and every pull_period_s a 4 s full-throttle pull."""
    phase = time.time() % CAR["pull_period_s"]
    wobble = 1.0 + 0.15 * math.sin(time.time() * 2.1)
    if phase < 4.0:
        load = math.sin(math.pi * phase / 4.0) ** 0.6
    else:
        load = 0.0
    hp = CAR["idle_hp"] * wobble + (CAR["peak_hp"] - CAR["idle_hp"]) * load
    nm = CAR["idle_nm"] * wobble + (CAR["peak_nm"] - CAR["idle_nm"]) * min(1.0, load * 1.25)
    return hp, nm


def ticker(session):
    """Runs once per HU session; always calls the newest (hot-reloaded) rules module."""
    while not session.state.get("closed"):
        module = sys.modules.get("rules")
        try:
            module.on_tick(session)
        except OSError:
            session.state["closed"] = True
            return
        except Exception as error:   # keep ticking across edits
            print(f"ioc rules: tick error {error!r}", flush=True)
        time.sleep(getattr(module, "TICK", 0.5))


# Pushed once per change of their values (the HMI subscribed before these got answers).
PUSH_ONCE = [(0xD1, 0x02, 0x434), (0xE0, 0x01, 0xC9A), (0x05, 0x00, 0xCA0), (0x05, 0x00, 0xC02), (0x05, 0x00, 0x22F), (0x05, 0x00, 0xC7A),
             (0xE0, 0x00, 0x509), (0xE0, 0x00, 0x515), (0x05, 0x00, 0xC18)]


def on_tick(session):
    subs = session.state.get("subs", {})
    for key in PUSH_ONCE + [k for k in probes() if k not in PUSH_ONCE]:
        data = status_for(*key)
        marker = ("pushed",) + key
        if data is not None and session.state.get(marker) != data:
            session.state[marker] = data
            send(session, subs.get(key, HMI_DEV), VEHICLE_NODE, key[0], key[1], key[2], OP_STATUS, data)
            print(f"ioc rules: pushed {key[0]:02X}/{key[1]}:{key[2]:03X} = {data.hex()}", flush=True)
    for key in LIVE:
        data = status_for(*key)
        if data is not None:
            send(session, subs.get(key, HMI_DEV), VEHICLE_NODE, key[0], key[1], key[2], OP_STATUS, data)


def send(session, dst, src, fb, inst, func, op, payload=b"", tag=0):
    session.send(transmission=0, variant=2, info=0, dst=dst, src=src, fblock=fb, instance=inst,
                 function=func, operation=op, tag=tag, payload=bytes(payload))


def announce(session):
    send(session, OMAP_SUBNET, J5_SUBNET, 0x02, 0x00, 0xF00, OP_STATUS, struct.pack("<HB", 1, 1), MSS_TAG)
    pairs = b"".join(struct.pack("<HH", VEHICLE_NODE, fb << 8 | inst) for fb, inst in sorted(set(EXTERNAL_FBLOCKS)))
    send(session, OMAP_SUBNET, J5_SUBNET, 0x02, 0x00, 0xF02, OP_STATUS, struct.pack("<H", 2) + pairs, MSS_TAG)
    print(f"ioc rules: MSS comm-OK + registry ({len(set(EXTERNAL_FBLOCKS))} FBlocks) sent", flush=True)


def on_connect(session):
    pass


def on_message(session, m):
    if session.state.get("announced") != ANNOUNCE_VERSION:
        session.state["announced"] = ANNOUNCE_VERSION
        announce(session)
    if not session.state.get("ticker"):
        session.state["ticker"] = True
        _SESSION_START[0] = time.time() - WELCOME_SECONDS     # no welcome until the HMI subscribes
        threading.Thread(target=ticker, args=(session,), daemon=True).start()
    key = repr(sorted(OVERRIDES.items()))
    if session.state.get("overrides_pushed") != key:
        session.state["overrides_pushed"] = key
        for (ofb, oinst, ofkt), data in OVERRIDES.items():
            send(session, HMI_DEV, VEHICLE_NODE, ofb, oinst, ofkt, OP_STATUS, data)
        print(f"ioc rules: overrides pushed {[(f'{a:02X}/{b}:{c:03X}', d.hex()) for (a, b, c), d in OVERRIDES.items()]}", flush=True)
    if m["dst"] != VEHICLE_NODE:
        return
    fb, inst, fn, op, p = m["fblock"], m["instance"], m["function"], m["operation"], m["payload"]
    stats = session.state.setdefault("stats", {"answered": set(), "unknown": set()})
    if fn == 0x001 and op == OP_SET and len(p) == 5 and p[0] == 1:      # Notification.Set
        fkt = struct.unpack(">H", p[3:5])[0]
        send(session, m["src"], VEHICLE_NODE, fb, inst, 0x001, OP_STATUS, p)            # ack
        session.state.setdefault("subs", {})[(fb, inst, fkt)] = m["src"]
        if (fb, inst, fkt) == (0xD1, 0x02, 0x434) and not session.state.get("welcome_started"):
            session.state["welcome_started"] = True      # HMI is up: play the welcome screen now
            _SESSION_START[0] = time.time()
            print(f"ioc rules: welcome screen phase started ({WELCOME_SECONDS:.0f} s)", flush=True)
        data = status_for(fb, inst, fkt)
        if data is not None:
            send(session, m["src"], VEHICLE_NODE, fb, inst, fkt, OP_STATUS, data)
            if (fb, inst, fkt) not in stats["answered"]:
                stats["answered"].add((fb, inst, fkt))
                print(f"ioc rules: {fb:02X}/{inst}:{fkt:03X} = {data.hex()}", flush=True)
        elif (fb, inst, fkt) not in stats["unknown"]:
            stats["unknown"].add((fb, inst, fkt))
            print(f"ioc rules: no value for {fb:02X}/{inst}:{fkt:03X}", flush=True)
    elif op == OP_GET:
        data = status_for(fb, inst, fn)
        if data is not None:
            send(session, m["src"], VEHICLE_NODE, fb, inst, fn, OP_STATUS, data)
        elif (fb, inst, fn) not in stats["unknown"]:
            stats["unknown"].add((fb, inst, fn))
            print(f"ioc rules: Get {fb:02X}/{inst}:{fn:03X} unanswered", flush=True)
    else:
        print(f"ioc rules: {fb:02X}/{inst}:{fn:03X} op {op:X} {p.hex()} from {m['src']:04X}", flush=True)
