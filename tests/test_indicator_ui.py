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


def test_indicator_partial_text_buffer():
    """Test that the partial text display maintains a short buffer of 3-5 words."""
    indicator = IndicatorWindow()

    # Send 1 word
    indicator.update_partial_text("Hello")
    assert indicator.partial_text == "Hello"

    # Send more than 5 words
    indicator.update_partial_text("one two three four five six seven")
    # Should keep only the last few words.
    # Exact behavior depends on implementation, but let's say last 5 words.
    words = indicator.partial_text.split()
    assert len(words) <= 5
    assert words[-1] == "seven"
    assert words[0] == "three"


def test_indicator_visibility_toggle():
    """Test showing and hiding the indicator."""
    indicator = IndicatorWindow()
    indicator.show()
    assert indicator.visible is True

    indicator.hide()
    assert indicator.visible is False
