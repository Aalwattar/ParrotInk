import numpy as np

from engine.audio.processing import scale_and_clip_to_int16


def test_scale_and_clip_float():
    # Input float32 in [-1.0, 1.0]
    chunk = np.array([-1.0, 0.0, 1.0, 0.5, -0.5], dtype=np.float32)
    converted = scale_and_clip_to_int16(chunk)

    # Expected: scaled by 32767
    assert converted.dtype == np.int16
    assert converted[0] == -32767
    assert converted[1] == 0
    assert converted[2] == 32767
    assert np.allclose(converted[3], 16383, atol=1)


def test_clipping_overflow():
    # Test values outside [-1.0, 1.0]
    chunk = np.array([-1.5, 1.5, 2.0], dtype=np.float32)
    converted = scale_and_clip_to_int16(chunk)

    assert converted[0] == -32768
    assert converted[1] == 32767
    assert converted[2] == 32767


def test_int_to_int16_clipping():
    # Test passing larger integers
    chunk = np.array([-40000, 40000], dtype=np.int32)
    converted = scale_and_clip_to_int16(chunk)
    assert converted[0] == -32768
    assert converted[1] == 32767
