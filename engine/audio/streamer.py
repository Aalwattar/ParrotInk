import asyncio
import time
from typing import AsyncGenerator, Tuple, cast

import numpy as np
import sounddevice as sd

from engine.logging import get_logger
from engine.types import CaptureFormatError

logger = get_logger("Audio")


def downmix_stereo_to_mono(chunk: np.ndarray) -> np.ndarray:
    """Downmixes stereo (N, 2) to mono (N,) by averaging channels."""
    if chunk.ndim == 2 and chunk.shape[1] > 1:
        # Average across channels. Specify dtype to maintain precision.
        return cast(np.ndarray, np.mean(chunk, axis=1, dtype=chunk.dtype))
    return chunk


def reshape_to_1d(chunk: np.ndarray) -> np.ndarray:
    """Flattens (N, 1) to (N,) or leaves (N,) as is."""
    if chunk.ndim == 2 and chunk.shape[1] == 1:
        return chunk.squeeze(axis=1)
    return chunk


def sanitize_nan_inf(chunk: np.ndarray) -> np.ndarray:
    """Replaces NaN and Inf values with 0.0."""
    if np.issubdtype(chunk.dtype, np.floating):
        mask = ~np.isfinite(chunk)
        if np.any(mask):
            chunk = chunk.copy()
            chunk[mask] = 0.0
    return chunk


def check_audio_invariants(chunk: np.ndarray) -> None:
    """Verifies that audio data meets basic dimensionality and type requirements."""
    if not np.issubdtype(chunk.dtype, np.number):
        raise CaptureFormatError(f"Non-numeric audio data: {chunk.dtype}")

    if chunk.ndim > 2:
        raise CaptureFormatError(f"Invalid dimensionality: {chunk.ndim}D (max 2D allowed)")


class AudioStreamer:
    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.async_q: asyncio.Queue[Tuple[np.ndarray, float]] = asyncio.Queue(maxsize=100)
        self.is_running = False
        self._stream: sd.InputStream | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._drop_count = 0
        self._last_drop_log = 0.0

    def _callback(self, indata: np.ndarray, frames: int, time_info, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            logger.warning(f"Audio status warning: {status}")

        capture_time = time.perf_counter()

        # Apply boundary invariants immediately
        try:
            chunk = indata.copy()
            check_audio_invariants(chunk)
            chunk = downmix_stereo_to_mono(chunk)
            chunk = reshape_to_1d(chunk)
            chunk = sanitize_nan_inf(chunk)
        except CaptureFormatError as e:
            logger.error(f"Capture format error: {e}")
            return
        except Exception as e:
            logger.error(f"Unexpected error in audio callback: {e}")
            return

        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._push_to_queue, chunk, capture_time)
        else:
            self._drop_count += 1
            now = time.time()
            if now - self._last_drop_log > 1.0:
                logger.warning(
                    f"Audio capture dropping chunks: event loop unavailable. "
                    f"Dropped so far: {self._drop_count}"
                )
                self._last_drop_log = now

    def _push_to_queue(self, chunk: np.ndarray, capture_time: float):
        """Internal helper to push data into the async queue with 'Drop Oldest' policy."""
        if self.async_q.full():
            try:
                self.async_q.get_nowait()
                self._drop_count += 1
                now = time.time()
                if now - self._last_drop_log > 1.0:
                    logger.warning(
                        f"Audio queue full, dropping oldest chunks. "
                        f"Dropped total: {self._drop_count}"
                    )
                    self._last_drop_log = now
            except asyncio.QueueEmpty:
                pass

        self.async_q.put_nowait((chunk, capture_time))

    def start(self, loop: asyncio.AbstractEventLoop | None = None):
        """Starts the audio capture stream."""
        if self.is_running:
            return

        self._loop = loop or asyncio.get_event_loop()

        # Clear any stale audio
        while not self.async_q.empty():
            try:
                self.async_q.get_nowait()
            except asyncio.QueueEmpty:
                break

        self._drop_count = 0
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,  # Default to 1, callback handles downmixing if device is stereo
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
        self._loop = None
        logger.info("Audio capture stopped.")

    def _normalize_audio(self, chunk: np.ndarray) -> np.ndarray:
        """DEPRECATED: Normalization now happens at the capture boundary."""
        return chunk

    async def async_generator(self) -> AsyncGenerator[Tuple[np.ndarray, float], None]:
        """Yields (audio_chunk, timestamp) tuples asynchronously."""
        while self.is_running or not self.async_q.empty():
            try:
                chunk, capture_time = self.async_q.get_nowait()
                yield chunk, capture_time
            except asyncio.QueueEmpty:
                if not self.is_running:
                    break
                await asyncio.sleep(0.01)
