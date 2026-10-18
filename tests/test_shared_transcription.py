import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from engine.app_types import AppState
from engine.audio.pipeline import AudioPipeline
from engine.transcription.base import BaseProvider


class ReadyProvider(BaseProvider):
    def __init__(self):
        super().__init__("", lambda text: None, lambda text: None, "ws://localhost")
        self.running = True

    @property
    def is_running(self):
        return self.running

    def get_type(self):
        return "test"

    def get_audio_spec(self):
        return None

    async def start(self):
        pass

    async def _do_stop(self):
        self.running = False

    async def send_audio(self, processed_chunk, capture_time):
        pass


@pytest.mark.asyncio
async def test_readiness_timeout_is_failure():
    with pytest.raises(TimeoutError):
        await ReadyProvider().wait_for_ready(timeout=0.01)


@pytest.mark.asyncio
async def test_failure_wakes_readiness_wait_without_waiting_for_timeout():
    provider = ReadyProvider()
    provider.running = False
    provider._failure_event.set()
    with pytest.raises(ConnectionError):
        await asyncio.wait_for(provider.wait_for_ready(timeout=30), timeout=0.1)


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["openai", "assemblyai"])
async def test_api_rejection_wakes_readiness_and_blocks_late_transcripts(name):
    from engine.config import Config
    from engine.config_resolver import resolve_effective_config
    from engine.transcription.assemblyai_provider import AssemblyAIProvider
    from engine.transcription.openai_provider import OpenAIProvider

    effective = resolve_effective_config(Config())
    finals = []
    cls = OpenAIProvider if name == "openai" else AssemblyAIProvider
    provider = cls("", lambda text: None, finals.append, getattr(effective, name))
    provider._is_running = True
    error = {"type": "error", "error": {"code": "invalid_api_key"}}
    await provider._handle_event(error)
    with pytest.raises(ConnectionError):
        await asyncio.wait_for(provider.wait_for_ready(timeout=30), timeout=0.1)
    await provider._handle_event(
        {
            "type": "Turn" if name == "assemblyai" else "input_audio_transcription.completed",
            "transcript": "Late text",
            "end_of_turn": True,
        }
    )
    assert not finals


@pytest.mark.asyncio
async def test_pipeline_reports_stopped_after_provider_failure():
    async def chunks():
        yield np.zeros(1600, dtype=np.float32), 1.0

    streamer = SimpleNamespace(async_generator=chunks, last_status=None)
    pipeline = AudioPipeline(streamer)
    pipeline._is_running = True
    calls = []

    async def vad(active, timestamp):
        calls.append("vad")

    async def send(chunk, timestamp):
        calls.append("audio")

    provider = SimpleNamespace(
        notify_voice_activity=vad, send_audio=send, is_running=False, get_type=lambda: "test"
    )
    adapter = SimpleNamespace(process=lambda chunk: b"pcm", voice_active=False)
    await pipeline._run_pipe(adapter, provider)
    assert calls == ["vad", "audio"]
    assert not pipeline.is_active


@pytest.mark.asyncio
async def test_manual_stop_finishes_before_closing_warm_connection(coordinator):
    coordinator._loop = asyncio.get_running_loop()
    coordinator.config.audio.connection_mode = "warm"
    coordinator.connection_manager.start_idle_timer = MagicMock()
    coordinator.state = AppState.LISTENING
    calls = []

    async def stop_capture():
        calls.append("capture")

    async def finish():
        calls.append("finish")

    coordinator.pipeline.stop = stop_capture
    provider = MagicMock(is_running=True)
    provider.finish_utterance = finish
    provider.stop = AsyncMock()
    coordinator.connection_manager.provider = provider
    await asyncio.gather(coordinator.stop_listening(), coordinator.stop_listening())
    assert calls == ["capture", "finish"]
    assert coordinator.state == AppState.IDLE
    provider.stop.assert_not_called()


@pytest.mark.asyncio
async def test_unrelated_ui_setting_does_not_reset_provider(coordinator, tmp_path):
    coordinator._loop = asyncio.get_running_loop()
    coordinator.connection_manager.stop_provider = AsyncMock()
    coordinator.config.update_and_save(
        {"ui": {"floating_indicator": {"opacity_idle": 0.4}}},
        path=tmp_path / "config.toml",
        blocking=True,
    )
    await asyncio.sleep(0)
    assert coordinator._configuration_future is None
    coordinator.connection_manager.stop_provider.assert_not_called()


@pytest.mark.asyncio
async def test_finalization_failure_closes_session_and_preserves_error(coordinator):
    coordinator._loop = asyncio.get_running_loop()
    coordinator.config.audio.connection_mode = "on_demand"
    coordinator.state = AppState.LISTENING
    coordinator.pipeline.stop = AsyncMock()
    provider = MagicMock(is_running=True)
    provider.finish_utterance = AsyncMock(side_effect=TimeoutError)
    provider.stop = AsyncMock()
    coordinator.connection_manager.provider = provider
    await coordinator.stop_listening()
    assert coordinator.state == AppState.ERROR
    assert coordinator.session_cancelled
    assert coordinator.connection_manager.provider is None
    provider.stop.assert_awaited_once()


