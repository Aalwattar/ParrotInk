from unittest.mock import MagicMock

import pytest

from engine.app_types import AppState
from engine.indicator_ui import IndicatorWindow
from engine.ui_bridge import UIBridge, UIEvent


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
    h.update_status_icon("Connecting to OpenAI...")

    # Check if indicator tracked it
    assert h._last_status_msg == "Connecting to OpenAI..."

    # Check if implementation was called
    mock_impl.update_status_icon.assert_called_with("Connecting to OpenAI...")


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
    h._last_status_msg = "Connecting..."
    h._render_preview()

    # It should pass "Connecting..." to the implementation
    mock_impl.update_partial_text.assert_called_with("Connecting...")

    # 2. Transcription text present
    h.on_partial("Hello")
    h._render_preview()

    # It should show "Hello", NOT "Connecting..."
    mock_impl.update_partial_text.assert_called_with("Hello")


def test_hud_concurrent_updates(bridge):
    """
    Test that rapid updates through UIBridge are handled without crashing.
    """
    # We use the real bridge and a mock Tray/Indicator
    mock_indicator = MagicMock()
    # Mocking the Tray's behavior when polling
    for _ in range(100):
        bridge.update_partial_text("Partial")
        bridge.update_status_message("Status")
        bridge.update_provider("openai")
        bridge.set_state(AppState.LISTENING)

    # Process some events
    for _ in range(400):
        event = bridge.get_event()
        if not event:
            break
        msg_type, data = event
        if msg_type == UIEvent.UPDATE_PARTIAL_TEXT:
            mock_indicator.update_partial_text(data)
        elif msg_type == UIEvent.UPDATE_STATUS_MESSAGE:
            mock_indicator.update_status_icon(data)
        elif msg_type == UIEvent.UPDATE_PROVIDER:
            mock_indicator.update_provider(data)
        elif msg_type == UIEvent.SET_STATE:
            mock_indicator.update_status(data == AppState.LISTENING)

    assert mock_indicator.update_partial_text.call_count == 100
    assert mock_indicator.update_provider.call_count == 100
