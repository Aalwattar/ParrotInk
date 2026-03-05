from unittest.mock import MagicMock, patch

import pytest
from PIL import Image


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.ui.floating_indicator.enabled = False
    return config


@patch("engine.ui.pystray.Icon")
@patch("engine.ui.Image.new")
@patch("engine.ui.ImageDraw.Draw")
def test_icon_fallback_when_assets_missing(mock_draw, mock_new, mock_pystray, mock_config):
    """
    Verify that the UI falls back to dynamic generation when .ico assets are missing.
    """
    from engine.ui import TrayApp

    # Mock Path.exists to return False for all .ico files
    with patch("engine.ui.Path.exists", return_value=False):
        _app = TrayApp(config=mock_config)

        # Initial state is IDLE. _create_icon is called in __init__.
        # It should have called _create_image (which uses Image.new)
        assert mock_new.called


@patch("engine.ui.pystray.Icon")
@patch("engine.ui.Image.open")
def test_icon_loading_when_assets_exist(mock_open, mock_pystray, mock_config):
    """
    Verify that the UI loads .ico assets when they exist.
    """
    from engine.ui import TrayApp

    # Mock Path.exists to return True for tray_idle.ico
    def side_effect(self):
        if str(self).endswith(".ico"):
            return True
        # Need to return True for other things the app might check, like pyproject.toml
        if "pyproject.toml" in str(self):
            return True
        return False

    with patch("engine.ui.Path.exists", side_effect):
        # We also need to mock Image.open to return a mock Image
        mock_img = MagicMock(spec=Image.Image)
        mock_open.return_value = mock_img

        _app = TrayApp(config=mock_config)

        # If implemented correctly, it should have called Image.open
        assert mock_open.called


@patch("engine.ui.pystray.Icon")
@patch("engine.ui.Image.open")
@patch("engine.ui.Image.new")
def test_icon_state_change_updates_asset(mock_new, mock_open, mock_pystray, mock_config):
    """
    Verify that changing state updates the icon to the correct asset.
    """
    from engine.ui import AppState, TrayApp

    def side_effect(self):
        if str(self).endswith(".ico"):
            return True
        if "pyproject.toml" in str(self):
            return True
        return False

    with patch("engine.ui.Path.exists", side_effect):
        mock_img = MagicMock(spec=Image.Image)
        mock_open.return_value = mock_img

        app = TrayApp(config=mock_config)
        mock_open.reset_mock()

        # Change state to LISTENING
        app.set_state(AppState.LISTENING)

        # Should have called Image.open for the listening icon
        assert mock_open.called
