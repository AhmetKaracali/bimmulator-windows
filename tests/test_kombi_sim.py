import io
from pathlib import Path
import runpy
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
from kombi_rpm import MAILBOX_OFFSET, SPEED_OFFSET, WORD, create_ram, open_rpm_mailbox
from kombi_sipc import Link, Message, read_message

Vehicle = runpy.run_path(str(TOOLS / "kombi-sim.py"))["Vehicle"]


class KombiTests(unittest.TestCase):
    def test_vehicle_updates_are_atomic(self):
        vehicle = Vehicle()
        before = vehicle.snapshot()
        for invalid in (float("nan"), -1, "90", True):
            with self.assertRaises(ValueError):
                vehicle.update({"gear": "D", "speed_kph": invalid})
            self.assertEqual(vehicle.snapshot(), before)
        state = vehicle.update({"gear": "D", "speed_kph": 88, "engine_rpm": 3100,
                                "guidance": {"turn": "left", "distance_m": 250, "road": "Main"}})
        self.assertEqual(state["revision"], 1)
        self.assertEqual(state["guidance"]["distance_m"], 250)
        self.assertEqual(vehicle.update({"guidance": None})["gear"], "D")

    def test_vehicle_publishes_valid_inputs_in_firmware_units(self):
        with tempfile.TemporaryDirectory() as directory:
            ram = Path(directory) / "gss.ram"
            create_ram(ram)
            with open_rpm_mailbox(ram) as mailbox:
                vehicle = Vehicle(mailbox)
                self.assertEqual(WORD.unpack_from(mailbox, MAILBOX_OFFSET), (81,))
                self.assertEqual(WORD.unpack_from(mailbox, SPEED_OFFSET), (1,))
                vehicle.update({"engine_rpm": 4103, "speed_kph": 87.26})
                self.assertEqual(WORD.unpack_from(mailbox, MAILBOX_OFFSET), (411,))
                self.assertEqual(WORD.unpack_from(mailbox, SPEED_OFFSET), (874,))
                with self.assertRaises(ValueError):
                    vehicle.update({"engine_rpm": 0, "speed_kph": 0, "gear": "invalid"})
                self.assertEqual(WORD.unpack_from(mailbox, MAILBOX_OFFSET), (411,))
                self.assertEqual(WORD.unpack_from(mailbox, SPEED_OFFSET), (874,))
                vehicle.update({"engine_rpm": 0, "speed_kph": 0})
                self.assertEqual(WORD.unpack_from(mailbox, MAILBOX_OFFSET), (1,))
                self.assertEqual(WORD.unpack_from(mailbox, SPEED_OFFSET), (1,))

    def test_sipc_layout_and_padding(self):
        frame = bytes.fromhex("1f000000 01000000 02000000 03000000 3412 cdab"
                              " ca00 020c 0c000000 78563412 11223300")
        message = Message(1, 2, 3, 0x1234, 0xabcd, 0xca, 0, 0xc02, 0xc, 0x12345678, b"\x11\x22\x33")
        self.assertEqual(message.to_wire(), frame)
        self.assertEqual(Message.from_json(message.to_json()), message)
        stream = io.BytesIO(frame + frame)
        self.assertEqual(read_message(stream), message)
        self.assertEqual(read_message(stream), message)
        self.assertIsNone(read_message(stream))
        for malformed in (frame[:3], frame[:-1], b"\xff" * 4):
            with self.assertRaises(ValueError):
                read_message(io.BytesIO(malformed))

    def test_sipc_link_reconnect_and_sequence(self):
        class Connection:
            def sendall(self, value):
                self.last_write = value

        link = Link()
        message = Message(1, 2, 3, 1, 2, 5, 0, 0xc7b, 0xc, 0, b"\x01\x02")
        connection = Connection()
        self.assertTrue(link.attach(connection))
        self.assertFalse(link.attach(Connection()))
        link.send(message)
        self.assertEqual(connection.last_write, message.to_wire())
        link.detach(connection)
        with self.assertRaises(ConnectionError):
            link.send(message)
        self.assertTrue(link.attach(Connection()))
        link.record("from_hu", message)
        self.assertEqual(link.status(1)["messages"][0]["direction"], "from_hu")
        self.assertEqual(link.status(2)["messages"], [])


if __name__ == "__main__":
    unittest.main()
