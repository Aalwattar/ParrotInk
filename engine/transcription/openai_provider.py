import asyncio
import json
from typing import Callable, Optional, Union

import websockets.asyncio.client
from websockets.asyncio.client import ClientConnection

from engine.audio.adapter import ProviderAudioSpec
from engine.config import Config
from engine.logging import get_logger

from .base import BaseProvider

logger = get_logger("OpenAI")


class OpenAIProvider(BaseProvider):
    """
    OpenAI Realtime API Provider optimized for transcription.
    Migrated to session.update with nested audio.input schema.
    """

    def __init__(
        self,
        api_key: str,
        on_partial: Callable[[str], None],
        on_final: Callable[[str], None],
        config: Config,
    ):
        super().__init__(api_key, on_partial, on_final, "")
        self.config = config
        self.url = self._build_url()
        self.ws: Optional[ClientConnection] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._is_running = False
        self.current_transcript = ""

    @property
    def is_running(self) -> bool:
        return self._is_running

    def get_audio_spec(self) -> ProviderAudioSpec:
        # OpenAI Realtime requires PCM16 Mono
        return ProviderAudioSpec(
            sample_rate_hz=self.config.providers.openai.core.input_audio_rate,
            wire_encoding="pcm16_base64",
        )

    def get_type(self) -> str:
        return "openai"

    def _build_url(self) -> str:
        if self.config.test.enabled:
            return self.config.test.openai_mock_url
        # Intent=transcription is still required in the URL for this flow
        return f"{self.config.providers.openai.core.realtime_ws_url_base}?intent=transcription"

    async def start(self):
        """Connect and configure the session."""
        # Removed "OpenAI-Beta": "realtime=v1" to support GA transcription features
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        # Log host for GA vs Azure verification
        try:
            from urllib.parse import urlparse

            parsed = urlparse(self.url)
            logger.info(f"Connecting to OpenAI Realtime Host: {parsed.netloc}")
        except Exception:
            logger.info(f"Connecting to OpenAI at {self.url}...")

        try:
            self.ws = await websockets.connect(
                self.url, additional_headers=headers if not self.config.test.enabled else None
            )
            self._is_running = True
            self._receive_task = asyncio.create_task(self._receive_loop())

            # Configure session using the nested schema
            await self._update_session()
            logger.info("Connected to OpenAI successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to OpenAI: {e}")
            raise

    async def _update_session(self):
        """Send the session.update configuration."""
        if not self.ws:
            return

        core = self.config.providers.openai.core
        adv = self.config.providers.openai.advanced

        # Map noise reduction
        noise_reduction = None
        if adv.noise_reduction == "auto":
            noise_reduction = "auto"

        # Restore 'type': 'transcription' for GA behavior
        session_update = {
            "type": "session.update",
            "session": {
                "type": "transcription",
                "audio": {
                    "input": {
                        "format": {"type": "audio/pcm", "rate": core.input_audio_rate},
                        "noise_reduction": noise_reduction,
                        "transcription": {
                            "model": core.model,  # e.g., gpt-4o-transcribe-latest
                            "language": core.language,
                        },
                        "turn_detection": {
                            "type": "server_vad",
                            "threshold": adv.vad_threshold,
                            "prefix_padding_ms": adv.prefix_padding_ms,
                            "silence_duration_ms": adv.silence_duration_ms,
                        }
                        if adv.turn_detection_type == "server_vad"
                        else None,
                    }
                },
                "include": ["item.input_audio_transcription.logprobs"]
                if adv.include_logprobs
                else [],
            },
        }

        logger.debug(f"Sending session.update: {json.dumps(session_update)}")
        await self.ws.send(json.dumps(session_update))

    async def stop(self):
        """Graceful shutdown."""
        self._is_running = False
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self.ws:
            await self.ws.close()
            self.ws = None
        logger.info("Disconnected from OpenAI.")

    async def send_audio(self, processed_chunk: Union[bytes, str], capture_time: float):
        """Send audio via input_audio_buffer.append."""
        if not self.ws or not self._is_running:
            return

        # processed_chunk is base64 string from AudioAdapter
        event = {"type": "input_audio_buffer.append", "audio": processed_chunk}
        try:
            await self.ws.send(json.dumps(event))
        except Exception as e:
            logger.error(f"Error sending audio to OpenAI: {e}")

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

    async def _handle_event(self, event: dict):
        """Route transcription events."""
        ev_type = event.get("type")

        # Live typing updates
        if ev_type == "conversation.item.input_audio_transcription.delta":
            delta = event.get("delta")
            if delta:
                self.current_transcript += delta
                self.on_partial(self.current_transcript)

        # Final segment completed
        elif ev_type == "conversation.item.input_audio_transcription.completed":
            transcript = event.get("transcript")
            if transcript:
                logger.info(f"OpenAI Final Segment: {transcript.strip()}")
                self.on_final(transcript.strip())
            self.current_transcript = ""

        # Buffer committed (VAD trigger)
        elif ev_type == "input_audio_buffer.committed":
            logger.debug("OpenAI: Audio buffer committed by server VAD.")
            # Reverted: Do NOT clear buffer here, as deltas for the committed segment
            # may still be arriving. We clear only on 'completed'.

        elif ev_type == "error":
            logger.error(f"OpenAI API Error: {event.get('error')}")

        elif ev_type == "session.updated":
            logger.info("OpenAI: Session configuration updated successfully.")
