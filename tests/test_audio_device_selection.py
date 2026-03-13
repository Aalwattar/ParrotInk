import unittest
from unittest.mock import patch

from engine.audio.streamer import AudioStreamer


class TestAudioDeviceSelection(unittest.IsolatedAsyncioTestCase):
    async def test_audio_streamer_accepts_device(self):
        """Verify that AudioStreamer accepts a device parameter and passes it to sd.InputStream."""
        try:
            AudioStreamer(device_name="My Device")
        except TypeError:
            self.fail("AudioStreamer should accept a device_name argument")

    @patch("sounddevice.InputStream")
    async def test_audio_streamer_passes_device_to_sd(self, mock_input_stream):
        """Verify that AudioStreamer passes the correct device index to sounddevice."""
        # Mock sounddevice.query_devices to return a dummy device list
        mock_devices = [
            {"name": "Default Device", "max_input_channels": 1, "hostapi": 0},
            {"name": "My Custom Mic", "max_input_channels": 2, "hostapi": 0},
        ]
        mock_hostapis = [{"name": "MME"}]

        with patch("sounddevice.query_devices", return_value=mock_devices):
            with patch("sounddevice.query_hostapis", return_value=mock_hostapis):
                streamer = AudioStreamer(device_name="My Custom Mic")
                # We need to ensure start() uses the correct device
                await streamer.start()

                # Check if sd.InputStream was called with device=1 (index of "My Custom Mic")
                args, kwargs = mock_input_stream.call_args
                self.assertEqual(kwargs.get("device"), 1)
                streamer.stop()


if __name__ == "__main__":
    unittest.main()
