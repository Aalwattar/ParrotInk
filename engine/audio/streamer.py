import asyncio
import time
from typing import AsyncGenerator, Optional, Tuple, cast

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
    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        device_name: Optional[str] = None,
    ):
        self.sample_rate = sample_rate

        self.chunk_size = chunk_size
        self.device_name = device_name
        self.async_q: asyncio.Queue[Tuple[np.ndarray, float]] = asyncio.Queue(
            maxsize=QUEUE_MAX_SIZE
        )
        self.is_running = False
        self._stream: sd.InputStream | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._drop_count = 0
        self._last_drop_log = 0.0
        self.last_status = None

        # Senior Optimization: Cache device indices to avoid expensive re-scans.
        self._cached_devices: list = []
        self._cached_hostapis: list = []
        self._wasapi_index: int = -1
        self.refresh_devices()

    def refresh_devices(self):
        """Refreshes the internal cache of audio devices and host APIs."""
        try:
            self._cached_devices = list(sd.query_devices())
            self._cached_hostapis = list(sd.query_hostapis())
            self._wasapi_index = -1
            for i, api in enumerate(self._cached_hostapis):
                if api["name"] == "Windows WASAPI":
                    self._wasapi_index = i
                    break
            logger.debug(
                f"Audio device cache refreshed. Found {len(self._cached_devices)} devices."
            )
        except Exception as e:
            logger.warning(f"Failed to refresh audio device cache: {e}")

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

    def _get_device_index(self, force_refresh: bool = False) -> Optional[int]:
        """Finds the device index based on the configured device name using the cache."""
        if not self.device_name or self.device_name.lower() == "default":
            # Fast-Path: PortAudio handles "None" as the system default instantly.
            return None

        if force_refresh:
            logger.info(f"Forcing audio device cache refresh for '{self.device_name}'...")
            self.refresh_devices()

        def _find_in_list(devices: list) -> Optional[int]:
            # 1. Try exact match on name + WASAPI preference
            for i, d in enumerate(devices):
                if d["name"] == self.device_name and d["max_input_channels"] > 0:
                    if self._wasapi_index != -1 and d["hostapi"] == self._wasapi_index:
                        return i

            # 2. Try substring match + WASAPI preference
            for i, d in enumerate(devices):
                if self.device_name.lower() in d["name"].lower() and d["max_input_channels"] > 0:
                    if self._wasapi_index != -1 and d["hostapi"] == self._wasapi_index:
                        return i

            # 3. Fallback: Try exact match on name (any host API)
            for i, d in enumerate(devices):
                if d["name"] == self.device_name and d["max_input_channels"] > 0:
                    return i

            # 4. Fallback: Try substring match (any host API)
            for i, d in enumerate(devices):
                if self.device_name.lower() in d["name"].lower() and d["max_input_channels"] > 0:
                    return i
            return None

        # 1. Try finding in cache
        idx = _find_in_list(self._cached_devices)
        if idx is not None:
            return idx

        # 2. Fallback: Refresh cache and try again
        if not force_refresh:
            logger.info(f"Device '{self.device_name}' not in cache. Refreshing...")
            self.refresh_devices()
            return _find_in_list(self._cached_devices)

        return None

    def _try_open_stream(self, sample_rate: int) -> sd.InputStream:
        """Helper to try mono, then stereo capture at a given sample rate."""
        chunk_size_adjusted = int(self.chunk_size * (sample_rate / self.sample_rate))

        # We try opening the stream. If it fails once, we refresh cache and try one more time.
        last_exception = None
        for attempt in range(2):
            force_refresh = attempt > 0
            device_index = self._get_device_index(force_refresh=force_refresh)

            if device_index is not None:
                logger.info(
                    f"Using specific audio device: {self.device_name} (Index: {device_index})"
                )

            # Senior Architecture: Mitigate 'Communication Ducking' by using WASAPI Shared mode.
            extra_settings = None
            try:
                # If no device_index, we need to know what the default device actually is
                # to check its Host API.
                target_idx = device_index if device_index is not None else sd.default.device[0]

                # Use cache if possible for performance
                devices = self._cached_devices if self._cached_devices else list(sd.query_devices())
                host_apis = (
                    self._cached_hostapis if self._cached_hostapis else list(sd.query_hostapis())
                )

                if target_idx is not None and 0 <= target_idx < len(devices):
                    device_info = devices[target_idx]
                    host_api_idx = device_info.get("hostapi")

                    if host_api_idx is not None and 0 <= host_api_idx < len(host_apis):
                        host_api_name = host_apis[host_api_idx]["name"]
                        if host_api_name == "Windows WASAPI":
                            extra_settings = sd.WasapiSettings(exclusive=False, auto_convert=True)
                            logger.debug("Applying WASAPI Shared Mode settings.")
                        else:
                            logger.debug(
                                f"Not applying WASAPI settings for host API: {host_api_name}"
                            )
            except (AttributeError, Exception) as e:
                logger.debug(f"Skipping WASAPI settings: {e}")
                pass

            try:
                stream = sd.InputStream(
                    samplerate=sample_rate,
                    channels=1,
                    device=device_index,
                    dtype=DEFAULT_DTYPE,
                    blocksize=chunk_size_adjusted,
                    callback=self._callback,
                    extra_settings=extra_settings,
                )
                return stream
            except Exception as e:
                logger.debug(
                    f"Mono capture at {sample_rate}Hz failed on attempt {attempt + 1}: {e}"
                )
                last_exception = e
                # If first attempt, retry with fresh cache.
                # If second attempt, fall through to try stereo.
                if not force_refresh:
                    continue

                # If we're here, it's the second attempt and mono still failed. Try stereo.
                try:
                    stream = sd.InputStream(
                        samplerate=sample_rate,
                        channels=2,
                        device=device_index,
                        dtype=DEFAULT_DTYPE,
                        blocksize=chunk_size_adjusted,
                        callback=self._callback,
                        extra_settings=extra_settings,
                    )
                    logger.info(f"Stereo capture fallback at {sample_rate}Hz successful.")
                    return stream
                except Exception as e2:
                    last_exception = e2
                    break  # Give up on this sample rate

        raise last_exception

    async def start(self, loop: asyncio.AbstractEventLoop | None = None):
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

        # Senior Architecture: Thread Isolation
        # Opening a PortAudio stream can be a slow, blocking call that hangs the UI/Hotkey thread.
        # We run it in a background thread to ensure responsiveness.
        def _open_and_start():
            rates_to_try = [self.sample_rate]
            if self.sample_rate not in (44100, 48000):
                rates_to_try.extend([44100, 48000])

            last_error = None
            for rate in rates_to_try:
                try:
                    # Guard against ZeroDivisionError just in case
                    if self.sample_rate == 0:
                        self.sample_rate = rate

                    self._stream = self._try_open_stream(rate)
                    if rate != self.sample_rate:
                        self.chunk_size = int(self.chunk_size * (rate / self.sample_rate))
                        self.sample_rate = rate
                    break
                except Exception as e:
                    logger.info(f"Failed to open audio stream at {rate}Hz: {e}")
                    last_error = e

            if self._stream is None:
                err_msg = str(last_error) if last_error else "Unknown error"
                logger.error(f"All audio capture fallbacks failed. Last error: {err_msg}")
                raise AudioHardwareError(f"Could not open audio device. Error: {err_msg}")

            self._stream.start()

        # Run the blocking open/start in an executor
        await self._loop.run_in_executor(None, _open_and_start)
        self.is_running = True

        if self._stream:
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
