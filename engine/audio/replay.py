from __future__ import annotations

import asyncio
import time
import wave
from pathlib import Path
from typing import AsyncGenerator, Optional, Tuple

import numpy as np

from engine.logging import get_logger

logger = get_logger("WavReplay")


class WavReplayer:
    """
    Reads a 16-bit PCM WAV file and yields chunks to simulate real-time capture.
    Supports mono downmixing of multi-channel files.
    """

    def __init__(self, file_path: str | Path, chunk_ms: int = 100):
        self.file_path = Path(file_path)
        self.chunk_ms = chunk_ms
        self._wav: Optional[wave.Wave_read] = None

    def _open(self) -> wave.Wave_read:
        if not self.file_path.exists():
            raise FileNotFoundError(f"WAV file not found: {self.file_path}")

        wr = wave.open(str(self.file_path), "rb")

        # Validate format
        if wr.getsampwidth() != 2:
            wr.close()
            raise ValueError(
                f"Only 16-bit PCM WAV is supported (found {wr.getsampwidth() * 8}-bit)"
            )

        return wr

    async def async_generator(self) -> AsyncGenerator[Tuple[np.ndarray, float], None]:
        """
        Yields (chunk, timestamp) pairs, pacing them to real-time.
        """
        wr = self._open()
        try:
            n_channels = wr.getnchannels()
            sample_rate = wr.getframerate()

            # frames per chunk
            chunk_size = (sample_rate * self.chunk_ms) // 1000

            logger.info(
                f"Replaying {self.file_path.name}: {sample_rate}Hz, "
                f"{n_channels} channels, {self.chunk_ms}ms chunks"
            )

            start_time = time.time()
            total_frames_sent = 0

            while True:
                data = wr.readframes(chunk_size)
                if not data:
                    break

                # Convert to numpy int16
                chunk = np.frombuffer(data, dtype=np.int16)

                # Reshape to (frames, channels)
                if n_channels > 1:
                    chunk = chunk.reshape(-1, n_channels)
                    # Downmix to mono (average across channels)
                    # We use float32 for averaging to avoid overflow before clipping back
                    chunk = chunk.astype(np.float32).mean(axis=1).astype(np.int16)

                # Ensure it's 1D float32 for the existing pipeline
                # (engine expects float32 from streamer)
                # Note: AppCoordinator normally gets float32 from sounddevice.
                chunk_f32 = chunk.astype(np.float32) / 32768.0

                total_frames_sent += len(chunk)
                current_timestamp = total_frames_sent / sample_rate

                # Yield the chunk
                yield chunk_f32, current_timestamp

                # Pacing
                elapsed = time.time() - start_time
                target_elapsed = total_frames_sent / sample_rate
                if target_elapsed > elapsed:
                    await asyncio.sleep(target_elapsed - elapsed)

        finally:
            wr.close()
