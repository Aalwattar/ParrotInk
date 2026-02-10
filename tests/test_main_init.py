from unittest.mock import MagicMock
import pytest
from engine.config import Config, HotkeysConfig, TranscriptionConfig, AudioConfig, AppTestConfig
from main import AppCoordinator

def test_coordinator_initialization():
    config = Config(
        default_provider="openai",
        hotkeys=HotkeysConfig(hotkey="ctrl+alt+v", hold_mode=True),
        audio=AudioConfig(capture_sample_rate=16000, chunk_ms=100),
        transcription=TranscriptionConfig(sample_rate=16000),
    )
    coordinator = AppCoordinator(config)
    assert coordinator.config.hotkeys.hotkey == "ctrl+alt+v"
    assert "ctrl" in coordinator.target_hotkey
    assert "alt" in coordinator.target_hotkey
    assert "v" in coordinator.target_hotkey

@pytest.mark.asyncio
async def test_coordinator_basic_state():
    config = Config()
    config.audio.capture_sample_rate = 16000
    config.audio.chunk_ms = 100
    config.default_provider = "openai"
    config.hotkeys.hotkey = "ctrl+alt+v"

    coordinator = AppCoordinator(config)
    assert coordinator.is_listening is False
