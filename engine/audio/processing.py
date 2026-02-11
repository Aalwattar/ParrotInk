from typing import cast

import numpy as np
import soxr  # type: ignore


def scale_and_clip_to_int16(chunk: np.ndarray) -> np.ndarray:
    """
    Converts audio chunk to int16 PCM.
    If input is float, scales [-1.0, 1.0] to [-32767, 32767] and clips.
    If input is int, clips to int16 range to avoid wraparound.
    """
    if np.issubdtype(chunk.dtype, np.floating):
        # Scale float to int16 range
        scaled = chunk * 32767.0
        return np.clip(scaled, -32768, 32767).astype(np.int16)
    else:
        # Just clip to int16 range
        return cast(np.ndarray, np.clip(chunk, -32768, 32767).astype(np.int16))


class Resampler:
    def __init__(self, source_rate: int, target_rate: int):
        self.source_rate = source_rate
        self.target_rate = target_rate
        # python-soxr uses ResampleStream for stateful resampling
        self._stream = soxr.ResampleStream(source_rate, target_rate, 1, "float32")

    def resample(self, chunk: np.ndarray) -> np.ndarray:
        """Resamples audio chunk. Input must be float32 1D array."""
        if chunk.dtype != np.float32:
            chunk = chunk.astype(np.float32)

        # ResampleStream.resample_chunk handles the state
        return cast(np.ndarray, self._stream.resample_chunk(chunk))

    def close(self):
        """Releases the soxr stream resources."""
        self._stream = None


class HighPassFilter:
    """A simple one-pole high-pass filter to remove DC offset and rumble."""

    def __init__(self, cutoff_hz: float = 80.0, sample_rate: int = 16000):
        # alpha = RC / (RC + dt)
        rc = 1.0 / (2.0 * np.pi * cutoff_hz)
        dt = 1.0 / sample_rate
        self.alpha = rc / (rc + dt)
        self.prev_x = 0.0
        self.prev_y = 0.0

    def process(self, chunk: np.ndarray) -> np.ndarray:
        """Applies the HPF to a 1D audio chunk."""
        out = np.zeros_like(chunk)
        for i in range(len(chunk)):
            out[i] = self.alpha * (self.prev_y + chunk[i] - self.prev_x)
            self.prev_x = chunk[i]
            self.prev_y = out[i]
        return out
