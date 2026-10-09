import asyncio
import importlib.util
import json
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import numpy as np
import pytest
import websockets

from engine.audio.adapter import ProviderAudioSpec
from engine.config import Config
from engine.eval_main import EvalCoordinator


@pytest.fixture
def eval_args(tmp_path):
    audio = tmp_path / "recording.wav"
    with wave.open(str(audio), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(bytes(16000))
    return SimpleNamespace(
        provider="assemblyai",
        audio=str(audio),
        config=None,
        verbose=0,
        quiet=True,
        timeout_seconds=2.0,
    )


@pytest.mark.asyncio
async def test_eval_replays_complete_audio_and_drains_last_turn(eval_args, capsys):
    provider = SimpleNamespace(
        get_audio_spec=lambda: ProviderAudioSpec(16000),
        start=AsyncMock(),
        wait_for_ready=AsyncMock(),
        stop=AsyncMock(),
        notify_voice_activity=AsyncMock(),
    )
    sent = []

    async def replay():
        for i in range(3):
            yield np.full(1600, 0.02, dtype=np.float32), (i + 1) / 10

    async def send_audio(chunk, capture_time):
        sent.append(chunk)
        if len(sent) == 1:
            coordinator.on_final("First turn.")

    async def finish():
        assert len(sent) == 3
        coordinator.on_final("Last turn.")

    provider.send_audio = send_audio
    provider.finish_utterance = AsyncMock(side_effect=finish)
    with (
        patch("engine.eval_main.load_config", return_value=Config()),
        patch("engine.eval_main.configure_logging"),
        patch("engine.eval_main.TranscriptionFactory.create", return_value=provider),
        patch("engine.eval_main.WavReplayer") as replayer,
    ):
        replayer.return_value.async_generator = replay
        coordinator = EvalCoordinator(eval_args)
        await coordinator.run()

    result = json.loads(capsys.readouterr().out.strip())
    assert result["status"] == "ok"
    assert result["final_text"] == "First turn. Last turn."
    assert result["time_to_first_final_s"] is not None
    provider.wait_for_ready.assert_awaited_once()
    provider.finish_utterance.assert_awaited_once()
    provider.stop.assert_awaited_once()
    assert provider.notify_voice_activity.await_count == 3
    assert provider.notify_voice_activity.await_args_list[-1].args == (True, 0.3)


@pytest.mark.asyncio
async def test_eval_connection_failure_closes_provider_and_adapter(eval_args, capsys):
    provider = SimpleNamespace(
        get_audio_spec=lambda: ProviderAudioSpec(16000),
        start=AsyncMock(side_effect=ConnectionError("bad credentials")),
        stop=AsyncMock(),
    )
    with (
        patch("engine.eval_main.load_config", return_value=Config()),
        patch("engine.eval_main.configure_logging"),
        patch("engine.eval_main.TranscriptionFactory.create", return_value=provider),
        patch("engine.eval_main.AudioAdapter") as adapter,
    ):
        await EvalCoordinator(eval_args).run()
    result = json.loads(capsys.readouterr().out.strip())
    assert result["error_code"] == "provider_auth"
    provider.stop.assert_awaited_once()
    adapter.return_value.close.assert_called_once()


@pytest.mark.asyncio
async def test_eval_timeout_closes_provider_without_orphaned_replay(eval_args, capsys):
    eval_args.timeout_seconds = 0.01
    provider = SimpleNamespace(
        get_audio_spec=lambda: ProviderAudioSpec(16000),
        start=AsyncMock(),
        wait_for_ready=AsyncMock(),
        stop=AsyncMock(),
        send_audio=AsyncMock(),
        notify_voice_activity=AsyncMock(),
        finish_utterance=AsyncMock(),
    )
    exited = []

    async def replay():
        try:
            await asyncio.sleep(1)
            yield np.zeros(1600, dtype=np.float32), 0.1
        finally:
            exited.append(True)

    with (
        patch("engine.eval_main.load_config", return_value=Config()),
        patch("engine.eval_main.configure_logging"),
        patch("engine.eval_main.TranscriptionFactory.create", return_value=provider),
        patch("engine.eval_main.WavReplayer") as replayer,
    ):
        replayer.return_value.async_generator = replay
        await EvalCoordinator(eval_args).run()
    result = json.loads(capsys.readouterr().out.strip())
    assert result["error_code"] == "timeout"
    assert exited == [True]
    provider.stop.assert_awaited_once()
    provider.finish_utterance.assert_not_awaited()


@pytest.fixture
def mock_server_module():
    path = Path(__file__).with_name("mock_transcription_server.py")
    spec = importlib.util.spec_from_file_location("modern_mock_transcription", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
async def test_mock_assemblyai_accepts_binary_audio_and_v3_control(mock_server_module):
    async with websockets.serve(
        mock_server_module.mock_assemblyai_handler, "127.0.0.1", 0
    ) as server:
        port = server.sockets[0].getsockname()[1]
        async with websockets.connect(f"ws://127.0.0.1:{port}") as ws:
            begin = json.loads(await asyncio.wait_for(ws.recv(), timeout=1))
            assert begin["type"] == "Begin"
            await ws.send(b"\x01\x00" * 100)
            partial = json.loads(await asyncio.wait_for(ws.recv(), timeout=1))
            assert partial["type"] == "Turn" and not partial["end_of_turn"]
            await ws.send(json.dumps({"type": "ForceEndpoint"}))
            final = json.loads(await asyncio.wait_for(ws.recv(), timeout=1))
            assert final["end_of_turn"] and final["turn_is_formatted"]
            await ws.send(json.dumps({"type": "Terminate"}))
            termination = json.loads(await asyncio.wait_for(ws.recv(), timeout=1))
            assert termination["type"] == "Termination"


@pytest.mark.asyncio
async def test_mock_openai_acknowledges_session_and_explicit_commit(mock_server_module):
    async with websockets.serve(mock_server_module.mock_openai_handler, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        async with websockets.connect(f"ws://127.0.0.1:{port}") as ws:
            await ws.send(
                json.dumps(
                    {
                        "type": "session.update",
                        "session": {
                            "audio": {"input": {"transcription": {"model": "gpt-live-transcribe"}}},
                        },
                    }
                )
            )
            assert json.loads(await ws.recv())["type"] == "session.updated"
            await ws.send(json.dumps({"type": "input_audio_buffer.append", "audio": "AQAA"}))
            await ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
            events = [json.loads(await asyncio.wait_for(ws.recv(), timeout=1)) for _ in range(3)]
            assert events[0]["type"] == "input_audio_buffer.committed"
            assert events[1]["type"].endswith(".delta")
            assert events[2]["type"].endswith(".completed")
            assert len({event["item_id"] for event in events}) == 1
