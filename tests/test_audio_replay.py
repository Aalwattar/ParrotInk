import time
import wave

import numpy as np
import pytest

from engine.audio.replay import WavReplayer


@pytest.fixture
def sample_wav(tmp_path):
    """Creates a 1-second 44.1kHz mono 16-bit PCM WAV file."""
    path = tmp_path / "test.wav"
    sample_rate = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # 440Hz sine wave
    data = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)

    with wave.open(str(path), "wb") as wr:
        wr.setnchannels(1)
        wr.setsampwidth(2)
        wr.setframerate(sample_rate)
        wr.writeframes(data.tobytes())

    return path


@pytest.fixture
def stereo_wav(tmp_path):
    """Creates a 1-second 44.1kHz stereo 16-bit PCM WAV file."""
    path = tmp_path / "stereo.wav"
    sample_rate = 44100
    duration = 0.5
    n_frames = int(sample_rate * duration)

    # Left: 440Hz, Right: Silence
    t = np.linspace(0, duration, n_frames, endpoint=False)
    left = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
    right = np.zeros(n_frames, dtype=np.int16)

    # Interleave
    data = np.stack((left, right), axis=1).flatten()

    with wave.open(str(path), "wb") as wr:
        wr.setnchannels(2)
        wr.setsampwidth(2)
        wr.setframerate(sample_rate)
        wr.writeframes(data.tobytes())

    return path


@pytest.mark.asyncio
async def test_replayer_mono(sample_wav):
    replayer = WavReplayer(sample_wav, chunk_ms=100)
    chunks = []
    async for chunk, _timestamp in replayer.async_generator():
        chunks.append(chunk)

    # 1 second / 100ms = 10 chunks
    assert len(chunks) == 10
    assert chunks[0].dtype == np.float32
    assert chunks[0].ndim == 1


@pytest.mark.asyncio
async def test_replayer_stereo_downmix(stereo_wav):
    replayer = WavReplayer(stereo_wav, chunk_ms=100)
    chunks = []
    async for chunk, _timestamp in replayer.async_generator():
        chunks.append(chunk)

    # 0.5 second / 100ms = 5 chunks
    assert len(chunks) == 5
    # Verify it's mono
    assert chunks[0].ndim == 1
    # Check that it's not silent (left channel had data)
    assert np.max(np.abs(chunks[0])) > 0


@pytest.mark.asyncio
async def test_replayer_pacing(sample_wav):
    replayer = WavReplayer(sample_wav, chunk_ms=200)
    start_time = time.time()
    async for _ in replayer.async_generator():
        pass
    elapsed = time.time() - start_time

    # 1 second file should take ~1 second
    assert 0.9 <= elapsed <= 1.2
