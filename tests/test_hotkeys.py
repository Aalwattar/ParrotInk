from unittest.mock import MagicMock, patch
from pynput import keyboard
from engine.config import Config, HotkeysConfig, TranscriptionConfig
from main import AppCoordinator


def setup_coordinator(hold_mode=True):
    config = Config(
        default_provider="openai",
        hotkeys=HotkeysConfig(hotkey="ctrl+alt+v", hold_mode=hold_mode),
        transcription=TranscriptionConfig(sample_rate=16000),
    )
    coordinator = AppCoordinator(config)
    coordinator.loop = MagicMock()
    return coordinator


def test_hotkey_parsing():
    coordinator = setup_coordinator()
    assert coordinator.target_hotkey == {"ctrl", "alt", "v"}


def test_key_normalization():
    coordinator = setup_coordinator()
    assert coordinator._get_canonical_name(keyboard.Key.ctrl_l) == "ctrl"
    assert coordinator._get_canonical_name(keyboard.Key.ctrl_r) == "ctrl"
    assert coordinator._get_canonical_name(keyboard.Key.alt_l) == "alt"
    assert coordinator._get_canonical_name(keyboard.KeyCode.from_char("V")) == "v"


def test_hold_mode_logic():
    coordinator = setup_coordinator(hold_mode=True)
    with patch("asyncio.run_coroutine_threadsafe") as mock_run:
        # Press Ctrl
        coordinator.on_press(keyboard.Key.ctrl_l)
        assert "ctrl" in coordinator.current_keys
        assert not coordinator.hotkey_pressed

        # Press Alt
        coordinator.on_press(keyboard.Key.alt_l)
        assert "alt" in coordinator.current_keys

        # Press V
        coordinator.on_press(keyboard.KeyCode.from_char("v"))
        assert coordinator.hotkey_pressed
        assert mock_run.called

        mock_run.reset_mock()
        # Release V
        coordinator.on_release(keyboard.KeyCode.from_char("v"))
        assert not coordinator.hotkey_pressed
        assert mock_run.called  # stop_listening should be called


def test_toggle_mode_logic():
    coordinator = setup_coordinator(hold_mode=False)
    with patch("asyncio.run_coroutine_threadsafe") as mock_run:
        # Full press
        coordinator.on_press(keyboard.Key.ctrl_l)
        coordinator.on_press(keyboard.Key.alt_l)
        coordinator.on_press(keyboard.KeyCode.from_char("v"))

        assert coordinator.hotkey_pressed
        assert mock_run.call_count == 1  # start_listening

        # Release should reset hotkey_pressed but NOT call stop_listening
        mock_run.reset_mock()
        coordinator.on_release(keyboard.KeyCode.from_char("v"))
        assert not coordinator.hotkey_pressed
        assert mock_run.call_count == 0

        # Press again to toggle off
        coordinator.on_press(keyboard.KeyCode.from_char("v"))
        assert coordinator.hotkey_pressed
        assert mock_run.call_count == 1  # stop_listening