import unittest
from unittest.mock import MagicMock, patch

from engine.audio.streamer import AudioStreamer


class TestAudioDeviceSelection(unittest.IsolatedAsyncioTestCase):
    async def test_audio_streamer_accepts_device(self):
        """Verify that AudioStreamer accepts a device parameter."""
        try:
            AudioStreamer(device_name="My Device")
        except TypeError:
            self.fail("AudioStreamer should accept a device_name argument")

    @patch("sounddevice.InputStream")
    async def test_audio_streamer_fast_path_default(self, mock_input_stream):
        """Verify that 'default' device uses the PortAudio fast-path (device=None)."""
        with patch("sounddevice.query_devices") as mock_query:
            streamer = AudioStreamer(device_name="default")
            await streamer.start()

            # Check if sd.InputStream was called with device=None (Fast-path)
            _, kwargs = mock_input_stream.call_args
            self.assertIsNone(kwargs.get("device"))

            # query_devices should NOT have been called for 'default' during _get_device_index
            # (Note: It IS called once in __init__ for cache initialization, but not during start)
            mock_query.reset_mock()
            await streamer.start()  # Already running, but just to show logic
            self.assertEqual(mock_query.call_count, 0)
            streamer.stop()

    @patch("sounddevice.InputStream")
    async def test_audio_streamer_caching(self, mock_input_stream):
        """Verify that device list is cached and not re-queried on every start."""
        mock_devices = [
            {"name": "My Mic", "max_input_channels": 1, "hostapi": 0},
        ]
        mock_hostapis = [{"name": "MME"}]

        with patch("sounddevice.query_devices", return_value=mock_devices) as mock_query:
            with patch("sounddevice.query_hostapis", return_value=mock_hostapis):
                streamer = AudioStreamer(device_name="My Mic")

                # First start: uses cache from __init__
                mock_query.reset_mock()
                await streamer.start()
                self.assertEqual(mock_query.call_count, 0)  # Should use cache
                streamer.stop()

    @patch("sounddevice.InputStream")
    async def test_audio_streamer_self_healing(self, mock_input_stream):
        """Verify 'Refresh on Failure' (Self-Healing) logic."""
        mock_devices_initial = [
            {"name": "Old Mic", "max_input_channels": 1, "hostapi": 0},
        ]
        mock_devices_new = [
            {"name": "New Mic", "max_input_channels": 1, "hostapi": 0},
        ]
        mock_hostapis = [{"name": "MME"}]

        # Setup: Streamer starts with 'Old Mic' in cache
        with patch("sounddevice.query_hostapis", return_value=mock_hostapis):
            with patch("sounddevice.query_devices", return_value=mock_devices_initial):
                streamer = AudioStreamer(device_name="New Mic")

                # Now, simulate that 'New Mic' is suddenly available
                # We mock InputStream to FAIL on the first call (stale/missing)
                # and SUCCEED on the second call (after refresh).
                mock_input_stream.side_effect = [
                    Exception("Device not found"),  # 1st attempt: Failure
                    MagicMock(),  # 2nd attempt: Success
                ]

                with patch("sounddevice.query_devices", return_value=mock_devices_new) as refresh:
                    await streamer.start()

                    # Verify that query_devices was called at least once to refresh
                    self.assertGreaterEqual(refresh.call_count, 1)

                    # Verify that start() succeeded in the end
                    self.assertTrue(streamer.is_running)
                    streamer.stop()

    @patch("sounddevice.InputStream")
    async def test_wasapi_guard_prevents_9984(self, mock_input_stream):
        """Verify that WasapiSettings are ONLY applied to WASAPI devices."""
        mock_devices = [
            {"name": "MME Mic", "max_input_channels": 1, "hostapi": 0},
            {"name": "WASAPI Mic", "max_input_channels": 1, "hostapi": 1},
        ]
        mock_hostapis = [{"name": "MME"}, {"name": "Windows WASAPI"}]

        with patch("sounddevice.query_devices", return_value=mock_devices):
            with patch("sounddevice.query_hostapis", return_value=mock_hostapis):
                # 1. Test MME Mic: Should NOT have extra_settings
                streamer_mme = AudioStreamer(device_name="MME Mic")
                await streamer_mme.start()
                _, kwargs_mme = mock_input_stream.call_args
                self.assertIsNone(kwargs_mme.get("extra_settings"))
                streamer_mme.stop()

                # 2. Test WASAPI Mic: SHOULD have extra_settings
                streamer_wasapi = AudioStreamer(device_name="WASAPI Mic")
                await streamer_wasapi.start()
                _, kwargs_wasapi = mock_input_stream.call_args
                self.assertIsNotNone(kwargs_wasapi.get("extra_settings"))
                streamer_wasapi.stop()


if __name__ == "__main__":
    unittest.main()
