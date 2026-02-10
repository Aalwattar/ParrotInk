from typing import Callable
from .base import BaseProvider
from .openai_provider import OpenAIProvider
from .assemblyai_provider import AssemblyAIProvider
from engine.config import Config

class TranscriptionFactory:
    """Factory for creating transcription providers."""

    @staticmethod
    def create(config: Config, on_partial: Callable[[str], None], on_final: Callable[[str], None]) -> BaseProvider:
        if config.default_provider == "openai":
            # Resolve URL based on test mode
            base_url = config.test.openai_mock_url if config.test.enabled else config.advanced.openai_url
            
            return OpenAIProvider(
                api_key=config.get_openai_key() or "",
                on_partial=on_partial,
                on_final=on_final,
                base_url=base_url
            )
        elif config.default_provider == "assemblyai":
            # Resolve URL based on test mode
            base_url = config.test.assemblyai_mock_url if config.test.enabled else config.advanced.assemblyai_url
            
            return AssemblyAIProvider(
                api_key=config.get_assemblyai_key() or "",
                on_partial=on_partial,
                on_final=on_final,
                base_url=base_url,
                sample_rate=config.transcription.sample_rate
            )
        else:
            raise ValueError(f"Unsupported transcription provider: {config.default_provider}")
