import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from engine.app_types import AppState
from engine.config import Config
from engine.config_resolver import resolve_effective_config
from engine.mouse import MouseMonitor
from engine.transcription.assemblyai_provider import AssemblyAIProvider


def test_short_click_between_samples_is_not_lost(mocker):
    callback = MagicMock()
    monitor = MouseMonitor(callback)
    monitor._stop_event = MagicMock()
    monitor._stop_event.is_set.return_value = False
    monitor._stop_event.wait.side_effect = [False, False, True]
    # The button is released at both samples; the short click changes foreground.
    mocker.patch("engine.mouse._read_button", return_value=False)
    mocker.patch("engine.mouse._read_position", return_value=(100, 200))
    mocker.patch("engine.mouse._read_foreground", side_effect=[10, 10, 20], create=True)
    monitor._poll()
    callback.assert_called_once_with(100, 200)


@pytest.mark.asyncio
async def test_assemblyai_tail_silence_does_not_fail_completed_recording():
    cfg = Config()
    cfg.audio.provider_stop_timeout_seconds = 0.1
    provider = AssemblyAIProvider(
        "", MagicMock(), MagicMock(), resolve_effective_config(cfg).assemblyai
    )
    provider.ws = AsyncMock()
    provider._is_running = True
    await provider._handle_event(
        {
            "type": "Turn",
            "turn_order": 0,
            "transcript": "test phrase",
            "end_of_turn": True,
            "turn_is_formatted": True,
        }
    )
    # Capture continues after the server's final turn, sending only silence.
    await provider.notify_voice_activity(False, 1.0)
    await provider.send_audio(bytes(3200), 1.0)
    await provider.finish_utterance()
    assert provider.is_running
    provider.ws.send.assert_awaited_once_with(bytes(3200))


@pytest.mark.asyncio
async def test_click_away_blocks_late_final_text_immediately(coordinator):
    coordinator._loop = asyncio.get_running_loop()
    coordinator.state = AppState.LISTENING
    coordinator.anchor = MagicMock()
    coordinator.anchor.is_match.return_value = False
    coordinator.config.hotkeys.hold_mode = False
    coordinator.config.interaction.cancel_on_click_outside_anchor = True
    coordinator.stop_listening = AsyncMock()
    coordinator._queue_injection = MagicMock()
    coordinator._on_mouse_click(100, 200)
    coordinator.on_final("late phrase")
    await asyncio.sleep(0)
    assert coordinator.session_cancelled
    coordinator._queue_injection.assert_not_called()
