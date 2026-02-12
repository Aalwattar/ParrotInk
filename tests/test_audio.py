from unittest.mock import patch
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
    import asyncio
    import threading

    loop = asyncio.new_event_loop()

    # Run loop in thread
    def run_loop(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    t = threading.Thread(target=run_loop, args=(loop,), daemon=True)
    t.start()

    try:
        with patch("sounddevice.InputStream"):
            streamer = AudioStreamer()
            streamer.start(loop=loop)
    
            chunk = np.array([0.1, 0.2, 0.3], dtype=np.float32)
            # Simulate callback
            streamer._callback(chunk, 3, None, None)

        # Give some time for call_soon_threadsafe to execute
        import time

        for _ in range(10):
            if streamer.async_q.qsize() == 1:
                break
            time.sleep(0.1)

        assert streamer.async_q.qsize() == 1
        normalized, _ = streamer.async_q.get_nowait()
        assert np.array_equal(normalized, chunk)
        streamer.stop()
    finally:
        loop.call_soon_threadsafe(loop.stop)
        t.join(timeout=1.0)


def test_audio_normalization_stereo():
    """Test normalization of stereo audio (downmixing)."""
    import asyncio
    import threading

    loop = asyncio.new_event_loop()

    def run_loop(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    t = threading.Thread(target=run_loop, args=(loop,), daemon=True)
    t.start()

    try:
        with patch("sounddevice.InputStream"):
            streamer = AudioStreamer()
            streamer.start(loop=loop)
    
            # 2 channels, 3 frames
            chunk = np.array([[0.1, 0.5], [0.2, 0.6], [0.3, 0.7]], dtype=np.float32)
            streamer._callback(chunk, 3, None, None)

        import time

        for _ in range(10):
            if streamer.async_q.qsize() == 1:
                break
            time.sleep(0.1)

        assert streamer.async_q.qsize() == 1
        normalized, _ = streamer.async_q.get_nowait()
        # Mean of [0.1, 0.5] is 0.3, etc.
        expected = np.array([0.3, 0.4, 0.5], dtype=np.float32)
        assert np.allclose(normalized, expected)
        streamer.stop()
    finally:
        loop.call_soon_threadsafe(loop.stop)
        t.join(timeout=1.0)


def test_play_sound_missing_file():
    """Verify that play_sound does not raise exception if file is missing."""
    from engine.audio_feedback import play_sound

    # Should not raise anything
    play_sound("non_existent.wav")
