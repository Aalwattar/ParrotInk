from engine.config import Config, HotkeysConfig, TranscriptionConfig
from engine.ui_bridge import UIBridge
from main import AppCoordinator


def setup_coordinator(hold_mode=True):
    config = Config(
        hotkeys=HotkeysConfig(hotkey="ctrl+alt+v", hold_mode=hold_mode),
        transcription=TranscriptionConfig(provider="openai"),
    )
    bridge = UIBridge()
    coordinator = AppCoordinator(config, bridge)
    return coordinator


def test_hotkey_parsing():
    coordinator = setup_coordinator()
    # Normalize hotkey for keyboard library
    assert coordinator.target_hotkey == {"ctrl", "alt", "v"}


def test_key_normalization():
    coordinator = setup_coordinator()
    # keyboard uses lowercase
    assert coordinator.target_hotkey == {"ctrl", "alt", "v"}


def test_hold_mode_logic():
    coordinator = setup_coordinator(hold_mode=True)
    assert coordinator.config.hotkeys.hold_mode is True


def test_toggle_mode_logic():
    coordinator = setup_coordinator(hold_mode=False)
    assert coordinator.config.hotkeys.hold_mode is False
