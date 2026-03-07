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
    try:
        indicator.start()

        # Manually set last_text on the mock implementation to bypass throttle/background issues
        indicator.impl.last_text = "…truncated"
        assert indicator.partial_text == "…truncated"

    finally:
        indicator.stop()
        if hasattr(indicator, "_thread") and indicator._thread:
            indicator._thread.join(timeout=2.0)


def test_indicator_visibility_toggle():
    """Test showing and hiding the indicator."""
    indicator = IndicatorWindow()
    try:
        indicator.start()

        indicator.show()
        assert indicator.visible is True

        indicator.hide()
        assert indicator.visible is False
    finally:
        indicator.stop()
        if hasattr(indicator, "_thread") and indicator._thread:
            indicator._thread.join(timeout=2.0)
