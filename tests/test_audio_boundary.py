import numpy as np
import pytest

from engine.audio import (
    check_audio_invariants,
    downmix_stereo_to_mono,
    reshape_to_1d,
    sanitize_nan_inf,
)
from engine.types import CaptureFormatError


def test_downmix_stereo_to_mono():
    # 2 channels, 3 frames
    stereo = np.array([[0.1, 0.5], [0.2, 0.6], [0.3, 0.7]], dtype=np.float32)
    mono = downmix_stereo_to_mono(stereo)
    expected = np.array([0.3, 0.4, 0.5], dtype=np.float32)
    assert np.allclose(mono, expected)
    assert mono.shape == (3,)


def test_downmix_already_mono():
    mono_in = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    mono_out = downmix_stereo_to_mono(mono_in)
    assert np.array_equal(mono_in, mono_out)


def test_reshape_to_1d():
    # (N, 1) -> (N,)
    n_1 = np.array([[0.1], [0.2], [0.3]], dtype=np.float32)
    n_out = reshape_to_1d(n_1)
    assert n_out.shape == (3,)
    assert np.allclose(n_out, [0.1, 0.2, 0.3])


def test_reshape_already_1d():
    n_1d = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    n_out = reshape_to_1d(n_1d)
    assert n_out.shape == (3,)


def test_sanitize_nan_inf():
    dirty = np.array([0.1, np.nan, 0.5, np.inf, -np.inf], dtype=np.float32)
    clean = sanitize_nan_inf(dirty)
    expected = np.array([0.1, 0.0, 0.5, 0.0, 0.0], dtype=np.float32)
    assert np.array_equal(clean, expected)


def test_check_audio_invariants_invalid_ndim():
    # 3D is not allowed
    invalid = np.zeros((2, 2, 2))
    with pytest.raises(CaptureFormatError, match="Invalid dimensionality"):
        check_audio_invariants(invalid)


def test_check_audio_invariants_non_numeric():
    # String array is not allowed
    invalid = np.array(["a", "b"])
    with pytest.raises(CaptureFormatError, match="Non-numeric audio data"):
        check_audio_invariants(invalid)


def test_check_audio_invariants_valid():
    valid = np.array([0.1, 0.2], dtype=np.float32)
    # Should not raise
    check_audio_invariants(valid)
