"""TCP adapter for the stock NBT Evo MOST daemon's upstream SIPC stream."""

from collections import deque
from dataclasses import dataclass
import socket
from socketserver import StreamRequestHandler, ThreadingTCPServer
import struct
import threading


LENGTH = struct.Struct("<I")
HEADER = struct.Struct("<IIIHHBBHB3xI")
MAX_PAYLOAD = 65535
FIELDS = {
    "transmission": 0xffffffff, "variant": 2, "info": 0xffffffff,
    "dst": 0xffff, "src": 0xffff, "fblock": 0xff, "instance": 0xff,
    "function": 0xfff, "operation": 0xf, "tag": 0xffffffff,
}


@dataclass(frozen=True)
class Message:
    transmission: int
    variant: int
    info: int
    dst: int
    src: int
    fblock: int
    instance: int
    function: int
    operation: int
    tag: int
    payload: bytes

    @classmethod
    def from_json(cls, data):
        if not isinstance(data, dict) or data.keys() != FIELDS.keys() | {"payload_hex"}:
            raise ValueError("invalid MOST fields")
        for field, upper in FIELDS.items():
            if type(data[field]) is not int or not 0 <= data[field] <= upper:
                raise ValueError(f"{field} must be an integer between 0 and {upper}")
        encoded = data["payload_hex"]
        if not isinstance(encoded, str) or len(encoded) > MAX_PAYLOAD * 2:
            raise ValueError("invalid payload_hex")
        return cls(*(data[field] for field in FIELDS), bytes.fromhex(encoded))

    def to_json(self):
        return {**{field: getattr(self, field) for field in FIELDS},
                "payload_hex": self.payload.hex()}

    def to_wire(self):
        body = HEADER.pack(*(getattr(self, field) for field in FIELDS)) + self.payload
        return LENGTH.pack(len(body)) + body + bytes(-len(body) % 4)


def read_message(stream):
    raw_length = stream.read(LENGTH.size)
    if not raw_length:
        return None
    if len(raw_length) != LENGTH.size:
        raise ValueError("truncated SIPC length")
    size, = LENGTH.unpack(raw_length)
    if not HEADER.size <= size <= HEADER.size + MAX_PAYLOAD:
        raise ValueError(f"invalid SIPC frame length {size}")
    aligned = size + (-size % 4)
    frame = stream.read(aligned)
    if len(frame) != aligned:
        raise ValueError("truncated SIPC frame")
    return Message(*HEADER.unpack_from(frame), frame[HEADER.size:size])


class Link:
    def __init__(self):
        self._lock = threading.Lock()
        self._send_lock = threading.Lock()
        self._connection = None
        self._history = deque(maxlen=64)
        self._sequence = 0

    def attach(self, connection):
        with self._lock:
            if self._connection is not None:
                return False
            self._connection = connection
            return True

    def detach(self, connection):
        with self._lock:
            if self._connection is connection:
                self._connection = None

    def record(self, direction, message):
        with self._lock:
            self._sequence += 1
            self._history.append((self._sequence, direction, message))

    def status(self, after):
        with self._lock:
            messages = tuple(self._history)
            connected = self._connection is not None
            sequence = self._sequence
        return {"connected": connected, "sequence": sequence,
                "messages": [{"sequence": index, "direction": direction, **message.to_json()}
                             for index, direction, message in messages if index > after]}

    def send(self, message):
        with self._send_lock:
            with self._lock:
                connection = self._connection
            if connection is None:
                raise ConnectionError("head unit is disconnected")
            connection.sendall(message.to_wire())
            self.record("to_hu", message)

    def close(self):
        with self._lock:
            if self._connection is not None:
                try:
                    self._connection.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass


class SIPCHandler(StreamRequestHandler):
    def handle(self):
        link = self.server.link
        if not link.attach(self.request):
            return
        print("MOST SIPC connected", flush=True)
        try:
            while (message := read_message(self.rfile)) is not None:
                link.record("from_hu", message)
        except (OSError, ValueError) as error:
            print(f"MOST SIPC receive ended: {error}", flush=True)
        finally:
            link.detach(self.request)
            print("MOST SIPC disconnected", flush=True)


class SIPCServer(ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, port):
        self.link = Link()
        super().__init__(("127.0.0.1", port), SIPCHandler)
