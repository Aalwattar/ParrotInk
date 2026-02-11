from typing import Callable

from engine.config import Config

from .assemblyai_provider import AssemblyAIProvider
from .base import BaseProvider
from .openai_provider import OpenAIProvider


class TranscriptionFactory:
    """Factory for creating transcription providers."""

    @staticmethod
    def create(
        config: Config, on_partial: Callable[[str], None], on_final: Callable[[str], None]
    ) -> BaseProvider:
        if config.default_provider == "openai":
            return OpenAIProvider(
                api_key=config.get_openai_key() or "",
                on_partial=on_partial,
                on_final=on_final,
                config=config,
            )
        elif config.default_provider == "assemblyai":
            return AssemblyAIProvider(
                api_key=config.get_assemblyai_key() or "",
                on_partial=on_partial,
                on_final=on_final,
                config=config,
            )
        else:
            raise ValueError(f"Unsupported transcription provider: {config.default_provider}")
