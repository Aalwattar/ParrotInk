from unittest.mock import MagicMock, patch

import pytest

from engine.config import load_config
from engine.ui import TrayApp
from engine.ui_bridge import UIEvent


@pytest.fixture
def mock_config():
    return load_config()


def test_tray_app_receives_version_notification(mock_config):
    bridge = MagicMock()
    # Mock bridge to return one event then nothing
    bridge.get_event.side_effect = [
        (UIEvent.UPDATE_VERSION_NOTIFICATION, ("v1.2.3", "http://test")),
        None,
    ]

    with patch("pystray.Icon"):
        app = TrayApp(mock_config, bridge)
        # We don't want to start the actual icon/ui mainloops
        app.icon = MagicMock()

        # We need a way to stop the loop after one iteration without preventing it from starting
        # We can mock stop_event.is_set to return False once, then True
        app._stop_event.is_set = MagicMock(side_effect=[False, True])

        app._poll_bridge()

        assert app.latest_version == "v1.2.3"
        assert app.release_url == "http://test"


@patch("webbrowser.open")
def test_on_update_clicked_opens_browser(mock_browser_open, mock_config):
    with patch("pystray.Icon"):
        app = TrayApp(mock_config)
        app.release_url = "http://release"

        app._on_update_clicked(None, None)

        mock_browser_open.assert_called_once_with("http://release")


def test_create_menu_with_update(mock_config):
    with patch("pystray.Icon"):
        app = TrayApp(mock_config)
        app.latest_version = "v1.2.3"
        app.release_url = "http://release"

        menu = app._create_menu()
        # First item should be the version label
        version_item = menu.items[0]

        assert "Update Available: v1.2.3" in version_item.text
        assert version_item.enabled is True
