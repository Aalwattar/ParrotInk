import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from engine.app_types import AppState
from main import AppCoordinator


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.hotkeys.hotkey = "ctrl+space"
    config.hotkeys.hold_mode = False
    config.audio.inactivity_timeout_seconds = 30
    config.audio.connection_timeout_seconds = 10
    config.transcription.provider = "openai"
    config.interaction.sounds.enabled = False
    config.interaction.cancel_on_click_outside_anchor = False
    config.test.enabled = True
    return config


@pytest.mark.asyncio
async def test_stats_integration_emits_on_stop(mock_config):
    """Verify that stop_listening triggers a RECORD_STATS event via the bridge."""
    bridge = MagicMock()

    # We need to mock the objects that are awaited
    mock_pipeline = MagicMock()
    mock_pipeline.stop = AsyncMock()

    mock_conn = MagicMock()
    mock_conn.ensure_connected = AsyncMock()
    mock_conn.stop_provider = AsyncMock()

    with (
        patch("main.AudioPipeline", return_value=mock_pipeline),
        patch("main.ConnectionManager", return_value=mock_conn),
        patch("main.InputMonitor"),
        patch("main.MouseMonitor"),
        patch("main.InjectionController"),
    ):
        coordinator = AppCoordinator(mock_config, bridge)
        coordinator.set_state(AppState.LISTENING)
        coordinator.session_start_time = time.time() - 5.0  # 5 seconds ago
        coordinator.session_word_count = 10

        await coordinator.stop_listening()

        # Check if record_stats was called on the bridge
        bridge.record_stats.assert_called_once()
        args = bridge.record_stats.call_args[1]
        assert args["duration"] >= 5.0
        assert args["words"] == 10
        assert args["provider"] == "openai"
        assert args["error"] is False


@pytest.mark.asyncio
async def test_stats_word_counting(mock_config):
    """Verify that on_final increments the word count."""
    bridge = MagicMock()
    with (
        patch("main.AudioPipeline"),
        patch("main.ConnectionManager"),
        patch("main.InputMonitor"),
        patch("main.MouseMonitor"),
        patch("main.InjectionController"),
    ):
        coordinator = AppCoordinator(mock_config, bridge)
        coordinator.session_word_count = 0

        coordinator.on_final("Hello world")
        assert coordinator.session_word_count == 2

        coordinator.on_final("This is a test.")
        assert coordinator.session_word_count == 6  # 2 + 4
