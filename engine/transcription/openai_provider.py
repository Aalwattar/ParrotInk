import asyncio
import json
import time
from typing import Callable, Optional, Union

import websockets.asyncio.client
from websockets.asyncio.client import ClientConnection

from engine.audio.adapter import ProviderAudioSpec
from engine.config import Config
from engine.logging import get_logger

from .base import BaseProvider

logger = get_logger("OpenAI")


class OpenAIProvider(BaseProvider):
    """OpenAI Realtime API transcription provider."""

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
        self.is_running = False
        self.current_partial = ""

    def get_audio_spec(self) -> ProviderAudioSpec:
        return ProviderAudioSpec(
            sample_rate_hz=self.config.providers.openai.core.input_audio_rate,
            wire_encoding="pcm16_base64",
        )

    def get_type(self) -> str:
        return "openai"

    def _build_url(self) -> str:
        if self.config.test.enabled:
            return self.config.test.openai_mock_url

        core = self.config.providers.openai.core
        # intent=transcription is used for transcription-only sessions
        return f"{core.realtime_ws_url_base}?intent=transcription"

    async def start(self):
        """Connect to OpenAI and start receiving events."""
        headers = {"Authorization": f"Bearer {self.api_key}", "OpenAI-Beta": "realtime=v1"}
        logger.info(f"Connecting to OpenAI at {self.url}...")
        try:
            self.ws = await websockets.connect(
                self.url, additional_headers=headers if not self.config.test.enabled else None
            )
            self.is_running = True

            # Initialize session for transcription only
            await self._initialize_session()

            self._receive_task = asyncio.create_task(self._receive_loop())
            logger.info("Connected to OpenAI successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to OpenAI: {e}")
            raise

    async def stop(self):
        """Close connection and stop tasks."""
        self.is_running = False
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
        """Send audio chunk as base64 encoded PCM16."""
        if not self.ws or not self.is_running:
            return

        send_start = time.perf_counter()
        lag_ms = (send_start - capture_time) * 1000
        logger.debug(f"Audio chunk age before send: {lag_ms:.1f}ms")

        # processed_chunk is already base64 string for OpenAI
        event = {"type": "input_audio_buffer.append", "audio": processed_chunk}
        event_str = json.dumps(event)
        logger.debug(f"Sending event: {event_str}")
        await self.ws.send(event_str)

    async def _initialize_session(self):
        """Configure session for audio-to-text only using transcription_session.update."""
        core = self.config.providers.openai.core
        adv = self.config.providers.openai.advanced

        # Note: We use transcription_session.update as specified for intent=transcription
        # Added 'session' wrapper to resolve "Missing required parameter: 'session'" error
        session_update = {
            "type": "transcription_session.update",
            "session": {
                "input_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": core.model,
                    "language": core.language,
                },
                "turn_detection": {
                    "type": adv.turn_detection_type,
                    "threshold": adv.vad_threshold,
                    "prefix_padding_ms": adv.prefix_padding_ms,
                    "silence_duration_ms": adv.silence_duration_ms,
                }
                if adv.turn_detection_type != "off"
                else None,
            },
        }
        event_str = json.dumps(session_update)
        logger.debug(f"Sending transcription session update: {event_str}")
        await self.ws.send(event_str)

    async def _receive_loop(self):
        """Listen for transcription events."""
        try:
            async for message in self.ws:
                logger.debug(f"Received message: {message}")
                event = json.loads(message)
                await self._handle_event(event)
        except websockets.exceptions.ConnectionClosed:
            logger.info("OpenAI connection closed.")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in OpenAI receive loop: {e}")

    async def _handle_event(self, event: dict):
        """Process incoming events."""
        event_type = event.get("type")

        if event_type == "conversation.item.input_audio_transcription.completed":
            transcript = event.get("transcript", "")
            if transcript:
                logger.info(f"Final transcript received: {transcript}")
                self.on_final(transcript)
            self.current_partial = ""

        elif event_type == "conversation.item.input_audio_transcription.delta":
            delta = event.get("delta", "")
            if delta:
                self.current_partial += delta
                self.on_partial(self.current_partial)

        elif event_type == "error":
            logger.error(f"OpenAI API Error: {event.get('error')}")
