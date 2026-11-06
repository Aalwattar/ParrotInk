import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from engine.app_types import AppState, AudioHardwareError, EffectiveCloudflareConfig
from engine.config import Config
from engine.config_resolver import resolve_effective_config
from engine.injection import InjectionController
from engine.mouse import MouseMonitor
from engine.transcription.assemblyai_provider import AssemblyAIProvider
from engine.transcription.cloudflare_provider import CloudflareProvider


@pytest.mark.asyncio
async def test_completed_cloudflare_recording_does_not_show_finalization_failure(coordinator):
    coordinator._loop = asyncio.get_running_loop()
    coordinator.pipeline.stop = AsyncMock()
    coordinator.injection_controller = InjectionController()
    coordinator.injection_controller.loop = coordinator._loop
    coordinator.state = AppState.LISTENING
    cfg = EffectiveCloudflareConfig(
        url="ws://localhost",
        model="@cf/deepgram/nova-3",
        protocol="deepgram_nova",
        sample_rate=16000,
        language="",
        endpointing_ms=500,
        stop_timeout=0.2,
        is_test=True,
    )
    provider = CloudflareProvider("", coordinator.on_partial, coordinator.on_final, cfg)
    provider.ws = AsyncMock()
    provider._is_running = True
    provider._has_audio = True

    async def acknowledge(message):
        await provider._handle_event(
            {
                "type": "Results",
                "is_final": True,
                "from_finalize": True,
                "channel": {"alternatives": [{"transcript": "test phrase"}]},
                "start": 0,
                "duration": 1,
                "channel_index": [0, 1],
            }
        )

    provider.ws.send.side_effect = acknowledge
    coordinator.connection_manager.provider = provider
    await coordinator.stop_listening()
    assert coordinator.state == AppState.IDLE
    assert not any(
        call.args == ("Final transcription failed",)
        for call in coordinator.ui_bridge.update_status_message.call_args_list
    )


def test_short_click_between_samples_is_not_lost(mocker):
    callback = MagicMock()
    monitor = MouseMonitor(callback)
    monitor._stop_event = MagicMock()
    monitor._stop_event.is_set.return_value = False
    monitor._stop_event.wait.side_effect = [False, False, True]
    mocker.patch("engine.mouse.threading.Thread")
    # The button is released at both samples; the short click changes foreground.
    mocker.patch("engine.mouse._read_position", return_value=(100, 200))
    mocker.patch("engine.mouse._read_foreground", side_effect=[10, 10, 20], create=True)
    monitor._poll()
    while not monitor._clicks.empty():
        monitor._notify(monitor._clicks.get_nowait())
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
async def test_assemblyai_completed_turn_with_silent_audio_keeps_hot_connection(coordinator):
    import numpy as np

    from engine.audio.adapter import AudioAdapter

    coordinator.loop = asyncio.get_running_loop()
    coordinator.state = AppState.LISTENING
    coordinator.config.transcription.provider = "assemblyai"
    coordinator._recording_provider = "assemblyai"
    coordinator.pipeline.stop = AsyncMock()
    provider = AssemblyAIProvider(
        "",
        coordinator.on_partial,
        coordinator.on_final,
        resolve_effective_config(coordinator.config).assemblyai,
    )
    provider.ws = AsyncMock()
    provider._is_running = True
    await provider._handle_event(
        {
            "type": "Turn",
            "turn_order": 0,
            "transcript": "Complete phrase.",
            "end_of_turn": True,
            "turn_is_formatted": True,
        }
    )
    adapter = AudioAdapter(16000, provider.get_audio_spec())
    audio = adapter.process(np.zeros(1600, dtype=np.float32))
    await provider.notify_voice_activity(adapter.voice_active, 1.0)
    await provider.send_audio(audio, 1.0)
    coordinator.connection_manager.provider = provider
    await coordinator.stop_listening()
    assert coordinator.state == AppState.IDLE
    assert coordinator.connection_manager.provider is provider
    assert provider.is_running
    assert provider.ws.send.call_args.args == (audio,)
    assert ("Final transcription failed",) not in [
        call.args for call in coordinator.ui_bridge.update_status_message.call_args_list
    ]


