from abc import ABC, abstractmethod
from typing import Callable, Union

from engine.audio.adapter import ProviderAudioSpec


class BaseProvider(ABC):
    """Abstract base class for transcription providers."""

    def __init__(
        self,
        api_key: str,
        on_partial: Callable[[str], None],
        on_final: Callable[[str], None],
        base_url: str,
    ):
        self.api_key = api_key
        self.on_partial = on_partial
        self.on_final = on_final
        self.base_url = base_url

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Return whether the provider session is currently active."""
        pass

    @abstractmethod
    def get_audio_spec(self) -> ProviderAudioSpec:
        """Return the audio specification required by this provider."""
        pass

    @abstractmethod
    def get_type(self) -> str:
        """Return the type identifier for this provider."""
        pass

    @abstractmethod
    async def start(self):
        """Start the transcription session."""
        pass

    @abstractmethod
    async def stop(self):
        """Stop the transcription session."""
        pass

    @abstractmethod
    async def send_audio(self, processed_chunk: Union[bytes, str], capture_time: float):
        """Send a pre-processed audio chunk (bytes or base64) for transcription."""
        pass
