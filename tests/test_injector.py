import unittest
from unittest.mock import call, patch

import win32con

from engine.injector import inject_text


class TestInjector(unittest.TestCase):
    @patch("engine.injector.win32api")
    @patch("engine.injector.time")
    def test_inject_text_basic(self, mock_time, mock_win32):
        # Setup mock for VkKeyScan
        # 'a' -> 0x41 (65), shift state 0
        def side_effect(char):
            if char == "a":
                return 0x41  # 'A' key, but let's assume result logic is (shift << 8) | vk
            if char == "A":
                return 0x141  # Shift (1) << 8 | 0x41
            return -1

        mock_win32.VkKeyScan.side_effect = side_effect

        # Test injecting 'a'
        inject_text("a")

        # Expect calls: key down, key up
        expected_calls = [
            call.VkKeyScan("a"),
            call.keybd_event(0x41, 0, 0, 0),
            call.keybd_event(0x41, 0, win32con.KEYEVENTF_KEYUP, 0),
        ]
        mock_win32.assert_has_calls(expected_calls, any_order=False)

    @patch("engine.injector.win32api")
    @patch("engine.injector.time")
    def test_inject_text_with_shift(self, mock_time, mock_win32):
        # 'A' requires shift
        mock_win32.VkKeyScan.return_value = 0x141  # Shift + A

        inject_text("A")

        # Expect calls: Shift down, A down, A up, Shift up
        expected_calls = [
            call.VkKeyScan("A"),
            call.keybd_event(win32con.VK_SHIFT, 0, 0, 0),
            call.keybd_event(0x41, 0, 0, 0),
            call.keybd_event(0x41, 0, win32con.KEYEVENTF_KEYUP, 0),
            call.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0),
        ]
        mock_win32.assert_has_calls(expected_calls, any_order=False)

    @patch("engine.injector.win32api")
    def test_inject_empty(self, mock_win32):
        inject_text("")
        mock_win32.keybd_event.assert_not_called()
