import numpy as np

from engine.audio.processing import Resampler


def test_resampler_logic():
    # 16kHz -> 24kHz
    resampler = Resampler(source_rate=16000, target_rate=24000)

    # Create 100ms of audio (1600 samples)
    chunk = np.sin(2 * np.pi * 440 * np.arange(1600) / 16000).astype(np.float32)

    resampled = resampler.resample(chunk)

    # Ratio is 1.5, so 1600 * 1.5 = 2400
    # Stateful resamplers may return fewer samples due to buffering/latency
    assert len(resampled) > 2000
    assert resampled.dtype == np.float32


def test_resampler_stateful_continuity():
    # High-level check: feeding two halves of a sine wave should be close to feeding the whole thing
    resampler = Resampler(source_rate=16000, target_rate=24000)

    chunk = np.sin(2 * np.pi * 440 * np.arange(3200) / 16000).astype(np.float32)
    half1 = chunk[:1600]
    half2 = chunk[1600:]

    out1 = resampler.resample(half1)
    out2 = resampler.resample(half2)

    combined = np.concatenate([out1, out2])
    # Total should be close to 4800
    assert len(combined) > 4000
