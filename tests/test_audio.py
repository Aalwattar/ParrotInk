import asyncio
import unittest
from unittest.mock import patch

import numpy as np

from engine.audio import AudioStreamer


class TestAudioStreamer(unittest.IsolatedAsyncioTestCase):
    def test_audio_streamer_init(self):
        """Verify that AudioStreamer initializes with correct sample rate and chunk size."""
        streamer = AudioStreamer(sample_rate=16000, chunk_size=1024)
        self.assertEqual(streamer.sample_rate, 16000)
        self.assertEqual(streamer.chunk_size, 1024)
        self.assertFalse(streamer.is_running)

    @patch("sounddevice.InputStream")
    async def test_audio_normalization_mono(self, mock_input_stream):
        """Test normalization of already mono audio."""
        loop = asyncio.get_event_loop()

        try:
            streamer = AudioStreamer()
            await streamer.start(loop=loop)

            chunk = np.array([0.1, 0.2, 0.3], dtype=np.float32)
            # Simulate callback
            streamer._callback(chunk, 3, None, None)

            # Give some time for call_soon_threadsafe to execute
            for _ in range(20):
                if streamer.async_q.qsize() == 1:
                    break
                await asyncio.sleep(0.1)

            self.assertEqual(streamer.async_q.qsize(), 1)
            normalized, _ = streamer.async_q.get_nowait()
            self.assertTrue(np.array_equal(normalized, chunk))
            streamer.stop()
        finally:
            pass

    @patch("sounddevice.InputStream")
    async def test_audio_normalization_stereo(self, mock_input_stream):
        """Test normalization of stereo audio (downmixing)."""
        loop = asyncio.get_event_loop()

        try:
            streamer = AudioStreamer()
            await streamer.start(loop=loop)

            # 2 channels, 3 frames
            chunk = np.array([[0.1, 0.5], [0.2, 0.6], [0.3, 0.7]], dtype=np.float32)
            streamer._callback(chunk, 3, None, None)

            for _ in range(20):
                if streamer.async_q.qsize() == 1:
                    break
                await asyncio.sleep(0.1)

            self.assertEqual(streamer.async_q.qsize(), 1)
            normalized, _ = streamer.async_q.get_nowait()
            # Mean of [0.1, 0.5] is 0.3, etc.
            expected = np.array([0.3, 0.4, 0.5], dtype=np.float32)
            self.assertTrue(np.allclose(normalized, expected))
            streamer.stop()
        finally:
            pass


def test_play_sound_missing_file():
    """Verify that play_sound does not raise exception if file is missing."""
    from engine.audio_feedback import play_sound

    # Should not raise anything
    play_sound("non_existent.wav")


if __name__ == "__main__":
    unittest.main()
