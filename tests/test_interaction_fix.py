import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from engine.config import Config
from main import AppCoordinator


@pytest.fixture
def mock_config():
    config = MagicMock(spec=Config)
    config.audio = MagicMock()
    config.audio.capture_sample_rate = 16000
    config.audio.chunk_ms = 30
    config.hotkeys = MagicMock()
    config.hotkeys.hotkey = "ctrl+space"
    config.hotkeys.hold_mode = True  # Set to Hold Mode
    config.test = MagicMock()
    config.test.enabled = True
    config.default_provider = "openai"
    return config


def test_hold_mode_interruption_bug(mock_config):
    """
    Test that when hold_mode is True, pressing a random key does NOT stop listening.
    Current behavior (Bug): It STOPS listening.
    Expected behavior (Fix): It ignores the key.
    """
    # Mock AudioStreamer to avoid sounddevice init
    with patch("main.AudioStreamer"):
        coordinator = AppCoordinator(mock_config)

        # Setup active listening state
        coordinator.stop_listening = AsyncMock()
        coordinator.is_listening = True
        coordinator.is_connecting = False
        coordinator.start_time = time.time() - 10  # Started 10s ago (past cooldown)
        coordinator.last_injection_time = 0
        coordinator.is_injecting = False
        coordinator.injection_lock = MagicMock()
        coordinator.injection_lock.locked.return_value = False
        coordinator.loop = MagicMock()  # Mock the loop

        # Simulate pressing 'a' (not the hotkey)
        # This simulates the "Stop on Any Key" callback
        coordinator._on_manual_stop(key="a")

        # ASSERT: verify stop_listening was NOT called
        # This should FAIL currently because the bug exists
        coordinator.stop_listening.assert_not_called()
