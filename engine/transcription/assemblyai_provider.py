import asyncio
import json
from typing import Callable, Optional, Union

import websockets.asyncio.client
from websockets.asyncio.client import ClientConnection

from engine.app_types import EffectiveAssemblyAIConfig, TranscriptionError
from engine.audio.adapter import ProviderAudioSpec
from engine.constants import STATUS_READY
from engine.logging import get_logger

from .base import BaseProvider
from .speaker_manager import SpeakerManager

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
        on_error: Optional[Callable[[TranscriptionError], None]] = None,
        speaker_manager: Optional[SpeakerManager] = None,
    ):
        super().__init__(
            api_key,
            on_partial,
            on_final,
            effective_config.url,
            stop_timeout=effective_config.stop_timeout,
            on_status=on_status,
            on_error=on_error,
        )
        self.effective_config = effective_config
        self.url = effective_config.url
        self.ws: Optional[ClientConnection] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._is_running = False
        self.last_transcript = ""
        self.speaker_manager = speaker_manager if effective_config.enable_diarization else None

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
                # Send end of stream message - V3 uses {"type": "Terminate"}
                terminate_msg = json.dumps({"type": "Terminate"})
                logger.debug(f"Sending termination message: {terminate_msg}")
                await self.ws.send(terminate_msg)
                # Give it a moment to process before hard close
                await asyncio.sleep(0.2)
            except Exception as e:
                logger.debug(f"Error during graceful shutdown: {e}")

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
            if self._is_running:
                logger.error(f"Error sending audio: {e}")
                self._is_running = False

    async def update_agent_context(self, context: str):
        """Update the agent context mid-stream using UpdateConfiguration."""
        if not self.ws or not self._is_running:
            return
        trimmed = context[:1500]
        try:
            msg = json.dumps({"type": "UpdateConfiguration", "agent_context": trimmed})
            logger.debug(f"Sending UpdateConfiguration for agent_context: {msg}")
            await self.ws.send(msg)
        except Exception as e:
            logger.error(f"Failed to update agent context mid-stream: {e}")

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
            if self._is_running:
                logger.error(f"Error in AssemblyAI receive loop: {e}")
                self._is_running = False

    async def _handle_event(self, event: dict):
        """Process incoming events."""
        msg_type = event.get("type") or event.get("message_type")
        text = event.get("transcript") or event.get("text")

        if text is not None:
            words = event.get("words", [])
            is_final = bool(event.get("end_of_turn"))
            turn_speaker = event.get("speaker_label")

            if self.speaker_manager:
                if is_final:
                    formatted = self.speaker_manager.format_final_turn(
                        transcript=text,
                        words=words,
                        turn_speaker=turn_speaker,
                    )
                    if formatted:
                        # Senior Privacy Implementation: Use structured metadata
                        # for automatic redaction
                        logger.debug("AssemblyAI Final (Turn)", extra={"text": formatted})
                        self.on_final(formatted)
                        self.last_transcript = ""  # Reset for next turn
                else:
                    # HUD only. We send raw, unformatted text for partials.
                    # The SmartInjector will safely diff this single-line text.
                    if text.strip():
                        self.on_partial(text)
                        self.last_transcript = text
                return

            # Default Mode (Diarization Disabled)
            if msg_type == "Turn":
                if is_final:
                    logger.debug("AssemblyAI Final (Turn)", extra={"text": text})
                    self.on_final(text)
                    self.last_transcript = ""
                else:
                    if text.strip():
                        self.on_partial(text)
                        self.last_transcript = text

        elif "error" in event:
            error_msg = str(event.get("error"))

            # Senior Robustness: Only report errors if we are still active.
            # Errors received during intentional shutdown are logged but not escalated.
            if not self._is_running:
                logger.debug(f"Ignoring AssemblyAI error during shutdown: {error_msg}")
                return

            logger.error(f"AssemblyAI API Error: {error_msg}")

            if self.on_error:
                # Map common AssemblyAI errors to user-friendly messages
                title = "AssemblyAI Error"
                message = error_msg

                if "Insufficient funds" in error_msg:
                    title = "Out of Credits"
                    message = "Please top up your AssemblyAI account."
                elif "Authentication" in error_msg or "Unauthorized" in error_msg:
                    title = "Auth Failed"
                    message = "Invalid AssemblyAI API Key. Check settings."
                elif "Rate limit" in error_msg:
                    title = "Rate Limited"
                    message = "Too many requests. Please wait a moment."

                self.on_error(TranscriptionError(title=title, message=message))

        elif msg_type == "SessionBegins":
            logger.info(f"AssemblyAI Session Started: {event.get('session_id')}")
            self._ready_event.set()
            if self.on_status:
                self.on_status(STATUS_READY)
