from unittest.mock import MagicMock, patch

# We need to ensure we can test the fallback even if Skia is actually installed.
# We'll mock the import in engine.indicator_ui


def test_hud_fallback_when_skia_missing():
    """Verify that IndicatorWindow falls back to GDI if Skia/HUD is unavailable."""

    # Force HUD_AVAILABLE to False as if imports failed
    with patch("engine.indicator_ui.HUD_AVAILABLE", False):
        from engine.indicator_ui import GdiFallbackWindow, IndicatorWindow

        indicator = IndicatorWindow()

        # Check that the implementation is indeed the fallback
        assert isinstance(indicator.impl, GdiFallbackWindow)

        # Verify basic methods don't crash
        indicator.update_status(True)
        assert indicator.impl.is_recording is True

        indicator.update_partial_text("test")
        assert indicator.impl.partial_text == "test"

        # Should not raise any errors when starting/stopping
        with patch.object(GdiFallbackWindow, "start") as mock_start:
            indicator.start()
            mock_start.assert_called_once()

        with patch.object(GdiFallbackWindow, "stop") as mock_stop:
            indicator.stop()
            mock_stop.assert_called_once()


def test_hud_available_selection():
    """Verify that IndicatorWindow selects HudOverlay when available."""

    with patch("engine.indicator_ui.HUD_AVAILABLE", True):
        # We need to mock HudOverlay since it might fail to init without real Win32 environment
        mock_hud_overlay_cls = MagicMock()
        with patch("engine.indicator_ui.HudOverlay", mock_hud_overlay_cls):
            from engine.indicator_ui import IndicatorWindow

            indicator = IndicatorWindow()
            mock_hud_overlay_cls.assert_called_once()
            assert indicator.impl == mock_hud_overlay_cls.return_value


def test_on_final_lingers_on_fallback():
    """Verify on_final logic works on fallback implementation."""
    with patch("engine.indicator_ui.HUD_AVAILABLE", False):
        from engine.indicator_ui import IndicatorWindow

        indicator = IndicatorWindow()
        indicator.impl.is_recording = False  # Idle

        with patch.object(indicator, "_start_linger_timer") as mock_linger:
            # Set initial text
            indicator.update_partial_text("preview")
            
            # on_final should NOT overwrite the preview with "final text"
            # It should trigger the flash logic instead
            indicator.on_final("final text", linger_seconds=1.0)

            # Assert text is UNCHANGED (or cleared if implementation decided to, but definitely not "final text")
            assert indicator.impl.partial_text == "preview"
            mock_linger.assert_called_once_with(1.0)
