import numpy as np
import pytest
import asyncio
from engine.audio import AudioStreamer

def test_audio_init():
    """Test initialization of AudioStreamer."""
    streamer = AudioStreamer(sample_rate=16000, chunk_size=1024)
    assert streamer.sample_rate == 16000
    assert streamer.chunk_size == 1024
    assert not streamer.is_running
    assert streamer.queue.empty()

def test_audio_callback():
    """Test the audio callback processing."""
    streamer = AudioStreamer()
    # Mock data: 1024 frames of 1 channel float32
    indata = np.random.uniform(-1, 1, (1024, 1)).astype(np.float32)
    
    # We want to verify that data is put into the queue
    streamer._callback(indata, 1024, None, None)
    
    # Check if queue has data
    assert not streamer.queue.empty()
    queued_data, capture_time = streamer.queue.get()
    assert np.array_equal(queued_data, indata)
    assert isinstance(capture_time, float)

def test_normalize_audio_mono():
    """Test normalization of already mono audio."""
    streamer = AudioStreamer()
    chunk = np.random.uniform(-1, 1, 1024).astype(np.float32)
    normalized = streamer._normalize_audio(chunk)
    assert normalized.shape == (1024,)
    assert np.array_equal(normalized, chunk)

def test_normalize_audio_stereo():
    """Test normalization (downmixing) of stereo audio."""
    streamer = AudioStreamer()
    # 1024 frames, 2 channels
    chunk = np.random.uniform(-1, 1, (1024, 2)).astype(np.float32)
    normalized = streamer._normalize_audio(chunk)
    assert normalized.shape == (1024,)
    # Should be average of channels
    expected = np.mean(chunk, axis=1)
    assert np.allclose(normalized, expected)

@pytest.mark.asyncio
async def test_audio_async_generator():
    """Test that the async_generator yields data from the queue."""
    streamer = AudioStreamer()
    streamer.is_running = True

    # Put two chunks in the queue with dummy timestamps
    chunk1 = np.zeros((1024, 1), dtype=np.float32)
    chunk2 = np.ones((1024, 1), dtype=np.float32)
    streamer.queue.put((chunk1, 1.0))
    streamer.queue.put((chunk2, 2.0))

    gen = streamer.async_generator()
    
    # Get first chunk
    val1, t1 = await gen.__anext__()
    assert val1.shape == (1024,)
    assert np.all(val1 == 0)
    assert t1 == 1.0

    # Get second chunk
    val2, t2 = await gen.__anext__()
    assert val2.shape == (1024,)
    assert np.all(val2 == 1)
    assert t2 == 2.0

    # Stop and verify it exits
    streamer.is_running = False
    # The generator should finish now
    with pytest.raises(StopAsyncIteration):
        await gen.__anext__()