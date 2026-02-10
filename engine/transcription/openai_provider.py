import asyncio
import base64
import json
from typing import Callable, Optional

import numpy as np
import websockets

from .base import BaseProvider
from engine.config import Config
from engine.logging import get_logger

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
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self._receive_task: Optional[asyncio.Task] = None
        self.is_running = False

    def _build_url(self) -> str:
        if self.config.test.enabled:
            return self.config.test.openai_mock_url
        
        core = self.config.providers.openai.core
        return f"{core.realtime_ws_url_base}?model={core.realtime_ws_model}"

    async def start(self):
        """Connect to OpenAI and start receiving events."""
        headers = {"Authorization": f"Bearer {self.api_key}", "OpenAI-Beta": "realtime=v1"}
        logger.info(f"Connecting to OpenAI at {self.url}...")
        try:
            self.ws = await websockets.connect(
                self.url, 
                additional_headers=headers if not self.config.test.enabled else None
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

    async def send_audio(self, audio_chunk: np.ndarray):
        """Send audio chunk as base64 encoded PCM16, with resampling if needed."""
        if not self.ws or not self.is_running:
            return

        source_rate = self.config.audio.capture_sample_rate
        target_rate = self.config.providers.openai.core.input_audio_rate

        # Ensure we have a 1D float array for resampling
        audio_chunk = audio_chunk.astype(np.float64).flatten()

        # Resample if capture rate differs from OpenAI target rate (usually 16k -> 24k)
        if source_rate != target_rate:
            num_samples = int(len(audio_chunk) * target_rate / source_rate)
            x_new = np.linspace(0, len(audio_chunk) - 1, num_samples)
            x_old = np.arange(len(audio_chunk))
            audio_chunk = np.interp(x_new, x_old, audio_chunk)

        # Convert float32 [-1.0, 1.0] or float64 to int16
        audio_int16 = (audio_chunk * 32767).astype(np.int16)
        audio_base64 = base64.b64encode(audio_int16.tobytes()).decode("utf-8")

        event = {"type": "input_audio_buffer.append", "audio": audio_base64}
        event_str = json.dumps(event)
        logger.debug(f"Sending event: {event_str}")
        await self.ws.send(event_str)

    async def _initialize_session(self):
        """Configure session for audio-to-text only (no voice response needed)."""
        core = self.config.providers.openai.core
        adv = self.config.providers.openai.advanced
        
        session_update = {
            "type": "session.update",
            "session": {
                "modalities": ["text"],
                "instructions": core.prompt if core.prompt else "Transmit transcribed text only.",
                "input_audio_format": core.input_audio_type.split("/")[-1],
                "input_audio_transcription": {"model": core.transcription_model},
                "turn_detection": {
                    "type": adv.turn_detection_type,
                    "threshold": adv.vad_threshold,
                    "prefix_padding_ms": adv.prefix_padding_ms,
                    "silence_duration_ms": adv.silence_duration_ms,
                } if adv.turn_detection_type != "off" else None,
            },
        }
        event_str = json.dumps(session_update)
        logger.debug(f"Sending session update: {event_str}")
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

        elif event_type == "error":
            logger.error(f"OpenAI API Error: {event.get('error')}")
