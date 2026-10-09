import asyncio
import base64
import json
from typing import Callable, Optional, Union
from urllib.parse import urlparse

import websockets.asyncio.client
from websockets.asyncio.client import ClientConnection

from engine.app_types import EffectiveOpenAIConfig, TranscriptionError
from engine.audio.adapter import ProviderAudioSpec
from engine.constants import STATUS_READY
from engine.logging import get_logger

from .base import BaseProvider

logger = get_logger("OpenAI")
MODERN_MODELS = {"gpt-live-transcribe", "gpt-transcribe"}


class OpenAIProvider(BaseProvider):
    """Realtime transcription with explicit audio turns and ordered text delivery."""

    def __init__(
        self,
        api_key: str,
        on_partial: Callable[[str], None],
        on_final: Callable[[str], None],
        effective_config: EffectiveOpenAIConfig,
        on_status: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[TranscriptionError], None]] = None,
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
        self._closing = False
        self._drained = asyncio.Event()
        self._reset_session()

    def _reset_session(self):
        self.current_transcript = ""
        self._transport_error: Optional[str] = None
        self._transcripts: dict[str, str] = {}
        self._completed: dict[str, str] = {}
        self._turn_order: list[str] = []
        self._previous: dict[str, Optional[str]] = {}
        self._emitted: set[str] = set()
        self._pending_commits = 0
        self._drained.set()
        self.reset_utterance()

    def reset_utterance(self):
        """Reset capture timing without discarding transcription still in flight."""
        self._has_audio = False
        self._audio_bytes = 0
        self._last_voice_time: Optional[float] = None
        self._voice_active: Optional[bool] = None
        self._commit_after_chunk = False
        self._prefix_audio = b""

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def _manual_turns(self) -> bool:
        model = self.effective_config.transcription_model
        return model in MODERN_MODELS or any(model.startswith(name + "-") for name in MODERN_MODELS)

    def get_audio_spec(self) -> ProviderAudioSpec:
        return ProviderAudioSpec(sample_rate_hz=24000, wire_encoding="pcm16_base64")

    def get_type(self) -> str:
        return self.effective_config.provider_id

    async def start(self):
        from engine.security import SecurityManager

        self._ready_event.clear()
        self._failure_event.clear()
        self._closing = False
        self._reset_session()
        is_test = self.effective_config.is_test
        if not SecurityManager.is_url_trusted(self.url, is_test=is_test) and not is_test:
            raise ConnectionError("Untrusted transcription endpoint")
        headers = self.effective_config.headers
        if headers is None:
            headers = {"Authorization": f"Bearer {self.api_key}"}
        logger.info("Connecting transcription WebSocket to host: %s", urlparse(self.url).netloc)
        try:
            self.ws = await websockets.connect(
                self.url,
                additional_headers=headers if not is_test else None,
                proxy=None if is_test else True,
            )
            self._is_running = True
            self._receive_task = asyncio.create_task(self._receive_loop())
            await self._update_session()
        except Exception:
            self._closing = True
            await self._close_transport()
            raise

    async def _update_session(self):
        if not self.ws:
            return
        cfg = self.effective_config
        transcription = {"model": cfg.transcription_model, "prompt": cfg.prompt}
        if self._manual_turns:
            languages = cfg.languages or ((cfg.language,) if cfg.language else ())
            if languages:
                transcription["languages"] = list(languages)
            if cfg.keywords:
                transcription["keywords"] = list(cfg.keywords)
            transcription["delay"] = cfg.delay
            turn_detection = None
        else:
            if cfg.language:
                transcription["language"] = cfg.language
            turn_detection = {
                "type": cfg.turn_detection_type,
                "threshold": cfg.vad_threshold,
                "prefix_padding_ms": cfg.prefix_padding_ms,
                "silence_duration_ms": cfg.silence_duration_ms,
            }
        audio_input = {
            "format": {"type": "audio/pcm", "rate": 24000},
            "transcription": transcription,
            "turn_detection": turn_detection,
            "noise_reduction": (
                {"type": cfg.noise_reduction_type}
                if cfg.noise_reduction_type and cfg.noise_reduction_type != "off"
                else None
            ),
        }
        await self.ws.send(
            json.dumps(
                {
                    "type": "session.update",
                    "session": {"type": "transcription", "audio": {"input": audio_input}},
                }
            )
        )

    async def notify_voice_activity(self, active: bool, capture_time: float):
        """Called before append; commit after the chunk that reaches the silence limit."""
        self._voice_active = active
        if active:
            self._last_voice_time = capture_time
            self._commit_after_chunk = False
        elif self._manual_turns and self._has_audio and self._last_voice_time is not None:
            silence = capture_time - self._last_voice_time
            self._commit_after_chunk = (
                silence >= self.effective_config.silence_duration_ms / 1000 - 1e-6
            )

    async def send_audio(self, processed_chunk: Union[bytes, str], capture_time: float):
        if not self.ws or not self._is_running or not processed_chunk:
            return
        if isinstance(processed_chunk, bytes):
            raw_audio = processed_chunk
            processed_chunk = base64.b64encode(processed_chunk).decode("ascii")
        else:
            raw_audio = base64.b64decode(processed_chunk)
        # Retain a bounded local pre-roll so soft speech onset is not discarded.
        if self._manual_turns and self._voice_active is False and not self._has_audio:
            prefix_ms = max(0, min(self.effective_config.prefix_padding_ms, 3000))
            capacity = int(prefix_ms * 48)  # Mono PCM16 at 24 kHz.
            self._prefix_audio = (self._prefix_audio + raw_audio)[-capacity:] if capacity else b""
            return
        try:
            if self._prefix_audio:
                await self.ws.send(
                    json.dumps(
                        {
                            "type": "input_audio_buffer.append",
                            "audio": base64.b64encode(self._prefix_audio).decode("ascii"),
                        }
                    )
                )
                self._audio_bytes += len(self._prefix_audio)
                self._has_audio = True
                self._prefix_audio = b""
            await self.ws.send(
                json.dumps({"type": "input_audio_buffer.append", "audio": processed_chunk})
            )
            self._has_audio = True
            self._audio_bytes += len(raw_audio)
            if self._commit_after_chunk:
                await self._commit_audio()
        except Exception:
            self._fail_transport("Could not send microphone audio. Reconnect and try again.")
            raise

    async def _commit_audio(self):
        if not self._has_audio or not self.ws or not self._is_running:
            return
        # The Realtime API requires at least 100 ms of audio per explicit commit.
        if self._audio_bytes < 4800:
            padding = base64.b64encode(bytes(4800 - self._audio_bytes)).decode("ascii")
            await self.ws.send(json.dumps({"type": "input_audio_buffer.append", "audio": padding}))
        self._pending_commits += 1
        self._drained.clear()
        try:
            await self.ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
        except Exception:
            self._pending_commits -= 1
            self._fail_transport("Could not finalize microphone audio. Reconnect and try again.")
            raise
        self.reset_utterance()

    async def finish_utterance(self):
        if self._transport_error or not self._is_running:
            raise ConnectionError(
                self._transport_error or "Transcription connection is not running"
            )
        if not self.ws:
            raise ConnectionError("Transcription connection is unavailable")
        await self._commit_audio()
        try:
            async with asyncio.timeout(max(0.1, self.stop_timeout * 0.75)):
                await self._drained.wait()
        except TimeoutError:
            logger.warning("Timed out waiting for final transcription turns")
            self._transport_error = "The final transcript timed out. Check the connection."
            self._is_running = False
            self._ready_event.clear()
            self._drained.set()
            if self.on_error:
                self.on_error(TranscriptionError("Transcription Delayed", self._transport_error))
            raise
        if self._transport_error or not self._is_running:
            raise ConnectionError(self._transport_error or "Transcription connection closed")

    async def _do_stop(self):
        try:
            if self._is_running:
                try:
                    await self.finish_utterance()
                except (TimeoutError, ConnectionError):
                    # Drain failures were already reported; transport cleanup is mandatory.
                    pass
        finally:
            self._closing = True
            await self._close_transport()

    async def _close_transport(self):
        self._is_running = False
        self._ready_event.clear()
        self._drained.set()
        if self._receive_task and self._receive_task is not asyncio.current_task():
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None
        if self.ws:
            try:
                await self.ws.close()
            finally:
                self.ws = None

    def _fail_transport(self, message: str):
        self._transport_error = message
        was_running = self._is_running
        self._is_running = False
        self._failure_event.set()
        self._ready_event.clear()
        self._drained.set()
        if was_running and not self._closing and self.on_error:
            self.on_error(TranscriptionError("Connection Lost", message))

    async def _receive_loop(self):
        try:
            async for message in self.ws:
                await self._handle_event(json.loads(message))
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.warning("Transcription receive connection ended unexpectedly")
        finally:
            if not self._closing:
                self._fail_transport(
                    "The transcription connection closed. Reconnect and try again."
                )

    def _flush_turns(self):
        while self._turn_order:
            item_id = self._turn_order[0]
            previous = self._previous.get(item_id)
            if previous and previous not in self._emitted:
                break
            if item_id not in self._completed:
                break
            self._turn_order.pop(0)
            transcript = self._completed.pop(item_id)
            self._transcripts.pop(item_id, None)
            self._emitted.add(item_id)
            if transcript.strip():
                self.on_final(transcript.strip())
        self.current_transcript = (
            self._transcripts.get(self._turn_order[0], "") if self._turn_order else ""
        )
        if self.current_transcript:
            self.on_partial(self.current_transcript)
        if not self._pending_commits and not self._turn_order:
            self._drained.set()

    async def _handle_event(self, event: dict):
        if self._transport_error or self._closing:
            return
        ev_type = event.get("type", "")
        item_id = event.get("item_id") or "_legacy"
        if ev_type == "input_audio_buffer.speech_stopped":
            if not self._manual_turns:
                self.reset_utterance()
                self._drained.clear()
        elif ev_type == "input_audio_buffer.committed":
            if self._pending_commits:
                self._pending_commits -= 1
            if item_id not in self._emitted and item_id not in self._turn_order:
                previous = event.get("previous_item_id")
                self._previous[item_id] = previous
                if previous in self._turn_order:
                    self._turn_order.insert(self._turn_order.index(previous) + 1, item_id)
                else:
                    # A late predecessor belongs ahead of its already known successor.
                    successors = [
                        i
                        for i, known in enumerate(self._turn_order)
                        if self._previous.get(known) == item_id
                    ]
                    self._turn_order.insert(
                        successors[0] if successors else len(self._turn_order), item_id
                    )
            self._drained.clear()
            self._flush_turns()
        elif ev_type in (
            "conversation.item.input_audio_transcription.delta",
            "input_audio_transcription.delta",
        ):
            if item_id in self._emitted or item_id in self._completed:
                return
            delta = event.get("delta", "")
            self._transcripts[item_id] = self._transcripts.get(item_id, "") + delta
            if not self._turn_order or self._turn_order[0] == item_id:
                self.current_transcript = self._transcripts[item_id]
                self.on_partial(self.current_transcript)
        elif ev_type in (
            "conversation.item.input_audio_transcription.completed",
            "input_audio_transcription.completed",
            "conversation.item.input_audio_transcription.failed",
            "input_audio_transcription.failed",
        ):
            if item_id in self._emitted:
                return
            self._completed[item_id] = event.get("transcript", "")
            if ev_type.endswith("failed") and self.on_error:
                self.on_error(
                    TranscriptionError(
                        "Transcription Failed",
                        "A spoken phrase could not be transcribed. Try again.",
                    )
                )
            if item_id not in self._turn_order and (item_id == "_legacy" or not self._manual_turns):
                self._turn_order.append(item_id)
                self._previous[item_id] = None
            self._flush_turns()
            if item_id == "_legacy":
                self._emitted.discard(item_id)
        elif ev_type == "error":
            if not self._is_running or self._closing:
                return
            error = event.get("error", {})
            code = str(error.get("code", ""))
            if "invalid_api_key" in code:
                title, message = "Auth Failed", "Invalid transcription credentials. Check settings."
            elif "rate_limit" in code:
                title, message = "Rate Limited", "Transcription rate limit reached. Please wait."
            elif "insufficient_quota" in code:
                title, message = "Out of Credits", "Please check your provider billing status."
            else:
                title, message = (
                    "Transcription Error",
                    "The server rejected transcription. Check the selected model and settings.",
                )
            self._transport_error = message
            self._is_running = False
            self._failure_event.set()
            self._ready_event.clear()
            self._drained.set()
            if self.on_error:
                self.on_error(TranscriptionError(title, message))
        elif ev_type in ("session.updated", "transcription_session.updated"):
            self._ready_event.set()
            if self.on_status:
                self.on_status(STATUS_READY)
