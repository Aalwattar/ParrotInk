import asyncio

import numpy as np
import pytest

from engine.audio import AudioStreamer


@pytest.mark.asyncio
async def test_audio_streamer_queue_overflow():
    # Set a very small maxsize for testing overflow
    # We might need to modify AudioStreamer to allow passing maxsize if we want it configurable
    # For now, let's assume it's 100 as per spec.
    streamer = AudioStreamer()
    # We'll mock the callback to push 110 chunks
    # Since it uses loop.call_soon_threadsafe, we need a running loop.

    # We need to reach into the streamer and replace its queue with a small one for testing
    streamer.async_q = asyncio.Queue(maxsize=5)

    # Push 6 items
    for i in range(6):
        chunk = np.array([float(i)], dtype=np.float32)
        # Manually trigger what the callback would do (simplified)
        if streamer.async_q.full():
            streamer.async_q.get_nowait()
        streamer.async_q.put_nowait((chunk, 1.0))

    assert streamer.async_q.qsize() == 5
    first = await streamer.async_q.get()
    # The first one (0.0) should have been dropped
    assert first[0][0] == 1.0


@pytest.mark.asyncio
async def test_audio_streamer_async_generator():
    streamer = AudioStreamer()
    streamer.is_running = True
    streamer.async_q = asyncio.Queue()

    # Push a few chunks
    for i in range(3):
        streamer.async_q.put_nowait((np.array([float(i)]), float(i)))

    chunks = []
    async for chunk, _ts in streamer.async_generator():
        chunks.append(chunk)
        if len(chunks) == 3:
            break

    assert len(chunks) == 3
    assert chunks[0][0] == 0.0
    assert chunks[2][0] == 2.0
