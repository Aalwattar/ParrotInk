from unittest.mock import MagicMock

import pytest

from engine.config import Config, HotkeysConfig, TranscriptionConfig
from main import AppCoordinator


def test_coordinator_initialization():
    config = Config(
        active_provider="openai",
        hotkeys=HotkeysConfig(hotkey="ctrl+alt+v", hold_mode=True),
        transcription=TranscriptionConfig(sample_rate=16000),
    )
    coordinator = AppCoordinator(config)
    assert coordinator.config.hotkeys.hotkey == "ctrl+alt+v"
    assert "ctrl" in coordinator.target_hotkey
    assert "alt" in coordinator.target_hotkey
    assert "v" in coordinator.target_hotkey


@pytest.mark.asyncio
async def test_coordinator_basic_state():
    config = MagicMock(spec=Config)
    # Setup nested mock
    config.transcription = MagicMock(spec=TranscriptionConfig)
    config.transcription.sample_rate = 16000
    config.active_provider = "openai"
    config.hotkeys = MagicMock(spec=HotkeysConfig)
    config.hotkeys.hotkey = "ctrl+alt+v"

    coordinator = AppCoordinator(config)
    assert coordinator.is_listening is False