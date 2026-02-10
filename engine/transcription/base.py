from abc import ABC, abstractmethod
from typing import AsyncGenerator, Callable
import numpy as np

class BaseProvider(ABC):
    """Abstract base class for transcription providers."""

    def __init__(self, api_key: str, on_partial: Callable[[str], None], on_final: Callable[[str], None]):
        self.api_key = api_key
        self.on_partial = on_partial
        self.on_final = on_final

    @abstractmethod
    async def start(self):
        """Start the transcription session."""
        pass

    @abstractmethod
    async def stop(self):
        """Stop the transcription session."""
        pass

    @abstractmethod
    async def send_audio(self, audio_chunk: np.ndarray):
        """Send an audio chunk for transcription."""
        pass
