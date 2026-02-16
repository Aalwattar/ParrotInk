import unittest
from unittest.mock import MagicMock

from engine.interaction import InputMonitor


class TestHotkeySuppression(unittest.TestCase):
    def test_hotkey_non_modifier_suppression(self):
        """
        Test that the non-modifier key of a hotkey is suppressed.
        """
        on_press = MagicMock()
        on_release = MagicMock()
        monitor = InputMonitor(on_press=on_press, on_release=on_release)

        # Define the target hotkey to monitor
        monitor.set_target_hotkey("ctrl+space")

        # Mock the listener and its suppress_event method
        mock_listener = MagicMock()
        monitor._listener = mock_listener

        # Mocking the KBDLLHOOKSTRUCT 'data' for a Space key (VK_SPACE = 0x20)
        class MockData:
            def __init__(self, vk_code):
                self.vkCode = vk_code

        # Call the (yet to be implemented) filter
        # It should return False and call mock_listener.suppress_event()
        result = monitor._win32_filter(0x100, MockData(0x20))  # WM_KEYDOWN, VK_SPACE

        self.assertFalse(result, "Filter should return False for suppressed key")
        mock_listener.suppress_event.assert_called_once()

    def test_manual_event_injection_on_suppression(self):
        """
        Test that suppressed keys are still injected into the event queue.
        """
        on_press = MagicMock()
        on_release = MagicMock()
        monitor = InputMonitor(on_press=on_press, on_release=on_release)
        monitor.set_target_hotkey("ctrl+space")

        # Mock listener
        monitor._listener = MagicMock()

        class MockData:
            def __init__(self, vk_code):
                self.vkCode = vk_code

        # Simulate Space Key (0x20)
        # WM_KEYDOWN = 0x100
        monitor._win32_filter(0x100, MockData(0x20))

        # Check if the event was put into the queue
        self.assertFalse(monitor._event_queue.empty())
        event_type, key = monitor._event_queue.get()
        self.assertEqual(event_type, "press")
        self.assertEqual(key.vk, 0x20)


if __name__ == "__main__":
    unittest.main()
