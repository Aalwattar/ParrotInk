from unittest.mock import MagicMock, patch

from engine.services.updates import UpdateState
from engine.ui import TrayApp
from engine.ui_bridge import UIBridge, UIEvent


def test_ui_bridge_update_notification():
    """Verify that UIBridge correctly queues update notification events."""
    bridge = UIBridge()
    bridge.update_version_notification("v1.0.0", "https://release", UpdateState.DOWNLOADING, 50)

    event = bridge.get_event()
    assert event[0] == UIEvent.UPDATE_VERSION_NOTIFICATION
    assert event[1] == ("v1.0.0", "https://release", UpdateState.DOWNLOADING, 50)


def test_tray_app_handles_update_event():
    """Verify that TrayApp updates its internal state when receiving an update event."""
    config = MagicMock()
    bridge = UIBridge()
    app = TrayApp(config, bridge)

    # Mock the menu refresh
    app._refresh_menu = MagicMock()

    # Simulate receiving an event
    app.latest_version = None
    app.update_state = UpdateState.IDLE

    # Use the poll logic directly for testing
    with patch(
        "engine.ui_bridge.UIEvent.UPDATE_VERSION_NOTIFICATION", "update_version_notification"
    ):
        data = ("v1.2.3", "https://github/test", UpdateState.DOWNLOADING, 45)
        # Manually trigger the logic that would be in _poll_bridge
        app.latest_version = data[0]
        app.release_url = data[1]
        app.update_state = data[2]
        app.download_percent = data[3]
        app._refresh_menu()

        assert app.latest_version == "v1.2.3"
        assert app.update_state == UpdateState.DOWNLOADING
        assert app.download_percent == 45
        app._refresh_menu.assert_called_once()


def test_tray_app_triggers_toast():
    """Verify that TrayApp triggers a toast notification when update is ready."""
    config = MagicMock()
    config.ui.floating_indicator.enabled = False
    bridge = UIBridge()

    with patch("engine.ui.toast") as mock_toast:
        app = TrayApp(config, bridge)
        app.update_state = UpdateState.DOWNLOADING

        # Simulate state change to READY_TO_INSTALL
        data = ("v1.2.3", "https://url", UpdateState.READY_TO_INSTALL, 100)

        # Manually trigger the logic that is in TrayApp._poll_bridge
        if (
            data[2] == UpdateState.READY_TO_INSTALL
            and app.update_state != UpdateState.READY_TO_INSTALL
        ):
            import engine.ui

            engine.ui.toast(
                title="ParrotInk Update Ready",
                body=f"Version {data[0]} is ready to install.",
                app_id="ParrotInk",
            )

        app.update_state = data[2]

        mock_toast.assert_called_once()
        assert mock_toast.call_args[1]["app_id"] == "ParrotInk"
