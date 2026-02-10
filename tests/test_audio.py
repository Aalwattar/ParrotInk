import numpy as np
import pytest

from engine.audio import AudioStreamer


def test_audio_streamer_initialization():
    """Test that AudioStreamer initializes with correct parameters."""
    streamer = AudioStreamer(sample_rate=16000, chunk_size=1024)
    assert streamer.sample_rate == 16000
    assert streamer.chunk_size == 1024
    assert not streamer.is_running


def test_audio_callback(mocker):
    """Test the audio callback processing."""
    streamer = AudioStreamer()
    # Mock data: 1024 frames of 1 channel float32
    indata = np.random.uniform(-1, 1, (1024, 1)).astype(np.float32)

    # We want to verify that data is put into the queue
    streamer._callback(indata, 1024, None, None)

    # Check if queue has data
    assert not streamer.queue.empty()
    queued_data = streamer.queue.get()
    assert np.array_equal(queued_data, indata)


def test_audio_generator(mocker):
    """Test that the generator yields data from the queue."""
    streamer = AudioStreamer()
    streamer.is_running = True

    # Put two chunks in the queue
    chunk1 = np.zeros((1024, 1), dtype=np.float32)
    chunk2 = np.ones((1024, 1), dtype=np.float32)
    streamer.queue.put(chunk1)
    streamer.queue.put(chunk2)

    gen = streamer.generator()

    # Get first chunk
    received1 = next(gen)
    assert np.array_equal(received1, chunk1)

    # Get second chunk
    received2 = next(gen)
    assert np.array_equal(received2, chunk2)

    # Stop streamer and ensure generator terminates
    streamer.is_running = False
    with pytest.raises(StopIteration):
        next(gen)
