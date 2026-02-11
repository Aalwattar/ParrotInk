import base64
from dataclasses import dataclass
from typing import Literal, Union

import numpy as np

from engine.audio.processing import Resampler, scale_and_clip_to_int16


@dataclass
class ProviderAudioSpec:
    sample_rate_hz: int
    channels: int = 1
    bit_depth: int = 16
    wire_encoding: Literal["pcm16_bytes", "pcm16_base64"] = "pcm16_bytes"
    preferred_chunk_ms: int = 100


class AudioAdapter:
    def __init__(self, capture_rate_hz: int, provider_spec: ProviderAudioSpec):
        self.capture_rate_hz = capture_rate_hz
        self.spec = provider_spec

        self._resampler = None
        if capture_rate_hz != provider_spec.sample_rate_hz:
            self._resampler = Resampler(capture_rate_hz, provider_spec.sample_rate_hz)

    def process(self, chunk: np.ndarray) -> Union[bytes, str]:
        """
        Transforms raw capture chunk (float32 or int16) into provider-ready format.
        1. Resample if necessary.
        2. Convert to int16 PCM.
        3. Encode (bytes or base64).
        """
        # 1. Resample (must be done in float for best quality)
        if self._resampler:
            # Resampler expects float32
            if chunk.dtype != np.float32:
                chunk = chunk.astype(np.float32)
            chunk = self._resampler.resample(chunk)

        # 2. Convert to int16
        pcm16 = scale_and_clip_to_int16(chunk)

        # 3. Encode
        raw_bytes = pcm16.tobytes()

        if self.spec.wire_encoding == "pcm16_base64":
            return base64.b64encode(raw_bytes).decode("ascii")

        return raw_bytes
