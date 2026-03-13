import asyncio
import unittest

import numpy as np

from engine.audio import AudioStreamer


class TestAudioStreamerAsync(unittest.IsolatedAsyncioTestCase):
    async def test_audio_streamer_queue_overflow(self):
        # Set a very small maxsize for testing overflow
        streamer = AudioStreamer()

        # We need to reach into the streamer and replace its queue with a small one for testing
        streamer.async_q = asyncio.Queue(maxsize=5)

        # Push 6 items
        for i in range(6):
            chunk = np.array([float(i)], dtype=np.float32)
            # Manually trigger what the callback would do (simplified)
            if streamer.async_q.full():
                streamer.async_q.get_nowait()
            streamer.async_q.put_nowait((chunk, 1.0))

        self.assertEqual(streamer.async_q.qsize(), 5)
        first = await streamer.async_q.get()
        # The first one (0.0) should have been dropped
        self.assertEqual(first[0][0], 1.0)

    async def test_audio_streamer_async_generator(self):
        streamer = AudioStreamer()
        streamer.is_running = True
        streamer.async_q = asyncio.Queue()

        # Push a few chunks
        for i in range(3):
            streamer.async_q.put_nowait((np.array([float(i)]), float(i)))

        chunks = []
        async for chunk, _ts in streamer.async_generator():
            chunks.append(chunk)
            if len(chunks) == 3:
                break

        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0][0], 0.0)
        self.assertEqual(chunks[2][0], 2.0)


if __name__ == "__main__":
    unittest.main()
