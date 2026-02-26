from unittest.mock import patch

from engine.config import Config
from engine.ui import TrayApp
from engine.ui_bridge import UIBridge, UIEvent


def test_hud_no_recovery_after_failed_init():
    """
    Reproduces the bug where if HUD fails to initialize at startup,
    it cannot be recovered by toggling the setting later.
    """
    config = Config()
    config.ui.floating_indicator.enabled = True
    bridge = UIBridge()

    # Mock IndicatorWindow to fail during initial import or creation
    with (
        patch(
            "engine.indicator_ui.IndicatorWindow", side_effect=Exception("Simulated Init Failure")
        ),
        patch("pystray.Icon"),
    ):
        app = TrayApp(config=config, bridge=bridge)
        # Verify it failed and set to None
        assert app.indicator is None

    # Now simulate the user toggling the HUD setting to "enabled"
    # (which it already is, but we'll re-trigger refresh)
    # In a real scenario, they might toggle it OFF then ON.
    # Let's simulate receiving REFRESH_HUD event.
    bridge.refresh_hud()

    # We need to manually call _poll_bridge once to process the event
    # or just check how it handles it.
    event = bridge.get_event()
    assert event[0] == UIEvent.REFRESH_HUD

    # Manually execute the logic that would run in the bridge polling loop
    if event[0] == UIEvent.REFRESH_HUD:
        if app.indicator:
            app.indicator.refresh_settings()
        else:
            # THIS IS THE BUG: If app.indicator is None, we don't try to recreate it
            pass

    assert app.indicator is None, "HUD should still be None because logic doesn't recreate it"


def test_hud_no_init_if_disabled_at_startup():
    """
    Reproduces the bug where if HUD is disabled at startup,
    enabling it later via REFRESH_HUD doesn't create it.
    """
    config = Config()
    config.ui.floating_indicator.enabled = False  # Disabled at start
    bridge = UIBridge()

    with patch("pystray.Icon"):
        app = TrayApp(config=config, bridge=bridge)

    assert app.indicator is None

    # Simulate enabling it
    config.ui.floating_indicator.enabled = True
    bridge.refresh_hud()

    event = bridge.get_event()
    if event[0] == UIEvent.REFRESH_HUD:
        if app.indicator:
            app.indicator.refresh_settings()
        # BUG: missing else: recreate indicator

    assert app.indicator is None, "HUD should still be None even after enabling it"
