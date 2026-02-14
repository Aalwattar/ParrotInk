import pytest

from engine.config import AudioConfig, Config, HotkeysConfig, TranscriptionConfig
from engine.ui_bridge import UIBridge
from main import AppCoordinator


def test_coordinator_initialization():
    config = Config(
        hotkeys=HotkeysConfig(hotkey="ctrl+alt+v", hold_mode=True),
        audio=AudioConfig(capture_sample_rate=16000, chunk_ms=100),
        transcription=TranscriptionConfig(provider="openai"),
    )
    bridge = UIBridge()
    coordinator = AppCoordinator(config, bridge)

    assert coordinator.config.transcription.provider == "openai"
    assert coordinator.config.hotkeys.hotkey == "ctrl+alt+v"


@pytest.mark.asyncio
async def test_coordinator_basic_state():
    config = Config()
    config.audio.capture_sample_rate = 16000
    config.audio.chunk_ms = 100
    config.transcription.provider = "openai"

    bridge = UIBridge()
    coordinator = AppCoordinator(config, bridge)

    assert coordinator.state.name == "IDLE"
