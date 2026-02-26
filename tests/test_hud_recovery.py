from unittest.mock import MagicMock, patch

from engine.config import Config
from engine.ui import TrayApp
from engine.ui_bridge import UIBridge, UIEvent


def test_hud_recovery_after_failed_init():
    """
    Verifies that if HUD fails to initialize at startup,
    it CAN be recovered by a refresh event (or on-demand).
    """
    config = Config()
    config.ui.floating_indicator.enabled = True
    bridge = UIBridge()

    # First call to IndicatorWindow fails
    with (
        patch(
            "engine.indicator_ui.IndicatorWindow",
            side_effect=[Exception("Simulated Init Failure"), MagicMock()],
        ),
        patch("pystray.Icon"),
    ):
        app = TrayApp(config=config, bridge=bridge)
        # Verify it failed and set to None
        assert app.indicator is None

        # Now simulate a REFRESH_HUD event which should trigger _ensure_indicator()
        bridge.refresh_hud()
        event = bridge.get_event()
        assert event[0] == UIEvent.REFRESH_HUD

        # Manually process the event like _poll_bridge would
        if event[0] == UIEvent.REFRESH_HUD:
            app._ensure_indicator()

        # Now it should be initialized (since we provided a second success mock)
        assert app.indicator is not None, "HUD should have recovered via _ensure_indicator()"


def test_hud_lazy_init_when_enabled_later():
    """
    Verifies that if HUD is disabled at startup,
    enabling it later via REFRESH_HUD creates it.
    """
    config = Config()
    config.ui.floating_indicator.enabled = False  # Disabled at start
    bridge = UIBridge()

    with patch("engine.indicator_ui.IndicatorWindow") as mock_indicator, patch("pystray.Icon"):
        app = TrayApp(config=config, bridge=bridge)
        assert app.indicator is None

        # Simulate enabling it in config
        config.ui.floating_indicator.enabled = True
        bridge.refresh_hud()

        event = bridge.get_event()
        if event[0] == UIEvent.REFRESH_HUD:
            app._ensure_indicator()

        assert app.indicator is not None, "HUD should have been created lazily when enabled"
        mock_indicator.assert_called_once()
