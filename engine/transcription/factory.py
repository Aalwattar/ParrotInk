from typing import Callable, Optional

from engine.config import Config
from engine.config_resolver import resolve_effective_config

from .assemblyai_provider import AssemblyAIProvider
from .base import BaseProvider
from .openai_provider import OpenAIProvider


class TranscriptionFactory:
    """Factory for creating transcription providers."""

    @staticmethod
    def create(
        config: Config,
        on_partial: Callable[[str], None],
        on_final: Callable[[str], None],
        on_status: Optional[Callable[[str], None]] = None,
    ) -> BaseProvider:
        effective = resolve_effective_config(config)

        if effective.provider_type == "openai":
            return OpenAIProvider(
                api_key=config.get_openai_key() or "",
                on_partial=on_partial,
                on_final=on_final,
                effective_config=effective.openai,
                on_status=on_status,
            )
        elif effective.provider_type == "assemblyai":
            return AssemblyAIProvider(
                api_key=config.get_assemblyai_key() or "",
                on_partial=on_partial,
                on_final=on_final,
                effective_config=effective.assemblyai,
                on_status=on_status,
            )
        else:
            raise ValueError(f"Unsupported transcription provider: {effective.provider_type}")
