#!/usr/bin/env python3
"""Check that mouse clicks and controller tilt take separate input paths."""

import io
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class Trace(io.StringIO):
    def open(self, **_options):
        return self

    def seek(self, offset, whence=io.SEEK_SET):
        # Feed the fixture as events arriving after the relay starts tailing.
        return super().seek(offset, io.SEEK_SET if whence == io.SEEK_END else whence)


class RelayTest(unittest.TestCase):
    def test_left_mouse_and_left_arrow(self):
        relay = runpy.run_path(str(Path(__file__).with_name("idrive-cid-input.py")))
        trace = Trace(
            "input_event_abs con -1, axis x, value 0x401\n"
            "input_event_abs con -1, axis y, value 0x7d6\n"
            "input_event_btn con -1, button left, down 1\ninput_event_sync\n"
            "input_event_btn con -1, button left, down 0\ninput_event_sync\n"
            "input_event_key_qcode con -1, key qcode left, down 1\ninput_event_sync\n"
            "input_event_key_qcode con -1, key qcode left, down 0\ninput_event_sync\n"
            "input_event_btn con -1, button wheel-up, down 1\ninput_event_sync\n"
        )
        sock, controller = Mock(), Mock()
        touch = relay["CidTouch"](sock, 43567)
        with patch("time.sleep", side_effect=EOFError), self.assertRaises(EOFError):
            relay["relay_input"](trace, touch, 1440, 540, controller)
        self.assertEqual(sock.sendto.call_count, 2)
        self.assertIsNone(touch.contact)
        self.assertEqual([call.args for call in controller.call_args_list], [(11,), (14,)])


if __name__ == "__main__":
    unittest.main()
