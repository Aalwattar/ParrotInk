import numpy as np

from engine.audio import AudioStreamer


def test_audio_streamer_init():
    """Verify that AudioStreamer initializes with correct sample rate and chunk size."""
    streamer = AudioStreamer(sample_rate=16000, chunk_size=1024)
    assert streamer.sample_rate == 16000
    assert streamer.chunk_size == 1024
    assert not streamer.is_running


def test_audio_normalization_mono():
    """Test normalization of already mono audio."""
    streamer = AudioStreamer()
    chunk = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    normalized = streamer._normalize_audio(chunk)
    assert np.array_equal(normalized, chunk)


def test_audio_normalization_stereo():
    """Test normalization of stereo audio (downmixing)."""
    streamer = AudioStreamer()
    # 2 channels, 3 frames
    chunk = np.array([[0.1, 0.5], [0.2, 0.6], [0.3, 0.7]], dtype=np.float32)
    normalized = streamer._normalize_audio(chunk)
    # Mean of [0.1, 0.5] is 0.3, etc.
    expected = np.array([0.3, 0.4, 0.5], dtype=np.float32)
    assert np.allclose(normalized, expected)


def test_play_sound_missing_file():
    """Verify that play_sound does not raise exception if file is missing."""
    from engine.audio_feedback import play_sound

    # Should not raise anything
    play_sound("non_existent.wav")
