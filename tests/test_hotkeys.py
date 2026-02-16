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


def test_hotkey_assignment():
    coordinator = setup_coordinator()
    # In the new architecture, InputMonitor holds the hotkey
    assert coordinator.input_monitor._hotkey_str == "ctrl+alt+v"
    assert coordinator.input_monitor._hold_mode is True


def test_hotkey_update_on_config_change():
    coordinator = setup_coordinator()
    new_config = coordinator.config
    new_config.hotkeys.hotkey = "ctrl+space"
    new_config.hotkeys.hold_mode = False

    coordinator._on_config_changed(new_config)

    assert coordinator.input_monitor._hotkey_str == "ctrl+space"
    assert coordinator.input_monitor._hold_mode is False


def test_hold_mode_logic():
    coordinator = setup_coordinator(hold_mode=True)
    assert coordinator.config.hotkeys.hold_mode is True


def test_toggle_mode_logic():
    coordinator = setup_coordinator(hold_mode=False)
    assert coordinator.config.hotkeys.hold_mode is False
