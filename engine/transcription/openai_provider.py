import asyncio
import json
from typing import Callable, Optional, Union

import websockets.asyncio.client
from websockets.asyncio.client import ClientConnection

from engine.app_types import EffectiveOpenAIConfig
from engine.audio.adapter import ProviderAudioSpec
from engine.logging import get_logger

from .base import BaseProvider

logger = get_logger("OpenAI")


class OpenAIProvider(BaseProvider):
    """
    OpenAI Realtime API Provider optimized for transcription.
    """

    def __init__(
        self,
        api_key: str,
        on_partial: Callable[[str], None],
        on_final: Callable[[str], None],
        effective_config: EffectiveOpenAIConfig,
    ):
        super().__init__(api_key, on_partial, on_final, "")
        self.effective_config = effective_config
        self.url = effective_config.url
        self.ws: Optional[ClientConnection] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._is_running = False
        self.current_transcript = ""

    @property
    def is_running(self) -> bool:
        return self._is_running

    def get_audio_spec(self) -> ProviderAudioSpec:
        # OpenAI Realtime requires PCM16 Mono at 24kHz
        return ProviderAudioSpec(
            sample_rate_hz=24000,
            wire_encoding="pcm16_base64",
        )

    def get_type(self) -> str:
        return "openai"

    async def start(self):
        """Connect and configure the session."""
        from engine.security import SecurityManager

        # Security Strategy: Only send the API key if the URL is trusted.
        # This prevents credential leak to malicious endpoints in config.
        is_trusted = SecurityManager.is_url_trusted(
            self.url, extra_trusted=self.effective_config.trusted_domains
        )
        is_test = self.effective_config.is_test

        if not is_trusted and not is_test:
            logger.error(f"Refusing to connect to untrusted endpoint: {self.url}")
            raise ConnectionError(f"Untrusted transcription endpoint: {self.url}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            from urllib.parse import urlparse

            parsed = urlparse(self.url)
            logger.info(f"Connecting to OpenAI Realtime Host: {parsed.netloc}")
        except Exception:
            logger.info(f"Connecting to OpenAI at {self.url}...")

        try:
            self.ws = await websockets.connect(
                self.url, additional_headers=headers if not is_test else None
            )
            self._is_running = True
            self._receive_task = asyncio.create_task(self._receive_loop())

            # Configure session
            await self._update_session()
            logger.info("Connected to OpenAI successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to OpenAI: {e}")
            raise

    async def _update_session(self):
        """Send the session.update configuration for a transcription session."""
        if not self.ws:
            return

        cfg = self.effective_config

        # Build session.update using the nested Transcription Session Object shape
        # session.type is REQUIRED for transcription-only sessions via session.update
        update_event = {
            "type": "session.update",
            "session": {
                "type": "transcription",
                "audio": {
                    "input": {
                        "format": {"type": "audio/pcm", "rate": 24000},
                        "transcription": {
                            "model": cfg.transcription_model,
                            "language": cfg.language,
                            "prompt": cfg.prompt,
                        },
                        "turn_detection": {
                            "type": cfg.turn_detection_type,
                            "threshold": cfg.vad_threshold,
                            "prefix_padding_ms": cfg.prefix_padding_ms,
                            "silence_duration_ms": cfg.silence_duration_ms,
                        },
                    }
                },
            },
        }

        # Handle noise reduction in the nested structure
        # Explicitly set to None (null in JSON) if disabled
        if cfg.noise_reduction_type and cfg.noise_reduction_type != "off":
            update_event["session"]["audio"]["input"]["noise_reduction"] = {
                "type": cfg.noise_reduction_type
            }
        else:
            update_event["session"]["audio"]["input"]["noise_reduction"] = None

        logger.debug(f"Sending session.update: {json.dumps(update_event)}")
        await self.ws.send(json.dumps(update_event))

    async def _do_stop(self):
        """Graceful shutdown."""
        self._is_running = False
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self.ws:
            try:
                await self.ws.close()
            finally:
                self.ws = None
        logger.info("Disconnected from OpenAI.")

    async def send_audio(self, processed_chunk: Union[bytes, str], capture_time: float):
        """Send audio via input_audio_buffer.append."""
        if not self.ws or not self._is_running:
            return

        event = {"type": "input_audio_buffer.append", "audio": processed_chunk}
        try:
            await self.ws.send(json.dumps(event))
        except Exception as e:
            logger.error(f"Error sending audio to OpenAI: {e}")
            self._is_running = False

    async def _receive_loop(self):
        """Handle incoming server events."""
        try:
            async for message in self.ws:
                logger.debug(f"Received OpenAI message: {message}")
                event = json.loads(message)
                await self._handle_event(event)
        except Exception as e:
            if self._is_running:
                logger.error(f"Error in OpenAI receive loop: {e}")
                self._is_running = False

    async def _handle_event(self, event: dict):
        """Route transcription events."""
        ev_type = event.get("type")

        # Support both prefixed and non-prefixed transcription events
        if ev_type in (
            "conversation.item.input_audio_transcription.delta",
            "input_audio_transcription.delta",
        ):
            delta = event.get("delta")
            if delta:
                logger.debug(f"OpenAI Delta: len={len(delta)}")
                self.current_transcript += delta
                self.on_partial(self.current_transcript)

        elif ev_type in (
            "conversation.item.input_audio_transcription.completed",
            "input_audio_transcription.completed",
        ):
            transcript = event.get("transcript")
            if transcript:
                # Senior Privacy Implementation: Lower level and use key for redaction
                logger.debug(f'OpenAI Final Segment: {{"transcript": "{transcript.strip()}"}}')
                self.on_final(transcript.strip())
            self.current_transcript = ""

        elif ev_type == "error":
            logger.error(f"OpenAI API Error: {event.get('error')}")

        elif ev_type == "session.updated":
            logger.info("OpenAI: Transcription session updated successfully.")
