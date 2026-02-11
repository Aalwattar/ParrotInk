import asyncio
import queue
import time
from typing import AsyncGenerator, Tuple

import numpy as np
import sounddevice as sd

from engine.logging import get_logger

logger = get_logger("Audio")


class AudioStreamer:
    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.queue: queue.Queue[Tuple[np.ndarray, float]] = queue.Queue()
        self.is_running = False
        self._stream: sd.InputStream | None = None

    def _callback(self, indata: np.ndarray, frames: int, time_info, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            logger.warning(f"Audio status warning: {status}")
        # Capture precise timestamp when audio block arrives
        capture_time = time.perf_counter()
        self.queue.put((indata.copy(), capture_time))

    def start(self):
        """Starts the audio capture stream."""
        if self.is_running:
            return

        # Clear any stale audio from previous sessions
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break

        # sounddevice starts a background thread for the callback.
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=self.chunk_size,
            callback=self._callback,
        )
        self._stream.start()
        self.is_running = True
        logger.info(f"Audio capture started at {self.sample_rate}Hz (chunk_size={self.chunk_size})")

    def stop(self):
        """Stops the audio capture stream."""
        if not self.is_running:
            return

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        self.is_running = False
        logger.info("Audio capture stopped.")

    def _normalize_audio(self, chunk: np.ndarray) -> np.ndarray:
        """Ensures audio is mono (1D array) by downmixing if necessary."""
        if chunk.ndim == 1:
            return chunk

        if chunk.ndim == 2:
            channels = chunk.shape[1]
            if channels > 1:
                # Downmix: average across channels to produce mono
                # We specify dtype to ensure we stay in float32
                return np.mean(chunk, axis=1, dtype=np.float32)
            else:
                # Squeeze (N, 1) to (N,)
                return chunk.squeeze()

        return chunk.flatten()

    async def async_generator(self) -> AsyncGenerator[Tuple[np.ndarray, float], None]:
        """Yields (audio_chunk, timestamp) tuples asynchronously without blocking the loop."""
        while self.is_running:
            try:
                # Non-blocking get
                chunk, capture_time = self.queue.get_nowait()
            except queue.Empty:
                # Important: Yield control to the event loop if queue is empty
                await asyncio.sleep(0.01)
                continue

            # Robust normalization (Mono + 1D)
            chunk = self._normalize_audio(chunk)

            # Debug log only if needed (commented out to reduce noise, or keep if crucial)
            # duration_ms = (len(chunk) / self.sample_rate) * 1000
            # logger.debug(f"Yielding audio chunk: {len(chunk)} samples ({duration_ms:.1f}ms)")

            yield chunk, capture_time
