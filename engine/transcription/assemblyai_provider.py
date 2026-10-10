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
        self.session_id: Optional[str] = None
        self.expires_at: Optional[int] = None
        self.session_configuration: dict = {}
        self._stopping = False
        self._termination_event = asyncio.Event()
        self._final_event = asyncio.Event()
        self._pending_audio = False
        self._pending_turns: set[int] = set()
        self._has_final_turn = False
        self._server_speech_pending = False
        self._completed_turns: set[int] = set()
        self._finish_lock = asyncio.Lock()

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
        self._failure_event.clear()
        self._stopping = False
        self._termination_event.clear()
        self._completed_turns.clear()
        self.reset_utterance()
        self.session_id = None
        self.expires_at = None
        self.session_configuration = {}
        is_test = self.effective_config.is_test
        is_trusted = SecurityManager.is_url_trusted(self.url, is_test=is_test)

        if not is_trusted and not is_test:
            logger.error(f"Refusing to connect to untrusted endpoint: {self.url}")
            raise ConnectionError(f"Untrusted transcription endpoint: {self.url}")

        headers = {"Authorization": self.api_key}
        logger.info(f"Connecting to AssemblyAI at {self.url}...")
        try:
            self.ws = await websockets.connect(
                self.url,
                additional_headers=headers if not is_test else None,
                proxy=None if is_test else True,
            )
            self._is_running = True
            self._receive_task = asyncio.create_task(self._receive_loop())
            logger.info("Connected to AssemblyAI successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to AssemblyAI: {e}")
            raise

    async def _do_stop(self):
        """Close connection and stop tasks."""
        self._stopping = True
        try:
            if self.ws and self._is_running:
                await self.finish_utterance()
                await self.ws.send(json.dumps({"type": "Terminate"}))
                # Keep receiving final turns until the server acknowledges termination.
                try:
                    await asyncio.wait_for(
                        self._termination_event.wait(),
                        timeout=min(1.0, max(0.05, self.stop_timeout * 0.2)),
                    )
                except TimeoutError:
                    logger.debug("AssemblyAI termination acknowledgement timed out.")
        except Exception as e:
            logger.debug(f"Error during graceful shutdown: {e}")
        finally:
            self._is_running = False
            self._ready_event.clear()
            if self._receive_task:
                self._receive_task.cancel()
                try:
                    await self._receive_task
                except asyncio.CancelledError:
                    pass
                self._receive_task = None
            if self.ws:
                ws, self.ws = self.ws, None
                await ws.close()
        logger.info("Disconnected from AssemblyAI.")

    def reset_utterance(self):
        """Clear recording-local text while retaining session-wide turn deduplication."""
        self.last_transcript = ""
        self._voice_active: Optional[bool] = None
        self._pending_audio = False
        self._pending_turns.clear()
        self._has_final_turn = False
        self._server_speech_pending = False
        self._final_event.clear()

    async def finish_utterance(self):
        """Request a final turn without terminating the reusable streaming session."""
        async with self._finish_lock:
            if not self._pending_audio and not self._pending_turns and not self.last_transcript:
                return
            if not self.ws or not self._is_running:
                raise ConnectionError("AssemblyAI disconnected before the current phrase finished.")
            self._final_event.clear()
            try:
                await self.ws.send(json.dumps({"type": "ForceEndpoint"}))
                await asyncio.wait_for(
                    self._final_event.wait(),
                    timeout=min(3.0, max(0.05, self.stop_timeout * 0.5)),
                )
            except TimeoutError:
                if (
                    self._is_running
                    and not self._failure_event.is_set()
                    and self._has_final_turn
                    and not self._server_speech_pending
                    and not self._pending_turns
                    and not self.last_transcript
                ):
                    # No new server turn exists to acknowledge after the completed final.
                    self._pending_audio = False
                    logger.info("AssemblyAI final already received; retaining hot connection.")
                    return
                logger.error(
                    "AssemblyAI final turn timed out: pending_audio=%s pending_turns=%d "
                    "partial_characters=%d voice_active=%s final_received=%s "
                    "server_speech_pending=%s",
                    self._pending_audio,
                    len(self._pending_turns),
                    len(self.last_transcript),
                    getattr(self, "_voice_active", None),
                    self._has_final_turn,
                    self._server_speech_pending,
                )
                raise TimeoutError(
                    "AssemblyAI did not finalize the current phrase in time."
                ) from None
            except Exception as e:
                self._connection_failed(f"Could not finish the current phrase: {e}")
                raise
            # Transport failure and Termination also wake waiters. Neither is proof
            # that the pending phrase received its final transcript.
            if not self._is_running or self._pending_audio or self._pending_turns:
                raise ConnectionError("AssemblyAI disconnected before the current phrase finished.")

    def _connection_failed(self, message: str):
        was_running = self._is_running
        self._is_running = False
        self._failure_event.set()
        self._ready_event.clear()
        self._final_event.set()
        if was_running and not self._stopping and self.on_error:
            self.on_error(TranscriptionError(title="AssemblyAI Connection Lost", message=message))

    async def send_audio(self, processed_chunk: Union[bytes, str], capture_time: float):
        """Send audio chunk as raw binary PCM16."""
        if not self.ws or not self._is_running:
            return

        # In V3, we send the raw bytes directly. processed_chunk is already bytes.
        try:
            if processed_chunk and getattr(self, "_voice_active", None) is not False:
                self._pending_audio = True
            await self.ws.send(processed_chunk)
        except websockets.exceptions.ConnectionClosed:
            logger.info("AssemblyAI connection closed while sending audio.")
            self._connection_failed("The streaming connection closed while sending audio.")
        except Exception as e:
            if self._is_running:
                logger.error(f"Error sending audio: {e}")
                self._connection_failed(str(e))

    async def notify_voice_activity(self, active: bool, capture_time: float):
        # Trailing silence after an already-final turn needs no ForceEndpoint.
        # Server SpeechStarted/Turn events still track speech missed by local VAD.
        self._voice_active = active

    async def update_agent_context(self, context: str):
        """Update the agent context mid-stream using UpdateConfiguration."""
        if not self.ws or not self._is_running:
            return
        trimmed = context[:1500]
        try:
            msg = json.dumps({"type": "UpdateConfiguration", "agent_context": trimmed})
            logger.debug(f"Sending UpdateConfiguration | length: {len(msg)}")
            await self.ws.send(msg)
        except Exception as e:
            logger.error(f"Failed to update agent context mid-stream: {e}")

    async def _receive_loop(self):
        """Listen for transcription events."""
        failure = "The streaming connection closed unexpectedly. Please reconnect."
        try:
            async for message in self.ws:
                event = json.loads(message)
                msg_type = event.get("type") or event.get("message_type") or "unknown"
                logger.debug(f"Received AssemblyAI event: {msg_type} | length: {len(message)}")
                await self._handle_event(event)
        except websockets.exceptions.ConnectionClosed:
            logger.info("AssemblyAI connection closed.")
        except asyncio.CancelledError:
            return
        except Exception as e:
            if self._is_running:
                logger.error(f"Error in AssemblyAI receive loop: {e}")
                failure = str(e)
        finally:
            if self._is_running:
                self._connection_failed(failure)

    async def _handle_event(self, event: dict):
        """Process incoming events."""
        if self._failure_event.is_set():
            return
        msg_type = event.get("type") or event.get("message_type")
        text = event.get("transcript", event.get("text"))

        if msg_type in {"Begin", "SessionBegins"}:
            self.session_id = event.get("id") or event.get("session_id")
            self.expires_at = event.get("expires_at")
            self.session_configuration = event.get("configuration", {})
            logger.info(f"AssemblyAI session started: {self.session_id}")
            self._ready_event.set()
            if self.on_status:
                self.on_status(STATUS_READY)
            return
        if msg_type == "Termination":
            self._termination_event.set()
            self._final_event.set()
            if not self._stopping:
                self._connection_failed("The streaming session ended. Please reconnect.")
            return
        if msg_type == "SpeechStarted":
            self._pending_audio = True
            self._server_speech_pending = True
            return

        if msg_type == "Turn" and text is not None:
            words = event.get("words", [])
            is_final = bool(event.get("end_of_turn"))
            turn_speaker = event.get("speaker_label")
            turn_order = event.get("turn_order")
            if turn_order is not None and turn_order in self._completed_turns:
                return
            if turn_order is not None:
                self._pending_turns.add(turn_order)
            # Legacy streaming models send an unformatted final and then its formatted
            # revision. Emit only the formatted revision when formatting was requested.
            awaiting_format = (
                is_final
                and self.effective_config.format_text
                and event.get("turn_is_formatted") is False
            )
            if awaiting_format:
                self.last_transcript = text
                return
            if is_final:
                if turn_order is not None:
                    self._completed_turns.add(turn_order)
                    self._pending_turns.discard(turn_order)
                self._pending_audio = False
                self._has_final_turn = True
                self._server_speech_pending = False
                self.last_transcript = ""
                if not self._pending_turns:
                    self._final_event.set()

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
            if not self._is_running or self._stopping:
                logger.debug(f"Ignoring AssemblyAI error during shutdown: {error_msg}")
                return

            error_code = event.get("error_code")
            logger.error(
                "AssemblyAI rejected the streaming session: code=%s pending_turns=%d",
                error_code if isinstance(error_code, int) else "unknown",
                len(self._pending_turns),
            )

            if self.on_error:
                # Map common AssemblyAI errors to user-friendly messages
                title = "AssemblyAI Error"
                message = "Check your AssemblyAI credentials, model, and connection settings."

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
            self._is_running = False
            self._failure_event.set()
            self._ready_event.clear()
            self._final_event.set()
