from unittest.mock import MagicMock, patch

import pytest

from engine.constants import STATUS_CONNECTING
from engine.indicator_ui import IndicatorWindow


@pytest.fixture
def bridge():
    return MagicMock()


@pytest.fixture
def hud(bridge):
    # Mock HudOverlay to avoid Win32 issues in tests
    mock_impl = MagicMock()
    # Ensure it has the required methods to pass initialization checks
    # and that it is NOT a GdiFallbackWindow
    mock_impl.update_status = MagicMock()

    # We MUST patch the source of the import used in IndicatorWindow.__init__
    with patch("engine.hud_renderer.HUD_AVAILABLE", True):
        with patch("engine.hud_renderer.HudOverlay", return_value=mock_impl):
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

    # Update provider
    h.update_provider("AssemblyAI")

    # Check state
    assert h._current_provider == "AssemblyAI"
    mock_impl.update_provider.assert_called_with("AssemblyAI")


def test_hud_render_preview_logic(hud):
    """
    Test the complex preview rendering logic (committed vs partial text).
    """
    h, mock_impl = hud

    # 1. Partial only
    h.on_partial("hello")
    # IndicatorWindow calls update_partial_text for HudOverlay
    assert mock_impl.update_partial_text.called


def test_hud_truncation_logic(hud):
    """
    Test truncation logic separately to avoid redraw throttle issues.
    """
    h, mock_impl = hud

    # Force a small limit for testing
    h.config.ui.floating_indicator.max_characters = 50

    # 3. Truncation check
    h._committed_text = "a" * 100
    h._render_preview()

    # Get the last call arguments
    args, _ = mock_impl.update_partial_text.call_args
    display_text = args[0]
    assert display_text.startswith("…")
    assert len(display_text) <= h.config.ui.floating_indicator.max_characters
