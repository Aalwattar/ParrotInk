from dataclasses import replace
from typing import Callable, Optional

from engine.app_types import TranscriptionError
from engine.config import Config
from engine.config_resolver import resolve_effective_config

from .assemblyai_provider import AssemblyAIProvider
from .base import BaseProvider
from .cloudflare_provider import CloudflareProvider
from .grok_provider import GrokProvider
from .openai_provider import OpenAIProvider
from .speaker_manager import SpeakerManager


class TranscriptionFactory:
    """Factory for creating transcription providers."""

    @staticmethod
    def create(
        config: Config,
        on_partial: Callable[[str], None],
        on_final: Callable[[str], None],
        on_status: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[TranscriptionError], None]] = None,
        speaker_manager: Optional[SpeakerManager] = None,
    ) -> BaseProvider:
        effective = resolve_effective_config(config)

        if effective.provider_type == "openai":
            return OpenAIProvider(
                api_key=config.get_openai_key() or "",
                on_partial=on_partial,
                on_final=on_final,
                effective_config=effective.openai,
                on_status=on_status,
                on_error=on_error,
            )
        elif effective.provider_type == "assemblyai":
            return AssemblyAIProvider(
                api_key=config.get_assemblyai_key() or "",
                on_partial=on_partial,
                on_final=on_final,
                effective_config=effective.assemblyai,
                on_status=on_status,
                on_error=on_error,
                speaker_manager=speaker_manager,
            )
        elif effective.provider_type == "cloudflare":
            cfg = effective.cloudflare
            if cfg is None:
                raise ValueError("Cloudflare configuration is missing")
            core = config.providers.cloudflare.core
            if not config.test.enabled and not core.account_id:
                raise ValueError("Configure your Cloudflare account ID in Gateway settings")
            token = config.get_cloudflare_key() or ""
            if cfg.protocol == "grok_stt":
                return GrokProvider(
                    token, on_partial, on_final, cfg, on_status=on_status, on_error=on_error
                )
            if cfg.protocol == "openai":
                headers = {
                    "cf-aig-authorization": f"Bearer {token}",
                    "cf-aig-collect-log-payload": "false",
                }
                if not core.use_byok:
                    upstream_key = config.get_openai_key()
                    if not upstream_key and not config.test.enabled:
                        raise ValueError("Set an OpenAI key, or enable Gateway BYOK")
                    headers["Authorization"] = f"Bearer {upstream_key or ''}"
                openai_cfg = replace(
                    effective.openai,
                    url=cfg.url,
                    transcription_model=cfg.model.removeprefix("openai/"),
                    languages=tuple([core.language])
                    if core.language
                    else effective.openai.languages,
                    headers=headers,
                    provider_id="cloudflare",
                )
                return OpenAIProvider(token, on_partial, on_final, openai_cfg, on_status, on_error)
            return CloudflareProvider(
                token, on_partial, on_final, cfg, on_status=on_status, on_error=on_error
            )
        else:
            raise ValueError(f"Unsupported transcription provider: {effective.provider_type}")
