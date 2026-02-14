from unittest.mock import MagicMock, patch

import pytest

from engine.ui import TrayApp


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.ui.floating_indicator.enabled = False
    config.hotkeys.hotkey = "alt+k"
    config.hotkeys.hold_mode = False
    config.interaction.run_at_startup = False
    config.interaction.sounds.enabled = True
    config.transcription.provider = "openai"
    return config


def test_on_toggle_hold_mode_callback(mock_config):
    mock_cb = MagicMock()
    app = TrayApp(config=mock_config, on_toggle_hold_mode=mock_cb)

    # Simulate clicking the menu item
    # Note: _on_toggle_hold_mode_clicked toggles the CURRENT value from config
    app._on_toggle_hold_mode_clicked(None, None)

    # If hold_mode was False, it should call callback with True
    mock_cb.assert_called_once_with(True)


def test_version_header_content(mock_config):
    with patch("engine.ui.get_app_version", return_value="1.2.3"):
        # Re-import or ensure we are patching where it's USED
        from engine.ui import TrayApp

        app = TrayApp(config=mock_config)
        menu_items = list(app.icon.menu)
        assert menu_items[0].text == "Voice2Text v1.2.3"
