import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from engine.app_types import AppState
from engine.config import Config
from main import AppCoordinator


@pytest.fixture
def mock_config():
    config = Config()
    config.audio.capture_sample_rate = 16000
    config.audio.chunk_ms = 30
    config.hotkeys.hotkey = "ctrl+space"
    config.hotkeys.hold_mode = True  # Set to Hold Mode
    config.test.enabled = True
    config.transcription.provider = "openai"
    config.interaction.stop_on_any_key = True
    config.interaction.sounds.enabled = False
    return config


@pytest.mark.asyncio
async def test_hold_mode_interruption_bug(mock_config):
    """
    Test that when hold_mode is True, pressing a random key does NOT stop listening.
    Current behavior (Bug): It STOPS listening.
    Expected behavior (Fix): It ignores the key.
    """
    # Mock AudioStreamer and Monitors to avoid sounddevice/hook init
    with (
        patch("main.AudioStreamer"),
        patch("main.InputMonitor"),
        patch("main.MouseMonitor"),
        patch("main.ConnectionManager") as connection_manager,
        patch("main.UIBridge"),
        patch("main.InjectionController"),
        patch("engine.platform_win.session.SessionMonitor"),
        patch("engine.services.updates.UpdateManager.start"),
        patch("main.AppCoordinator._hook_watchdog_task_run"),
    ):
        connection_manager.return_value.stop_provider = AsyncMock()
        coordinator = AppCoordinator(mock_config)

        # Setup active listening state
        coordinator.stop_listening = AsyncMock()
        coordinator.state = AppState.LISTENING
        coordinator.start_time = time.time() - 10  # Started 10s ago (past cooldown)
        coordinator.last_injection_time = 0
        coordinator.is_injecting = False
        coordinator.injection_lock = MagicMock()
        coordinator.injection_lock.locked.return_value = False
        coordinator._loop = asyncio.get_running_loop()

        # Simulate pressing 'a' (not the hotkey)
        # This simulates the "Stop on Any Key" callback
        coordinator._on_manual_stop(key="a")

        # ASSERT: verify stop_listening was NOT called
        # This should FAIL currently because the bug exists
        coordinator.stop_listening.assert_not_called()
        await coordinator.shutdown()
