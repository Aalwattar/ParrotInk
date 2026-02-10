from unittest.mock import MagicMock, call, patch

import win32con

from engine.injector import inject_text


class TestInjector:
    @patch("engine.injector.win32api")
    @patch("engine.injector.time")
    def test_inject_text_basic(self, mock_time, mock_win32):
        # Test injecting 'a'
        inject_text("a")

        # Expect calls: Unicode key down, key up for 'a' (codepoint 97)
        # KEYEVENTF_UNICODE = 4
        # KEYEVENTF_KEYUP = 2
        expected_calls = [
            call.keybd_event(0, 97, 4, 0),
            call.keybd_event(0, 97, 6, 0),
        ]
        mock_win32.assert_has_calls(expected_calls, any_order=False)

    @patch("engine.injector.win32api")
    @patch("engine.injector.time")
    def test_inject_text_with_shift(self, mock_time, mock_win32):
        # 'A' (codepoint 65)
        inject_text("A")

        # With UNICODE, we don't need manual shift for 'A' because the 
        # system handles the codepoint directly.
        expected_calls = [
            call.keybd_event(0, 65, 4, 0),
            call.keybd_event(0, 65, 6, 0),
        ]
        mock_win32.assert_has_calls(expected_calls, any_order=False)

    @patch("engine.injector.win32api")
    @patch("engine.injector.time")
    def test_inject_empty(self, mock_time, mock_win32):
        inject_text("")
        assert mock_win32.keybd_event.call_count == 0