"""Behaviour of the Jacinto MOSTSubSystemServer stand-in (hot-reloaded by j5_server.py).

Phase 3: central registry + message routing.
Seen: 0x0F registerMOSTClientExt("most-MOSTSubSystem") -> responseMOSTClient(handle, devId),
0x09 registerMOSTSubnet(0x2000) -> responseMOSTSubnet, then 0x00 requestRegisterDevices(handle,
[fblock keys]) for every FBlock the OMAP hosts.
"""
import os
import threading

from dsys import Reader, Writer, read_message, write_message, write_registry

HU_NODE = 0x0100          # MOST logical node address of the head unit (timing master)
CLIENT_HANDLE = 1
COMM_STATE_ON = 2         # most!0x144314 switch: state 2 cancels the SYSAVAIL timeout

# FBlocks simulated by this server for the rest of the car: key -> device id.
# DISCOVERY: advertise every FBlock id (instance 1) on a simulated vehicle node so each HMI
# proxy reveals itself with its first MOST message (see 'route ?' lines in j5.out).
VEHICLE_NODE = 0x0200
DISCOVERY = True
VEHICLE_FBLOCKS = ({(fb << 8 | inst): VEHICLE_NODE for fb in range(0x01, 0xFF) for inst in (0x00, 0x01)}
                   if DISCOVERY else {})


def registry(link):
    entries = dict(VEHICLE_FBLOCKS)
    for key in link.state.setdefault("hu_fblocks", set()):
        entries[key] = HU_NODE
    return sorted(entries.items())


def publish_registry(link):
    reg = registry(link)
    link.response(0x80000009, write_registry(Writer(), reg).bytes())   # informationRegistry
    link.attribute(0xC0000001, write_registry(Writer(), reg).bytes())  # Registry attribute


def publish_attributes(link):
    link.attribute(0xC0000002, Writer().u16(HU_NODE).bytes())          # DeviceID
    link.attribute(0xC0000003, Writer().u32(0).bytes())                # CommCtrl = ENABLE
    publish_registry(link)
    link.attribute(0xC0000000, Writer().u32(COMM_STATE_ON).bytes())    # MOST communication state


def debounce_registry(link):
    timer = link.state.get("reg_timer")
    if timer:
        timer.cancel()
    timer = threading.Timer(0.3, publish_registry, args=(link,))
    link.state["reg_timer"] = timer
    timer.start()


INFO_CONNECT, INFO_DISCONNECT, INFO_ACTIVATE, INFO_DEACTIVATE = 0x80000003, 0x80000004, 0x80000005, 0x80000006


def key_vector(keys):
    w = Writer().i32(len(keys))
    for k in keys:
        w.u16(k)
    return w.bytes()


def activate(link, keys):
    link.response(INFO_ACTIVATE, key_vector(sorted(keys)))


def connect(link, keys):
    """informationConnect([DeviceInfo(fblockKey, deviceId)]) for keys we can serve."""
    reg = dict(registry(link))
    found = [(k, reg[k]) for k in sorted(keys) if k in reg]
    missing = [f"{k:04X}" for k in keys if k not in reg]
    if missing:
        print(f"  devctrl not in registry: {missing}", flush=True)
    if found:
        w = Writer().i32(len(found))
        for key, dev in found:
            w.u16(key).u16(dev)
        link.response(INFO_CONNECT, w.bytes())


def on_hello(link):
    print("rules: bridge registered (phase 3: registry + routing)", flush=True)


def route(link, msg):
    key = msg["fblock"] << 8 | msg["inst"]
    hu = link.state.setdefault("hu_fblocks", set())
    tag = f"{msg['fblock']:02X}.{msg['inst']:02X}.{msg['func']:03X}.{msg['op']:X} {msg['src']:04X}->{msg['dst']:04X} {msg['payload']}"
    if key in hu or msg["dst"] in (HU_NODE, 0x2000) and key in hu:
        # addressed to an FBlock the OMAP registered: loop it back as informationProcessMessage
        w = Writer()
        write_message(w, dict(msg, transmission=0, variant=2, variant_value=0))
        link.response(0x80000001, w.bytes())
        print(f"route loopback {tag}", flush=True)
    else:
        link.state.setdefault("unrouted", {}).setdefault(key, 0)
        link.state["unrouted"][key] += 1
        print(f"route ? {tag}", flush=True)


