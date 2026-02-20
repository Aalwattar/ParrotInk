from abc import ABC, abstractmethod
from typing import Callable, Optional, Union

from engine.audio.adapter import ProviderAudioSpec


class BaseProvider(ABC):
    """Abstract base class for transcription providers."""

    def __init__(
        self,
        api_key: str,
        on_partial: Callable[[str], None],
        on_final: Callable[[str], None],
        base_url: str,
        stop_timeout: float = 2.0,
        on_status: Optional[Callable[[str], None]] = None,
    ):
        self.api_key = api_key
        self.on_partial = on_partial
        self.on_final = on_final
        self.base_url = base_url
        self.stop_timeout = stop_timeout
        self.on_status = on_status

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

    async def stop(self):
        """
        Stop the transcription session with a mandatory timeout.
        """
        import asyncio

        from engine.logging import get_logger

        logger = get_logger("Provider")
        try:
            async with asyncio.timeout(self.stop_timeout):
                await self._do_stop()
        except TimeoutError:
            logger.warning(f"{self.get_type()} provider stop timed out (force killed).")
        except Exception as e:
            logger.error(f"Error stopping {self.get_type()} provider: {e}")

    @abstractmethod
    async def _do_stop(self):
        """Internal implementation of stop logic."""
        pass

    @abstractmethod
    async def send_audio(self, processed_chunk: Union[bytes, str], capture_time: float):
        """Send a pre-processed audio chunk (bytes or base64) for transcription."""
        pass
