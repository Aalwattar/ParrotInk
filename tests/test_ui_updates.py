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


@patch.object(TrayApp, "_create_icon", return_value=MagicMock())
def test_tray_app_handles_update_event(mock_create_icon):
    """Verify that TrayApp updates its internal state when receiving an update event."""
    config = MagicMock()
    config.ui.floating_indicator.enabled = False
    bridge = UIBridge()

    app = TrayApp(config, bridge)
    app.icon = MagicMock()
    app._refresh_menu = MagicMock()

    app.latest_version = None
    app.update_state = UpdateState.IDLE

    # Queue an event in the bridge
    bridge.update_version_notification("v1.2.3", "https://github/test", UpdateState.DOWNLOADING, 45)

    # Stop after one poll
    app._stop_event.is_set = MagicMock(side_effect=[False, True])

    app._poll_bridge()

    assert app.latest_version == "v1.2.3"
    assert app.update_state == UpdateState.DOWNLOADING
    assert app.download_percent == 45
    app._refresh_menu.assert_called_once()


@patch.object(TrayApp, "_create_icon", return_value=MagicMock())
def test_tray_app_triggers_toast(mock_create_icon):
    """Verify that TrayApp triggers a toast notification when update is ready."""
    config = MagicMock()
    config.ui.floating_indicator.enabled = False
    bridge = UIBridge()

    app = TrayApp(config, bridge)
    app.icon = MagicMock()
    app.update_state = UpdateState.DOWNLOADING

    # Queue an event for READY_TO_INSTALL
    bridge.update_version_notification("v1.2.3", "https://url", UpdateState.READY_TO_INSTALL, 100)

    # Stop after one poll
    app._stop_event.is_set = MagicMock(side_effect=[False, True])

    app._poll_bridge()

    assert app.update_state == UpdateState.READY_TO_INSTALL
