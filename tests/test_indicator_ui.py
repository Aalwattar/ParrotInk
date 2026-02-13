import time

from engine.indicator_ui import IndicatorWindow


def test_indicator_initialization():
    """Test that the indicator initializes with default state."""
    # We should be able to instantiate it without a real window if we mock the Win32 calls
    indicator = IndicatorWindow()
    assert indicator.is_recording is False
    assert indicator.partial_text == ""
    assert indicator.visible is False


def test_indicator_status_update():
    """Test updating the recording status."""
    indicator = IndicatorWindow()
    indicator.update_status(True)
    assert indicator.is_recording is True

    indicator.update_status(False)
    assert indicator.is_recording is False


def test_indicator_partial_text_truncation():
    """Test that the partial text display is truncated by character count (180)."""
    indicator = IndicatorWindow()
    indicator.start()

    # Send a very long string (> 180 chars)
    long_text = "A" * 200
    indicator.update_partial_text(long_text)

    time.sleep(0.2)
    # Should keep only the last few characters with an ellipsis.
    # length should be around 180 (including ellipsis).
    assert len(indicator.partial_text) <= 180
    assert indicator.partial_text.startswith("…")


def test_indicator_visibility_toggle():
    """Test showing and hiding the indicator."""
    indicator = IndicatorWindow()
    indicator.start()

    indicator.show()
    assert indicator.visible is True

    indicator.hide()
    assert indicator.visible is False
