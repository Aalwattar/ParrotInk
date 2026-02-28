from unittest.mock import MagicMock

import pytest

from engine.constants import STATUS_CONNECTING, STATUS_LISTENING, STATUS_READY
from engine.indicator_ui import IndicatorWindow
from engine.ui_bridge import UIBridge


@pytest.fixture
def bridge():
    return UIBridge()


@pytest.fixture
def hud(bridge):
    # Mock HudOverlay to avoid Win32 issues in tests
    mock_impl = MagicMock()
    # We patch IndicatorWindow to use our mock_impl
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("engine.indicator_ui.HUD_AVAILABLE", True)
        mp.setattr("engine.indicator_ui.HudOverlay", lambda **kwargs: mock_impl)
        h = IndicatorWindow()
        return h, mock_impl


def test_hud_status_propagation(hud):
    h, mock_impl = hud

    # Simulate a status update
    h.update_status_icon(STATUS_CONNECTING)

    # Check if indicator tracked it
    assert h._last_status_msg == STATUS_CONNECTING

    # Check if implementation was called
    mock_impl.update_status_icon.assert_called_with(STATUS_CONNECTING)


def test_hud_provider_mismatch(hud):
    """
    Test that the HUD can receive and track provider updates.
    """
    h, mock_impl = hud

    # This should be implemented
    h.update_provider("assemblyai")
    assert h._current_provider == "assemblyai"
    mock_impl.update_provider.assert_called_with("assemblyai")


def test_hud_render_preview_logic(hud):
    h, mock_impl = hud

    # 1. No text, specific status
    h._committed_text = ""
    h._current_partial_text = ""
    h._last_status_msg = STATUS_CONNECTING
    h._render_preview()

    # It should pass STATUS_CONNECTING to the implementation
    mock_impl.update_partial_text.assert_called_with(STATUS_CONNECTING)

    # 2. Transcription text present
    h.on_partial("Hello")
    h._render_preview()

    # It should show "Hello", NOT STATUS_CONNECTING
    mock_impl.update_partial_text.assert_called_with("Hello")

    # 3. No text, recording state (Placeholder logic)
    h._committed_text = ""
    h._current_partial_text = ""
    h._last_status_msg = ""
    h.update_status(True)
    h._render_preview()
    # It should show STATUS_LISTENING
    mock_impl.update_partial_text.assert_called_with(STATUS_LISTENING)

    # 4. Ready status during start of session
    h.update_status_icon(STATUS_READY)
    h.update_status(True)
    h._render_preview()
    # Ready should survive if no text is present
    mock_impl.update_partial_text.assert_called_with(STATUS_READY)
