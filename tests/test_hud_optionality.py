from unittest.mock import MagicMock, patch


def test_hud_fallback_when_skia_missing():
    """Verify that IndicatorWindow falls back to GDI if Skia/HUD is unavailable."""
    with patch("engine.hud_renderer.HUD_AVAILABLE", False):
        from engine.indicator_ui import GdiFallbackWindow, IndicatorWindow

        indicator = IndicatorWindow()
        assert isinstance(indicator.impl, GdiFallbackWindow)


def test_hud_available_selection():
    """Verify that IndicatorWindow selects HudOverlay when available."""
    with patch("engine.hud_renderer.HUD_AVAILABLE", True):
        # We MUST patch the source used in engine.indicator_ui
        mock_instance = MagicMock()
        mock_instance.update_status = MagicMock()

        with patch("engine.hud_renderer.HudOverlay", return_value=mock_instance):
            from engine.indicator_ui import IndicatorWindow

            indicator = IndicatorWindow()
            assert indicator.impl == mock_instance


def test_on_final_lingers_on_fallback():
    """Verify on_final logic works on fallback implementation."""
    with patch("engine.hud_renderer.HUD_AVAILABLE", False):
        from engine.indicator_ui import IndicatorWindow

        indicator = IndicatorWindow()
        indicator.impl.is_recording = False  # Idle
        with patch.object(indicator, "_start_linger_timer") as mock_linger:
            # on_final should trigger _render_preview
            indicator.on_final("final text", linger_seconds=1.0)

            # Since GdiFallbackWindow HAS update_text, it uses it for the result
            assert indicator.impl.last_text == "final text"

            mock_linger.assert_called_once_with(1.0)
