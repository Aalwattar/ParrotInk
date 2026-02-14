from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

# Global mock for pystray.Icon to prevent Win32 class registration during imports/tests
with patch("pystray.Icon"):
    from engine.app_types import AppState
    from engine.ui import TrayApp


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.ui.floating_indicator.enabled = False
    config.hotkeys.hotkey = "alt+k"
    config.interaction.run_at_startup = False
    return config


def test_get_icon_color(mock_config):
    with patch("engine.ui.pystray.Icon"):
        app = TrayApp(config=mock_config)

        # Fluent colors
        assert app._get_icon_color(AppState.LISTENING) == "#0078D4"  # Microsoft Blue (Vibrant)
        assert app._get_icon_color(AppState.IDLE) == "#475569"  # Slate-600
        assert app._get_icon_color(AppState.ERROR) == "#EF4444"  # Red-500


def test_create_image_size(mock_config):
    with patch("engine.ui.pystray.Icon"):
        app = TrayApp(config=mock_config)
        img = app._create_image("blue")
        assert isinstance(img, Image.Image)
        assert img.size == (64, 64)


def test_create_image_is_rounded_rect(mock_config):
    with patch("engine.ui.pystray.Icon"):
        # Hard to test visual shape, but we can check if it runs without error
        app = TrayApp(config=mock_config)
        img = app._create_image("#0078D4")
        assert img.mode == "RGBA"  # Switched to RGBA for transparency/rounded corners
