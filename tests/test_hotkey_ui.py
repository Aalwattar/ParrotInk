from unittest.mock import patch

from engine.hotkey_ui import HotkeyRecorder


def test_hotkey_recorder_validation():
    """Verify that the hotkey recorder correctly identifies valid/invalid combinations."""
    # We mock gdiplus to avoid initialization issues during instantiation
    with patch("engine.hotkey_ui.gdiplus"):
        recorder = HotkeyRecorder(on_captured=lambda x: None)

        # Valid combos
        assert recorder._is_valid(["ctrl", "alt", "v"]) is True
        assert recorder._is_valid(["f12"]) is True
        assert recorder._is_valid(["shift", "backtick"]) is True

        # Invalid (only modifiers)
        assert recorder._is_valid(["ctrl"]) is False
        assert recorder._is_valid(["alt", "shift"]) is False
        assert recorder._is_valid([]) is False


def test_hotkey_recorder_vk_mapping():
    """Verify VK to text mapping."""
    with patch("engine.hotkey_ui.gdiplus"):
        recorder = HotkeyRecorder(on_captured=lambda x: None)
        assert recorder._vk_to_text(0x11, 0) == "ctrl"
        assert recorder._vk_to_text(0x12, 0) == "alt"
        assert recorder._vk_to_text(112, 0) == "f1"