@pytest.mark.parametrize(
    "click_away,hold_mode,expected",
    [(True, False, True), (False, False, False), (True, True, False)],
)
def test_mouse_observation_runs_only_when_needed(coordinator, click_away, hold_mode, expected):
    coordinator.config.interaction.cancel_on_click_outside_anchor = click_away
    coordinator.config.hotkeys.hold_mode = hold_mode
    coordinator.mouse_monitor.start = MagicMock()
    coordinator._start_mouse_monitor()
    assert coordinator.mouse_monitor.start.called is expected


@pytest.mark.asyncio
async def test_terminal_transcription_session_is_detached_in_warm_mode(coordinator):
    coordinator._loop = asyncio.get_running_loop()
    coordinator.config.audio.connection_mode = "warm"
    coordinator.state = AppState.LISTENING
    coordinator.pipeline.stop = AsyncMock()
    provider = MagicMock(is_running=True)

    async def finish():
        provider.is_running = False

    provider.finish_utterance = finish
    provider.stop = AsyncMock()
    coordinator.connection_manager.provider = provider
    await coordinator.stop_listening()
    assert coordinator.connection_manager.provider is None
    provider.stop.assert_awaited_once()
    assert coordinator.state == AppState.IDLE


@pytest.mark.asyncio
async def test_old_cloudflare_openai_config_reports_unavailable_before_connecting(coordinator):
    coordinator.config.transcription.provider = "cloudflare"
    coordinator.config.providers.cloudflare.core.account_id = "a" * 32
    coordinator.config.providers.cloudflare.core.model = "openai/gpt-live-transcribe"
    coordinator.state = AppState.IDLE
    coordinator.connection_manager.ensure_connected = AsyncMock()
    await coordinator.start_listening()
    coordinator.connection_manager.ensure_connected.assert_not_awaited()
    coordinator.ui_bridge.update_status_message.assert_any_call("Model unavailable in Cloudflare")
    assert coordinator.config.providers.cloudflare.core.model == "openai/gpt-live-transcribe"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "decision,message",
    [
        ("not_editable", "Click an editable text field"),
        ("unknown", "Cannot verify this field; click an editable text field"),
    ],
)
async def test_noneditable_target_rejects_dictation_before_network_or_microphone(
    coordinator, mocker, decision, message
):
    coordinator.config.test.enabled = False
    coordinator.config.transcription.provider = "openai"
    coordinator.get_provider_availability = MagicMock(return_value={"openai": True})
    coordinator.state = AppState.IDLE
    coordinator.input_monitor._state = 1
    coordinator.connection_manager.ensure_connected = AsyncMock()
    coordinator.pipeline.start = AsyncMock()
    mocker.patch(
        "main.Anchor.capture_current",
        return_value=SimpleNamespace(
            can_dictate=False,
            focused_element=None,
            assessment=SimpleNamespace(decision=decision, reason="test_reason"),
        ),
    )
    await coordinator.start_listening()
    coordinator.connection_manager.ensure_connected.assert_not_awaited()
    coordinator.pipeline.start.assert_not_awaited()
    assert coordinator.input_monitor._state == 0
    assert coordinator.session_cancelled
    assert coordinator.state == AppState.IDLE
    coordinator.ui_bridge.update_status_message.assert_any_call(message)


@pytest.mark.asyncio
async def test_writable_target_still_starts_dictation(coordinator, mocker):
    coordinator.config.test.enabled = False
    coordinator.config.transcription.provider = "openai"
    coordinator.config.interaction.sounds.enabled = False
    coordinator.get_provider_availability = MagicMock(return_value={"openai": True})
    coordinator.state = AppState.IDLE
    coordinator._loop = asyncio.get_running_loop()
    coordinator.connection_manager.ensure_connected = AsyncMock()
    coordinator.connection_manager.provider = ReadyProvider()
    coordinator.pipeline.start = AsyncMock()
    coordinator.pipeline.stop = AsyncMock()
    mocker.patch.object(coordinator, "_start_mouse_monitor")
    target = SimpleNamespace(can_dictate=True, has_focus=lambda: True)
    mocker.patch("main.Anchor.capture_current", return_value=target)
    await coordinator.start_listening()
    coordinator.connection_manager.ensure_connected.assert_awaited_once()
    coordinator.pipeline.start.assert_awaited_once()
    assert coordinator.state == AppState.LISTENING
    await coordinator.stop_listening()


@pytest.mark.asyncio
async def test_target_changed_during_connection_does_not_start_microphone(coordinator, mocker):
    coordinator.state = AppState.IDLE
    coordinator.connection_manager.ensure_connected = AsyncMock()
    coordinator.connection_manager.provider = ReadyProvider()
    coordinator.pipeline.start = AsyncMock()
    target = SimpleNamespace(can_dictate=True, has_focus=lambda: False)
    mocker.patch("main.Anchor.capture_current", return_value=target)
    await coordinator.start_listening()
    coordinator.pipeline.start.assert_not_awaited()
    assert coordinator.state == AppState.IDLE
    assert coordinator.session_cancelled