def on_request(link, ident, payload):
    if ident == 0x0F:     # registerMOSTClientExt(name) -> responseMOSTClient(handle, deviceId)
        link.response(0x80000000, Writer().u32(CLIENT_HANDLE).u16(HU_NODE).bytes())
    elif ident == 0x09:   # registerMOSTSubnet(subnet) -> responseMOSTSubnet(handle)
        link.response(0x80000008, Writer().u32(CLIENT_HANDLE).bytes())
        threading.Timer(1.0, startup_sequence, args=(link,)).start()
    elif ident == 0x00:           # requestRegisterDevices: FBlocks the OMAP serves
        r = Reader(payload)
        r.u32()
        keys = [r.u16() for _ in range(r.i32())]
        link.state.setdefault("hu_fblocks", set()).update(keys)
        print(f"registered HU FBlocks {[f'{k:04X}' for k in keys]} -> informationActivate", flush=True)
        activate(link, keys)
        debounce_registry(link)
    elif ident == 0x01:           # requestRegisterDevCtrls: FBlocks the OMAP wants to control
        r = Reader(payload)
        r.u32()
        keys = [r.u16() for _ in range(r.i32())]
        link.state.setdefault("devctrls", set()).update(keys)
        print(f"devctrl request {[f'{k:04X}' for k in keys]} -> informationConnect", flush=True)
        connect(link, keys)
    elif ident in (0x04, 0x05):   # unregister
        r = Reader(payload)
        r.u32()
        keys = [r.u16() for _ in range(r.i32())]
        link.state.setdefault("hu_fblocks", set()).difference_update(keys)
        debounce_registry(link)
    elif ident == 0x02:           # requestProcessMessage(handle, message)
        r = Reader(payload)
        r.u32()
        route(link, read_message(r))
    elif ident == 0x0E:           # requestProcessMessageVector(handle, [messages])
        r = Reader(payload)
        r.u32()
        for _ in range(r.i32()):
            route(link, read_message(r))
    else:
        print(f"request {ident:#x} ({len(payload)} bytes) not handled yet: {payload.hex()}", flush=True)


def seed_from_log(link, path=os.path.join(os.environ.get("IDRIVE_HOME", os.path.expanduser("~/idrive")), "j5.jsonl")):
    import json
    hu = link.state.setdefault("hu_fblocks", set())
    try:
        for line in open(path):
            e = json.loads(line)
            if e.get("kind") == "request" and e.get("id") in ("0x0", "0x1") and isinstance(e.get("decoded"), dict):
                hu.update(int(k, 16) for k in e["decoded"].get("fblock_keys", []))
    except OSError:
        pass


BROADCAST = 0x03C8
NWM_FBLOCK, FKT_CONFIGURATION, FKT_CENTRAL_REGISTRY = 0x02, 0xA00, 0xA01
OP_STATUS = 0xC
CONFIG_OK = 0x01


def most_info(link, fblock, inst, func, op, payload, src=HU_NODE, dst=BROADCAST):
    """Deliver a MOST message from the (simulated) network to the OMAP client."""
    w = Writer()
    write_message(w, {"transmission": 0, "variant": 2, "variant_value": 0, "dst": dst, "src": src,
                      "fblock": fblock, "inst": inst, "func": func, "op": op, "tag": 0,
                      "payload": bytes(payload)})
    link.response(0x80000001, w.bytes())


def nwm_config_ok(link):
    for inst in (0x00, 0x01):
        most_info(link, NWM_FBLOCK, inst, FKT_CONFIGURATION, OP_STATUS, [CONFIG_OK])


def connect_vehicle(link):
    """Proactively announce every simulated (non-HU) FBlock as connected."""
    hu = link.state.get("hu_fblocks", set())
    connect(link, [k for k in VEHICLE_FBLOCKS if k not in hu])


def startup_sequence(link):
    publish_attributes(link)
    nwm_config_ok(link)
    connect_vehicle(link)


def on_reload(link):
    if not link.state.get("hu_fblocks"):
        seed_from_log(link)
    print(f"rules: reloaded; HU FBlocks {sorted(f'{k:04X}' for k in link.state.get('hu_fblocks', ()))}", flush=True)
    publish_attributes(link)
    if link.state.get("hu_fblocks"):
        activate(link, link.state["hu_fblocks"])
    if link.state.get("devctrls"):
        connect(link, link.state["devctrls"])
    nwm_config_ok(link)
    connect_vehicle(link)
