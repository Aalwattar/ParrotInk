from typing import Callable
from .base import BaseProvider
from .openai_provider import OpenAIProvider
from .assemblyai_provider import AssemblyAIProvider
from engine.config import Config

class TranscriptionFactory:
    """Factory for creating transcription providers."""

    @staticmethod
    def create(config: Config, on_partial: Callable[[str], None], on_final: Callable[[str], None]) -> BaseProvider:
        if config.active_provider == "openai":
            return OpenAIProvider(
                api_key=config.openai_api_key,
                on_partial=on_partial,
                on_final=on_final
            )
        elif config.active_provider == "assemblyai":
            return AssemblyAIProvider(
                api_key=config.assemblyai_api_key,
                on_partial=on_partial,
                on_final=on_final,
                sample_rate=config.transcription.sample_rate
            )
        else:
            raise ValueError(f"Unsupported transcription provider: {config.active_provider}")
