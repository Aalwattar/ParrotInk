import base64

import numpy as np
import pytest

from engine.audio.adapter import AudioAdapter, ProviderAudioSpec


@pytest.mark.parametrize("amplitude,expected", [(0.0, False), (0.05, True)])
def test_voice_activity_is_a_python_boolean(amplitude, expected):
    adapter = AudioAdapter(16000, ProviderAudioSpec(16000, wire_encoding="pcm16_bytes"))
    adapter.process(np.full(1600, amplitude, dtype=np.float32))
    assert adapter.voice_active is expected


def test_audio_adapter_pcm16_bytes():
    spec = ProviderAudioSpec(
        sample_rate_hz=16000, channels=1, bit_depth=16, wire_encoding="pcm16_bytes"
    )

    # Capture is 16k

    adapter = AudioAdapter(capture_rate_hz=16000, provider_spec=spec)

    # Input float32 16k

    chunk = np.array([0.0, 0.5, 1.0], dtype=np.float32)

    processed = adapter.process(chunk)

    assert isinstance(processed, bytes)

    # 3 samples * 2 bytes = 6 bytes

    assert len(processed) == 6

    # Check values (little endian)

    # 0.5 * 32767 = 16383 (0x3FFF) -> \xff\x3f

    assert processed[2:4] == b"\xff\x3f"


def test_audio_adapter_pcm16_base64():
    spec = ProviderAudioSpec(
        sample_rate_hz=16000, channels=1, bit_depth=16, wire_encoding="pcm16_base64"
    )

    adapter = AudioAdapter(capture_rate_hz=16000, provider_spec=spec)

    chunk = np.array([0.0, 1.0], dtype=np.float32)

    processed = adapter.process(chunk)

    assert isinstance(processed, str)

    # Decode back and check

    decoded = base64.b64decode(processed)

    assert len(decoded) == 4

    assert decoded[2:4] == b"\xff\x7f"  # 32767


def test_audio_adapter_with_resampling():
    spec = ProviderAudioSpec(
        sample_rate_hz=24000,  # OpenAI
        channels=1,
        bit_depth=16,
        wire_encoding="pcm16_bytes",
    )
    adapter = AudioAdapter(capture_rate_hz=16000, provider_spec=spec)

    # 100ms at 16k = 1600 samples
    chunk = np.zeros(1600, dtype=np.float32)
    processed = adapter.process(chunk)

    # Expected output at 24k is 2400 samples
    # 2400 * 2 bytes = 4800 bytes.
    # Allowing for some buffering/latency
    assert len(processed) > 4000
    assert len(processed) <= 4800