@pytest.mark.asyncio
async def test_click_away_blocks_late_final_text_immediately(coordinator):
    coordinator._loop = asyncio.get_running_loop()
    coordinator.state = AppState.LISTENING
    coordinator.injection_controller.begin(MagicMock())
    coordinator.injection_controller.target.is_match.return_value = False
    coordinator.config.hotkeys.hold_mode = False
    coordinator.config.interaction.cancel_on_click_outside_anchor = True
    coordinator.stop_listening = AsyncMock()
    coordinator.injection_controller.queue = MagicMock()
    coordinator._on_mouse_click(100, 200)
    coordinator.on_final("late phrase")
    await asyncio.sleep(0)
    assert coordinator.injection_controller.cancelled
    coordinator.injection_controller.queue.assert_not_called()


@pytest.mark.asyncio
async def test_insertion_timeout_is_not_reported_as_transcription_failure(coordinator, caplog):
    coordinator._loop = asyncio.get_running_loop()
    coordinator.state = AppState.LISTENING
    coordinator.pipeline.stop = AsyncMock()
    coordinator.config.audio.provider_stop_timeout_seconds = 0.01
    provider = MagicMock(is_running=True)
    provider.finish_utterance = AsyncMock()
    coordinator.connection_manager.provider = provider
    coordinator.loop = asyncio.get_running_loop()
    await coordinator.injection_controller.lock.acquire()
    coordinator.injection_controller.queue("pending text")
    await coordinator.stop_listening()
    statuses = [call.args[0] for call in coordinator.ui_bridge.update_status_message.call_args_list]
    assert "Could not insert final text" in statuses
    assert "Final transcription failed" not in statuses
    assert "stage=editor_insertion" in caplog.text
    coordinator.injection_controller.lock.release()
    assert coordinator.injection_controller.cancelled
    await coordinator.injection_controller.drain()


@pytest.mark.asyncio
async def test_recorded_audio_gets_longer_finalization_but_not_insertion_timeout(
    coordinator, mocker
):
    coordinator.loop = asyncio.get_running_loop()
    coordinator.state = AppState.LISTENING
    coordinator._recording_provider = "cloudflare"
    coordinator.config.transcription.provider = "cloudflare"
    coordinator.config.providers.cloudflare.core.model = "microsoft/mai-transcribe-2"
    coordinator.config.audio.provider_stop_timeout_seconds = 0.01
    coordinator.pipeline.stop = AsyncMock()
    provider = MagicMock(is_running=True)
    provider.finish_utterance = AsyncMock()
    coordinator.connection_manager.provider = provider
    timeout = mocker.spy(asyncio, "timeout")
    await coordinator.stop_listening()
    provider.finish_utterance.assert_awaited_once()
    assert timeout.call_args_list[0].args == (60.0,)
    assert timeout.call_args_list[1].args == (0.01,)
    assert coordinator.state == AppState.IDLE


@pytest.mark.asyncio
async def test_provider_timeout_keeps_finalization_failure_and_logs_stage(coordinator, caplog):
    coordinator._loop = asyncio.get_running_loop()
    coordinator.state = AppState.LISTENING
    coordinator.pipeline.stop = AsyncMock()
    provider = MagicMock(is_running=True)
    provider.finish_utterance = AsyncMock(side_effect=TimeoutError())
    coordinator.connection_manager.provider = provider
    await coordinator.stop_listening()
    coordinator.ui_bridge.update_status_message.assert_any_call("Final transcription failed")
    assert "stage=provider_finalize" in caplog.text


@pytest.mark.asyncio
async def test_stop_during_editor_focus_check_does_not_create_pipeline_error(coordinator, mocker):
    coordinator.state = AppState.LISTENING
    coordinator.injection_controller.begin(MagicMock())

    async def check(*args):
        coordinator.state = AppState.IDLE
        coordinator.injection_controller.release()
        return False

    mocker.patch("main.asyncio.to_thread", side_effect=check)
    mocker.patch("main.asyncio.sleep", new=AsyncMock())
    await coordinator._listening_monitor_loop()
    assert coordinator.state == AppState.IDLE


@pytest.mark.asyncio
async def test_final_text_after_focus_change_is_discarded_during_stop(coordinator, mocker):
    coordinator.loop = asyncio.get_running_loop()
    coordinator.state = AppState.LISTENING
    target = MagicMock()
    target.has_focus.return_value = False
    coordinator.injection_controller.begin(target)
    coordinator.pipeline.stop = AsyncMock()
    inject = mocker.patch.object(coordinator.injection_controller.injector, "inject")
    provider = MagicMock(is_running=True)

    async def finish():
        assert coordinator.injection_controller.target is target
        coordinator.on_final("late phrase")

    provider.finish_utterance = AsyncMock(side_effect=finish)
    coordinator.connection_manager.provider = provider
    await coordinator.stop_listening()
    inject.assert_not_called()
    assert coordinator.state == AppState.IDLE
    assert coordinator.injection_controller.cancelled
    assert coordinator.injection_controller.target is None


