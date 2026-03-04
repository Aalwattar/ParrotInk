import asyncio
import time
from typing import AsyncGenerator, Tuple, cast

import numpy as np
import sounddevice as sd

from engine.app_types import AudioHardwareError, CaptureFormatError
from engine.logging import get_logger

logger = get_logger("Audio")

# Internal Constants (Not exposed to user)
QUEUE_MAX_SIZE = 500
DROP_LOG_INTERVAL = 1.0
DEFAULT_DTYPE = "float32"


def downmix_stereo_to_mono(chunk: np.ndarray) -> np.ndarray:
    """Downmixes stereo (N, 2) to mono (N,) by averaging channels in float64."""
    if chunk.ndim == 2 and chunk.shape[1] > 1:
        # Average across channels using float64 to prevent precision loss/quantization noise
        return cast(np.ndarray, np.mean(chunk, axis=1, dtype=np.float64).astype(chunk.dtype))
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
        self.async_q: asyncio.Queue[Tuple[np.ndarray, float]] = asyncio.Queue(
            maxsize=QUEUE_MAX_SIZE
        )
        self.is_running = False
        self._stream: sd.InputStream | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._drop_count = 0
        self._last_drop_log = 0.0
        self.last_status = None

    def _callback(self, indata: np.ndarray, frames: int, time_info, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            # Store status instead of logging it to avoid thread contention
            self.last_status = status

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
            if now - self._last_drop_log > DROP_LOG_INTERVAL:
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
                if now - self._last_drop_log > DROP_LOG_INTERVAL:
                    logger.warning(
                        f"Audio queue full, dropping oldest chunks. "
                        f"Dropped total: {self._drop_count}"
                    )
                    self._last_drop_log = now
            except asyncio.QueueEmpty:
                pass

        self.async_q.put_nowait((chunk, capture_time))

    def _try_open_stream(self, sample_rate: int) -> sd.InputStream:
        """Helper to try mono, then stereo capture at a given sample rate."""
        chunk_size_adjusted = int(self.chunk_size * (sample_rate / self.sample_rate))
        try:
            stream = sd.InputStream(
                samplerate=sample_rate,
                channels=1,
                dtype=DEFAULT_DTYPE,
                blocksize=chunk_size_adjusted,
                callback=self._callback,
            )
            return stream
        except Exception as e:
            logger.debug(f"Mono capture at {sample_rate}Hz failed: {e}. Trying stereo...")
            try:
                stream = sd.InputStream(
                    samplerate=sample_rate,
                    channels=2,
                    dtype=DEFAULT_DTYPE,
                    blocksize=chunk_size_adjusted,
                    callback=self._callback,
                )
                logger.info(f"Stereo capture fallback at {sample_rate}Hz successful.")
                return stream
            except Exception as e2:
                raise e2

    def start(self, loop: asyncio.AbstractEventLoop | None = None):
        """Starts the audio capture stream with robust fallbacks."""
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

        rates_to_try = [self.sample_rate]
        if self.sample_rate not in (44100, 48000):
            rates_to_try.extend([44100, 48000])

        last_error = None
        for rate in rates_to_try:
            try:
                self._stream = self._try_open_stream(rate)
                break
            except Exception as e:
                logger.info(f"Failed to open audio stream at {rate}Hz: {e}")
                last_error = e

        if self._stream is None:
            err_msg = str(last_error) if last_error else "Unknown error"
            logger.error(f"All audio capture fallbacks failed. Last error: {err_msg}")
            raise AudioHardwareError(f"Could not open audio device. Error: {err_msg}")

        self._stream.start()
        self.is_running = True
        logger.info(
            f"Audio capture started at {self._stream.samplerate}Hz "
            f"(channels={self._stream.channels})"
        )

    def stop(self):
        """Stops the audio capture stream."""
        if not self.is_running:
            return

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        self.is_running = False

        # Unblock any waiting consumers
        if self._loop:
            self._loop.call_soon_threadsafe(self.async_q.put_nowait, (None, 0.0))

        self._loop = None
        logger.info("Audio capture stopped.")

    async def async_generator(self) -> AsyncGenerator[Tuple[np.ndarray, float], None]:
        """Yields (audio_chunk, timestamp) tuples asynchronously."""
        while self.is_running:
            try:
                # Use await to avoid busy-waiting
                item = await self.async_q.get()

                # Check for sentinel
                if item[0] is None:
                    break

                yield item
            except asyncio.CancelledError:
                break
