from unittest.mock import MagicMock, patch


def test_hud_fallback_when_skia_missing():
    """Verify that IndicatorWindow falls back to GDI if Skia/HUD is unavailable."""
    with patch("engine.indicator_ui.HUD_AVAILABLE", False):
        from engine.indicator_ui import GdiFallbackWindow, IndicatorWindow

        indicator = IndicatorWindow()
        assert isinstance(indicator.impl, GdiFallbackWindow)
        indicator.update_status(True)
        assert indicator.impl.is_recording is True
        indicator.update_partial_text("test")
        assert indicator.impl.partial_text == "test"
        with patch.object(GdiFallbackWindow, "start") as mock_start:
            indicator.start()
            mock_start.assert_called_once()
        with patch.object(GdiFallbackWindow, "stop") as mock_stop:
            indicator.stop()
            mock_stop.assert_called_once()


def test_hud_available_selection():
    """Verify that IndicatorWindow selects HudOverlay when available."""
    with patch("engine.indicator_ui.HUD_AVAILABLE", True):
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
            # on_final should include the text in the rolling preview history
            indicator.on_final("final text", linger_seconds=1.0)
            # In the new design, on_final appends to _committed_text and renders it.
            assert indicator.impl.partial_text == "final text"
            mock_linger.assert_called_once_with(1.0)
