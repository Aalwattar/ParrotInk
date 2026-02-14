import pytest
from unittest.mock import MagicMock
from engine.ui import TrayApp
from engine.app_types import AppState
from PIL import Image

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.ui.floating_indicator.enabled = False
    config.hotkeys.hotkey = "alt+k"
    config.interaction.run_at_startup = False
    return config

def test_get_icon_color(mock_config):
    app = TrayApp(config=mock_config)
    
    # Fluent colors
    assert app._get_icon_color(AppState.LISTENING) == "#0078D4" # Microsoft Blue (as planned)
    assert app._get_icon_color(AppState.IDLE) == "#475569"      # Slate-600
    assert app._get_icon_color(AppState.ERROR) == "#EF4444"     # Red-500

def test_create_image_size(mock_config):
    app = TrayApp(config=mock_config)
    img = app._create_image("blue")
    assert isinstance(img, Image.Image)
    assert img.size == (64, 64)

def test_create_image_is_rounded_rect(mock_config):
    # Hard to test visual shape, but we can check if it runs without error
    app = TrayApp(config=mock_config)
    img = app._create_image("#0078D4")
    assert img.mode == "RGBA" # Switched to RGBA for transparency/rounded corners
