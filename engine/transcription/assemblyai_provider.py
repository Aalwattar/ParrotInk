import asyncio
import json
from typing import Callable, Optional, Union

import websockets.asyncio.client
from websockets.asyncio.client import ClientConnection

from engine.app_types import EffectiveAssemblyAIConfig
from engine.audio.adapter import ProviderAudioSpec
from engine.constants import STATUS_READY
from engine.logging import get_logger

from .base import BaseProvider

logger = get_logger("AssemblyAI")


class AssemblyAIProvider(BaseProvider):
    """AssemblyAI transcription provider using Streaming V3."""

    def __init__(
        self,
        api_key: str,
        on_partial: Callable[[str], None],
        on_final: Callable[[str], None],
        effective_config: EffectiveAssemblyAIConfig,
        on_status: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(
            api_key,
            on_partial,
            on_final,
            effective_config.url,
            stop_timeout=effective_config.stop_timeout,
            on_status=on_status,
        )
        self.effective_config = effective_config
        self.url = effective_config.url
        self.ws: Optional[ClientConnection] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._is_running = False
        self.last_transcript = ""

    @property
    def is_running(self) -> bool:
        return self._is_running

    def get_audio_spec(self) -> ProviderAudioSpec:
        return ProviderAudioSpec(
            sample_rate_hz=self.effective_config.sample_rate,
            wire_encoding="pcm16_bytes",
        )

    def get_type(self) -> str:
        return "assemblyai"

    async def start(self):
        """Connect to AssemblyAI and start receiving events."""
        from engine.security import SecurityManager

        self._ready_event.clear()
        is_trusted = SecurityManager.is_url_trusted(self.url)
        is_test = self.effective_config.is_test

        if not is_trusted and not is_test:
            logger.error(f"Refusing to connect to untrusted endpoint: {self.url}")
            raise ConnectionError(f"Untrusted transcription endpoint: {self.url}")

        headers = {"Authorization": self.api_key}
        logger.info(f"Connecting to AssemblyAI at {self.url}...")
        try:
            self.ws = await websockets.connect(
                self.url, additional_headers=headers if not is_test else None
            )
            self._is_running = True
            self._receive_task = asyncio.create_task(self._receive_loop())
            logger.info("Connected to AssemblyAI successfully.")
            # V3 does not send a SessionBegins handshake message, so we are ready immediately
            self._ready_event.set()
        except Exception as e:
            logger.error(f"Failed to connect to AssemblyAI: {e}")
            raise

    async def _do_stop(self):
        """Close connection and stop tasks."""
        is_active = self._is_running
        self._is_running = False

        if self.ws and is_active:
            try:
                # Send end of stream message
                terminate_msg = json.dumps({"terminate_session": True})
                logger.debug(f"Sending termination message: {terminate_msg}")
                await self.ws.send(terminate_msg)
                # Give it a moment to process before hard close
                await asyncio.sleep(0.2)
            except Exception as e:
                logger.debug(f"Error during graceful shutdown: {e}")

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
        logger.info("Disconnected from AssemblyAI.")

    async def send_audio(self, processed_chunk: Union[bytes, str], capture_time: float):
        """Send audio chunk as raw binary PCM16."""
        if not self.ws or not self._is_running:
            return

        # In V3, we send the raw bytes directly. processed_chunk is already bytes.
        try:
            await self.ws.send(processed_chunk)
        except websockets.exceptions.ConnectionClosed:
            logger.info("AssemblyAI connection closed while sending audio.")
            self._is_running = False
        except Exception as e:
            logger.error(f"Error sending audio: {e}")

    async def _receive_loop(self):
        """Listen for transcription events."""
        try:
            async for message in self.ws:
                logger.debug(f"Received message: {message}")
                event = json.loads(message)
                await self._handle_event(event)
        except websockets.exceptions.ConnectionClosed:
            logger.info("AssemblyAI connection closed.")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in AssemblyAI receive loop: {e}")

    async def _handle_event(self, event: dict):
        """Process incoming events."""
        msg_type = event.get("type") or event.get("message_type")
        text = event.get("transcript") or event.get("text")

        if text is not None:
            if msg_type == "Turn":
                # In V3, transcripts within a Turn are cumulative.
                clean_text = text.strip()
                if clean_text:
                    self.on_partial(text)
                    self.last_transcript = text

                if event.get("end_of_turn"):
                    # Senior Privacy Implementation: Use structured metadata for automatic redaction
                    logger.debug("AssemblyAI Final (Turn)", extra={"text": text})
                    self.on_final(text)
                    self.last_transcript = ""

            elif msg_type == "FinalTranscript":
                # Senior Privacy Implementation: Use structured metadata for automatic redaction
                logger.debug("AssemblyAI Final", extra={"text": text})
                self.on_final(text)
            elif msg_type == "PartialTranscript":
                self.on_partial(text)

        elif "error" in event:
            logger.error(f"AssemblyAI API Error: {event.get('error')}")
        elif msg_type == "SessionBegins":
            logger.info(f"AssemblyAI Session Started: {event.get('session_id')}")
            self._ready_event.set()
            if self.on_status:
                self.on_status(STATUS_READY)
