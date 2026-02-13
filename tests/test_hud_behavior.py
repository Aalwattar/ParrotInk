import time
from unittest.mock import MagicMock

from engine.indicator_ui import IndicatorWindow


def test_hud_flash_behavior():
    """Test that on_final triggers a flash and does NOT update partial text."""
    indicator = IndicatorWindow()
    # Mock the implementation
    indicator.impl = MagicMock()
    indicator.impl.is_recording = True

    # Send partial
    indicator.update_partial_text("Hello world")
    # First update should pass (if throttle allows)
    # We might need to sleep to clear throttle if initialized recently
    time.sleep(0.1)
    indicator.update_partial_text("Hello world")

    # Check if update_text/update_partial_text was called
    assert indicator.impl.update_partial_text.called or indicator.impl.update_text.called

    # Reset mock
    indicator.impl.reset_mock()

    # Trigger Final
    indicator.on_final("Hello world final")

    # Verify:
    # 1. update_status_icon("finalized") called
    # 2. update_partial_text("Hello world final") NOT called

    indicator.impl.update_status_icon.assert_called_with("finalized")

    # Ensure text was NOT updated with the final string
    for call in indicator.impl.mock_calls:
        name = call[0]
        args = call[1]
        if name in ["update_partial_text", "update_text"]:
            assert "Hello world final" not in args


def test_hud_throttling():
    """Test that rapid updates are throttled."""
    indicator = IndicatorWindow()
    indicator.impl = MagicMock()

    # Reset throttle timer
    indicator._last_redraw_at = 0

    # First call: Should pass
    indicator.update_partial_text("A")
    assert (
        indicator.impl.update_partial_text.call_count == 1
        or indicator.impl.update_text.call_count == 1
    )

    # Immediate second call: Should be dropped
    indicator.update_partial_text("B")
    # Count should still be 1 (assuming impl methods match)
    # Let's check calls more generally
    call_count = (
        indicator.impl.update_partial_text.call_count + indicator.impl.update_text.call_count
    )
    assert call_count == 1

    # Wait 60ms (>50ms throttle)
    time.sleep(0.06)

    # Third call: Should pass
    indicator.update_partial_text("C")
    call_count = (
        indicator.impl.update_partial_text.call_count + indicator.impl.update_text.call_count
    )
    assert call_count == 2
