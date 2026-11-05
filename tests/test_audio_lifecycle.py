import asyncio
import threading
from unittest.mock import AsyncMock, Mock

import numpy as np
import pytest

from engine.audio.pipeline import AudioPipeline
from engine.audio.streamer import AudioStreamer


@pytest.mark.asyncio
async def test_cancelled_open_closes_late_stream():
    streamer = AudioStreamer()
    entered, release = threading.Event(), threading.Event()
    stream = Mock()

    def open_stream(rate, generation):
        entered.set()
        release.wait(2)
        return stream

    streamer._try_open_stream = open_stream
    task = asyncio.create_task(streamer.start())
    await asyncio.to_thread(entered.wait, 2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    release.set()
    for _ in range(100):
        if stream.close.called:
            break
        await asyncio.sleep(0.01)
    stream.close.assert_called_once()
    stream.start.assert_not_called()
    assert not streamer.is_running


@pytest.mark.asyncio
async def test_stop_drains_audio_and_reports_sustained_voice():
    streamer = AudioStreamer()
    streamer._try_open_stream = Mock(return_value=Mock(samplerate=16000, channels=1))
    pipeline = AudioPipeline(streamer)
    adapter = Mock(capture_rate_hz=16000, voice_active=True)
    adapter.process.side_effect = lambda chunk: chunk
    provider = Mock(is_running=True)
    provider.send_audio = AsyncMock()
    provider.notify_voice_activity = AsyncMock()
    activity = Mock()
    pipeline.on_voice_activity = activity
    await pipeline.start(adapter, provider, asyncio.get_running_loop())
    streamer._push_to_queue(np.array([1]), 1.0)
    streamer._push_to_queue(np.array([2]), 2.0)
    await pipeline.stop()
    assert provider.send_audio.await_count == 2
    assert activity.call_count == 2


@pytest.mark.asyncio
async def test_stop_during_start_does_not_start_pipeline():
    streamer = Mock(sample_rate=16000)
    entered, release = asyncio.Event(), asyncio.Event()

    async def start(loop):
        entered.set()
        await release.wait()

    streamer.start = start
    pipeline = AudioPipeline(streamer)
    task = asyncio.create_task(
        pipeline.start(Mock(capture_rate_hz=16000), Mock(), asyncio.get_running_loop())
    )
    await entered.wait()
    await pipeline.stop()
    release.set()
    await task
    assert not pipeline.is_active
    assert pipeline._audio_task is None


@pytest.mark.asyncio
async def test_drain_timeout_cleans_up_full_queue_sentinel():
    streamer = AudioStreamer()
    streamer.async_q = asyncio.Queue(maxsize=1)
    streamer._try_open_stream = Mock(return_value=Mock(samplerate=16000, channels=1))
    pipeline = AudioPipeline(streamer)
    adapter = Mock(capture_rate_hz=16000, voice_active=True)
    adapter.process.side_effect = lambda chunk: chunk
    provider = Mock(is_running=True)
    entered = asyncio.Event()

    async def blocked_send(*args):
        entered.set()
        await asyncio.Event().wait()

    provider.send_audio = blocked_send
    provider.notify_voice_activity = AsyncMock()
    await pipeline.start(adapter, provider, asyncio.get_running_loop())
    streamer._push_to_queue(np.array([1]), 1.0)
    await entered.wait()
    streamer._push_to_queue(np.array([2]), 2.0)
    with pytest.raises(asyncio.TimeoutError):
        await pipeline.stop()
    assert streamer._sentinel_task is None
    assert streamer.async_q.qsize() == 1


@pytest.mark.asyncio
async def test_old_stream_callback_does_not_enter_new_session():
    streamer = AudioStreamer()
    streamer._loop = asyncio.get_running_loop()
    old_generation = streamer._start_cancel
    streamer._start_cancel = threading.Event()
    streamer._callback(np.array([1]), 1, None, None, generation=old_generation)
    await asyncio.sleep(0)
    assert streamer.async_q.empty()


@pytest.mark.asyncio
async def test_device_stop_failure_cleans_up_consumer():
    streamer = AudioStreamer()
    device = Mock(samplerate=16000, channels=1)
    device.stop.side_effect = RuntimeError("device failure")
    streamer._try_open_stream = Mock(return_value=device)
    pipeline = AudioPipeline(streamer)
    await pipeline.start(Mock(capture_rate_hz=16000), Mock(), asyncio.get_running_loop())
    task = pipeline._audio_task
    await asyncio.sleep(0)
    with pytest.raises(RuntimeError, match="device failure"):
        await pipeline.stop()
    device.close.assert_called_once()
    assert task.done()
    assert pipeline._audio_task is None
    assert streamer._sentinel_task is None
    assert streamer._loop is None
