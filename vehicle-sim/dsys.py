"""DSYSMOSTServer 4.5 payload codec (reversed from libimp_sys_most_base_nbt.cpp-ne.so.17:
toDSI(CDSYSMOSTServerRequest/Response), DSYSMOSTTypes::DSIWrite*).

Values are written with natural alignment (u16 on 2, u32 on 4) relative to the payload start;
the DSI stream body starts 16-byte aligned, so that matches the guest encoder.
Names marked '?' are inferred from argument types, not yet confirmed at runtime.
"""
import struct

NAMES = {
    0x00: "requestRegisterDevices", 0x01: "requestRegisterDevCtrls", 0x02: "requestProcessMessage",
    0x03: "req03(no args)?", 0x04: "requestUnregisterDevices", 0x05: "requestUnregisterDevCtrls",
    0x06: "requestChangeInstID", 0x07: "req07(u32): CleanUp/EnableNotificationProxy?",
    0x08: "req08(no args)?", 0x09: "req09(u16): registerMOSTSubnet?", 0x0A: "req0A(no args)?",
    0x0B: "requestSetRegistryFilter", 0x0C: "requestSetCommunicationCtrl",
    0x0D: "requestRegisterExtDevices", 0x0E: "requestProcessMessageVector",
    0x0F: "req0F(string): registerMOSTClientExt?", 0x10: "req10(no args)?",
    0x11: "req11(u32): CleanUp/EnableNotificationProxy?",
    0x80000000: "responseMOSTClient", 0x80000001: "informationProcessMessage",
    0x80000002: "informationChangeInstID", 0x80000003: "informationConnect",
    0x80000004: "info04(fblock keys): Activate/Deactivate/Disconnect?",
    0x80000005: "info05(fblock keys): Activate/Deactivate/Disconnect?",
    0x80000006: "info06(fblock keys): Activate/Deactivate/Disconnect?",
    0x80000007: "informationCleanUp", 0x80000008: "responseMOSTSubnet",
    0x80000009: "informationRegistry",
    0xC0000000: "attr MOSTCommunicationState", 0xC0000001: "attr Registry",
    0xC0000002: "attr DeviceID", 0xC0000003: "attr CommunicationCtrl", 0xC0000004: "attr ExtDeviceID",
}


def name(ident):
    return NAMES.get(ident, f"unknown {ident:#x}")


class Reader:
    def __init__(self, data):
        self.d, self.p = data, 0

    def _a(self, n):
        self.p += -self.p % n

    def u8(self):
        v = self.d[self.p]; self.p += 1; return v

    def u16(self):
        self._a(2); v = struct.unpack_from("<H", self.d, self.p)[0]; self.p += 2; return v

    def u32(self):
        self._a(4); v = struct.unpack_from("<I", self.d, self.p)[0]; self.p += 4; return v

    def i32(self):
        self._a(4); v = struct.unpack_from("<i", self.d, self.p)[0]; self.p += 4; return v

    def blob(self):  # CHBBuffer / CHBString: assumed u32 length + bytes
        n = self.u32(); v = self.d[self.p:self.p + n]; self.p += n; return v

    def rest(self):
        return self.d[self.p:]


class Writer:
    def __init__(self):
        self.b = bytearray()

    def _a(self, n):
        self.b += bytes(-len(self.b) % n)

    def u8(self, v):
        self.b += bytes([v & 0xFF]); return self

    def u16(self, v):
        self._a(2); self.b += struct.pack("<H", v & 0xFFFF); return self

    def u32(self, v):
        self._a(4); self.b += struct.pack("<I", v & 0xFFFFFFFF); return self

    def i32(self, v):
        self._a(4); self.b += struct.pack("<i", v); return self

    def blob(self, data):
        self.u32(len(data)); self.b += data; return self

    def bytes(self):
        return bytes(self.b)


# --- composite types -------------------------------------------------------------------------
def read_header(r):
    return {"dst": r.u16(), "src": r.u16(), "fblock": r.u8(), "inst": r.u8(), "func": r.u16(),
            "op": r.u8(), "tag": r.u32()}


def write_header(w, h):
    w.u16(h["dst"]).u16(h["src"]).u8(h["fblock"]).u8(h["inst"]).u16(h["func"]).u8(h["op"]).u32(h.get("tag", 0))


def read_message(r):
    m = {"transmission": r.i32(), "variant": r.i32()}
    m["variant_value"] = r.i32() if m["variant"] in (1, 2) else None
    m.update(read_header(r))
    m["payload"] = r.blob().hex()
    return m


def write_message(w, m):
    w.i32(m.get("transmission", 0)).i32(m.get("variant", 2))
    if m.get("variant", 2) in (1, 2):
        w.i32(m.get("variant_value", 0))
    write_header(w, m)
    w.blob(bytes.fromhex(m["payload"]) if isinstance(m["payload"], str) else m["payload"])


def read_vec(r, item):
    n = r.i32()
    if n < 0 or n > 4096:
        raise ValueError(f"bad vector length {n}")
    return [item(r) for _ in range(n)]


def write_registry(w, entries):
    """entries: [(fblock_key, device_id)], fblock_key = fblock << 8 | instance."""
    w.i32(len(entries))
    for key, dev in entries:
        w.u16(key).u16(dev)
    return w


def decode(ident, payload):
    """Best-effort decode for logging; returns dict or error text."""
    r = Reader(payload)
    try:
        if ident in (0x00, 0x01, 0x04, 0x05, 0x0B):
            out = {"handle": r.u32(), "fblock_keys": [f"{k:04x}" for k in read_vec(r, Reader.u16)]}
        elif ident == 0x02:
            out = {"handle": r.u32(), "message": read_message(r)}
        elif ident == 0x0E:
            out = {"handle": r.u32(), "messages": read_vec(r, read_message)}
        elif ident == 0x06:
            out = {"handle": r.u32(), "fblock_key": r.u16(), "inst": r.u8()}
        elif ident in (0x07, 0x11, 0x0C, 0x80000008, 0xC0000000, 0xC0000003):
            out = {"value": r.u32()}
        elif ident in (0x09, 0xC0000002, 0xC0000004):
            out = {"value": r.u16()}
        elif ident == 0x0D:
            out = {"handle": r.u32(), "entries": read_vec(r, lambda rr: (f"{rr.u16():04x}", rr.blob().decode("latin-1")))}
        elif ident == 0x0F:
            out = {"string": r.blob().decode("latin-1")}
        elif ident == 0x80000000:
            out = {"handle": r.u32(), "device_id": r.u16()}
        elif ident == 0x80000001:
            out = read_message(r)
        elif ident in (0x80000009, 0xC0000001):
            out = {"registry": [(f"{k:04x}", f"{d:04x}") for k, d in read_vec(r, lambda rr: (rr.u16(), rr.u16()))]}
        else:
            return None
        rest = r.rest()
        if rest:
            out["_rest"] = rest.hex()
        return out
    except Exception as error:  # layout guess wrong: keep the raw bytes in the log
        return f"decode error: {error}"
