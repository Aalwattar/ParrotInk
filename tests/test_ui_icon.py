from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.ui.floating_indicator.enabled = False
    config.hotkeys.hotkey = "alt+k"
    config.interaction.run_at_startup = False
    return config


def test_get_icon_color(mock_config):
    # Patch pystray BEFORE importing TrayApp inside the test to ensure the mock is used
    with patch("pystray.Icon"), patch("pystray.Menu"), patch("pystray.MenuItem"):
        from engine.app_types import AppState
        from engine.ui import TrayApp

        app = TrayApp(config=mock_config)

        # Fluent colors
        assert app._get_icon_color(AppState.LISTENING) == "#0078D4"
        assert app._get_icon_color(AppState.IDLE) == "#475569"
        assert app._get_icon_color(AppState.ERROR) == "#EF4444"


def test_create_image_size(mock_config):
    with patch("pystray.Icon"), patch("pystray.Menu"), patch("pystray.MenuItem"):
        from PIL import Image

        from engine.ui import TrayApp

        app = TrayApp(config=mock_config)
        img = app._create_image("blue")
        assert isinstance(img, Image.Image)
        assert img.size == (64, 64)


def test_create_image_is_rounded_rect(mock_config):
    with patch("pystray.Icon"), patch("pystray.Menu"), patch("pystray.MenuItem"):
        from engine.ui import TrayApp

        app = TrayApp(config=mock_config)
        img = app._create_image("#0078D4")
        assert img.mode == "RGBA"