@pytest.mark.asyncio
async def test_final_text_still_inserts_into_unchanged_target(coordinator, mocker):
    coordinator.loop = asyncio.get_running_loop()
    coordinator.state = AppState.LISTENING
    coordinator.injection_controller.begin(MagicMock())
    coordinator.injection_controller.target.has_focus.return_value = True
    coordinator.pipeline.stop = AsyncMock()
    inject = mocker.patch.object(coordinator.injection_controller.injector, "inject")
    provider = MagicMock(is_running=True)

    async def finish():
        coordinator.on_final("last words")

    provider.finish_utterance = AsyncMock(side_effect=finish)
    coordinator.connection_manager.provider = provider
    await coordinator.stop_listening()
    inject.assert_called_once_with("last words", True)
    assert coordinator.state == AppState.IDLE
    assert not coordinator.injection_controller.cancelled


@pytest.mark.asyncio
async def test_any_key_stop_preserves_final_transcript(coordinator):
    coordinator.loop = asyncio.get_running_loop()
    coordinator.state = AppState.LISTENING
    coordinator.start_time = 0
    coordinator.config.hotkeys.hold_mode = False
    coordinator.injection_controller.begin(MagicMock())
    stopped = asyncio.Event()
    coordinator.stop_listening = AsyncMock(side_effect=stopped.set)
    coordinator.injection_controller.queue = MagicMock()
    coordinator._on_manual_stop("x")
    coordinator.on_final("car")
    await asyncio.wait_for(stopped.wait(), timeout=1)
    assert not coordinator.injection_controller.cancelled
    coordinator.stop_listening.assert_awaited_once()
    coordinator.injection_controller.queue.assert_called_once_with("car", is_final=True)


@pytest.mark.asyncio
async def test_stop_during_pipeline_start_does_not_restore_listening(coordinator, mocker):
    coordinator.loop = asyncio.get_running_loop()
    target = MagicMock(can_dictate=True)
    target.has_focus.return_value = True
    mocker.patch("main.Anchor.capture_current", return_value=target)
    coordinator.get_provider_availability = MagicMock(
        return_value={coordinator.config.transcription.provider: True}
    )
    coordinator.connection_manager.ensure_connected = AsyncMock()
    coordinator.connection_manager.provider = MagicMock(is_running=False)
    entered = asyncio.Event()
    resume = asyncio.Event()

    async def start(**kwargs):
        entered.set()
        await resume.wait()

    coordinator.pipeline.start = start
    coordinator.pipeline.stop = AsyncMock()
    task = asyncio.create_task(coordinator.start_listening())
    await entered.wait()
    await coordinator.stop_listening()
    resume.set()
    await task
    assert coordinator.state == AppState.IDLE


@pytest.mark.asyncio
async def test_pipeline_drain_timeout_reports_failure(coordinator):
    coordinator.state = AppState.LISTENING
    coordinator.pipeline.stop = AsyncMock(side_effect=[TimeoutError(), None])
    coordinator.connection_manager.stop_provider = AsyncMock()
    await coordinator.stop_listening()
    assert coordinator.state == AppState.ERROR
    coordinator.ui_bridge.update_status_message.assert_any_call("Final transcription failed")


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [AudioHardwareError("mic"), RuntimeError("start")])
async def test_stale_start_failure_does_not_stop_new_session(coordinator, mocker, error):
    coordinator.loop = asyncio.get_running_loop()
    target = MagicMock(can_dictate=True)
    target.has_focus.return_value = True
    mocker.patch("main.Anchor.capture_current", return_value=target)
    coordinator.get_provider_availability = MagicMock(
        return_value={coordinator.config.transcription.provider: True}
    )
    coordinator.connection_manager.ensure_connected = AsyncMock()
    coordinator.connection_manager.provider = MagicMock(is_running=False)
    entered = asyncio.Event()
    resume = asyncio.Event()

    async def start(**kwargs):
        entered.set()
        await resume.wait()
        raise error

    coordinator.pipeline.start = start
    coordinator.pipeline.stop = AsyncMock()
    task = asyncio.create_task(coordinator.start_listening())
    await entered.wait()
    await coordinator.stop_listening()
    coordinator._session_token = object()
    coordinator.state = AppState.LISTENING
    coordinator.stop_listening = AsyncMock()
    resume.set()
    await task
    await asyncio.sleep(0)
    assert coordinator.state == AppState.LISTENING
    coordinator.stop_listening.assert_not_awaited()
