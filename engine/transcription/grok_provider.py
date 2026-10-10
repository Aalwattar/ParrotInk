"""Grok STT's binary audio protocol through Cloudflare's unified AI endpoint.

Stopping a recording sends audio.done and drains transcript.done. This closes
the upstream session; the next recording must establish a fresh connection.
"""

import asyncio
import json
from typing import Callable, Optional, Union

import websockets.asyncio.client as websockets
from websockets.exceptions import InvalidStatus

from engine.app_types import EffectiveCloudflareConfig, TranscriptionError
from engine.audio.adapter import ProviderAudioSpec
from engine.constants import STATUS_READY
from engine.security import SecurityManager

from .base import BaseProvider


class GrokProvider(BaseProvider):
    def __init__(
        self,
        api_key: str,
        on_partial: Callable[[str], None],
        on_final: Callable[[str], None],
        effective_config: EffectiveCloudflareConfig,
        on_status: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[TranscriptionError], None]] = None,
    ):
        super().__init__(
            api_key,
            on_partial,
            on_final,
            effective_config.url,
            effective_config.stop_timeout,
            on_status,
            on_error,
        )
        self.effective_config = effective_config
        self.ws = None
        self._is_running = False
        self._closing = False
        self._ending = False
        self._done_received = False
        self._receive_task = None
        self._has_audio = False
        self._finalized = asyncio.Event()
        self._finish_lock = asyncio.Lock()
        self._emitted_end = 0.0
        self._emitted_text: list[str] = []
        self._chunks: dict[float, str] = {}

    @property
    def is_running(self) -> bool:
        return self._is_running

    def get_type(self) -> str:
        return "cloudflare"

    def get_audio_spec(self) -> ProviderAudioSpec:
        return ProviderAudioSpec(
            sample_rate_hz=self.effective_config.sample_rate, wire_encoding="pcm16_bytes"
        )

    async def start(self):
        self._ready_event.clear()
        self._failure_event.clear()
        self._finalized.clear()
        self._closing = self._ending = self._done_received = self._has_audio = False
        self._emitted_end = 0.0
        self._emitted_text.clear()
        self._chunks.clear()
        if not SecurityManager.is_url_trusted(self.base_url, is_test=self.effective_config.is_test):
            raise ConnectionError("Untrusted Cloudflare Grok endpoint")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "cf-aig-gateway-id": self.effective_config.gateway_id,
            "cf-aig-collect-log-payload": "false",
        }
        try:
            self.ws = await websockets.connect(
                self.base_url,
                additional_headers=None if self.effective_config.is_test else headers,
                proxy=None if self.effective_config.is_test else True,
            )
        except Exception as error:
            self._failure_event.set()
            if isinstance(error, InvalidStatus) and error.response.status_code in (401, 403):
                raise ConnectionError(
                    "Cloudflare rejected the Grok token. Check Account > Workers AI > Read "
                    "permission and access to the configured account."
                ) from None
            raise ConnectionError("Could not connect to Cloudflare Grok STT") from None
        self._is_running = True
        self._receive_task = asyncio.create_task(self._receive_loop())

    def _fail(self, message: str):
        already_failed = self._failure_event.is_set()
        self._is_running = False
        self._failure_event.set()
        self._ready_event.clear()
        self._finalized.set()
        if not already_failed and not self._closing and self.on_error:
            self.on_error(TranscriptionError(title="Cloudflare Grok STT", message=message))

    async def send_audio(self, processed_chunk: Union[bytes, str], capture_time: float):
        if not self.ws or not self._is_running or not self._ready_event.is_set() or self._ending:
            raise ConnectionError("Cloudflare Grok STT is not ready for audio")
        if not isinstance(processed_chunk, bytes):
            raise TypeError("Grok streaming expects PCM16 bytes")
        if not processed_chunk:
            return
        try:
            await self.ws.send(processed_chunk)
            self._has_audio = True
        except Exception:
            self._fail("The audio connection closed. Please reconnect.")
            raise ConnectionError("Cloudflare Grok audio transport failed") from None

    async def finish_utterance(self):
        async with self._finish_lock:
            if self._done_received:
                return
            if not self.ws or not self._is_running:
                if self._has_audio:
                    raise ConnectionError("Grok disconnected before the final transcript")
                return
            # audio.done is a session-wide drain, so earlier phrase finals never
            # cause this wait to finish before newer queued audio is processed.
            self._ending = True
            self._finalized.clear()
            try:
                await self.ws.send(json.dumps({"type": "audio.done"}))
                await asyncio.wait_for(self._finalized.wait(), self.stop_timeout * 0.8)
                if not self._done_received or self._failure_event.is_set():
                    raise ConnectionError("Grok disconnected before the final transcript")
            except asyncio.CancelledError:
                self._fail("Transcription finalization was interrupted. Please reconnect.")
                raise
            except TimeoutError:
                self._fail("The final transcript did not arrive. Please reconnect.")
                raise TimeoutError("Grok final transcript timed out") from None
            except Exception:
                self._fail("Could not finish transcription. Please reconnect.")
                raise ConnectionError("Grok finalization failed") from None

    def reset_utterance(self):
        # A drained Grok connection cannot be reused. Preserve pending audio and
        # deduplication until start() creates the next session.
        return None

    @staticmethod
    def _bounds(event):
        start = event.get("start")
        duration = event.get("duration")
        if isinstance(start, (int, float)) and isinstance(duration, (int, float)):
            return float(start), float(start + duration)
        return None

    def _emit_utterance(self, event):
        text = event.get("text", "").strip()
        bounds = self._bounds(event)
        if bounds and bounds[1] <= self._emitted_end:
            return
        if text:
            self.on_final(text)
            self._emitted_text.append(text)
        if bounds:
            self._emitted_end = max(self._emitted_end, bounds[1])
            self._chunks = {k: v for k, v in self._chunks.items() if k >= bounds[1]}
        else:
            self._chunks.clear()

    def _emit_terminal_remainder(self, event):
        text = event.get("text", "").strip()
        if not text and not event.get("words"):
            # Cloudflare can send only a terminal acknowledgment after phrase finals.
            remaining = " ".join(self._chunks[start] for start in sorted(self._chunks)).strip()
            if remaining:
                self.on_final(remaining)
            self._chunks.clear()
            return
        if not self._emitted_text:
            if text:
                self.on_final(text)
            return
        # A transcript.done payload includes the complete session, not just the current
        # phrase. Prefer word timestamps to retain repeated identical phrases.
        words = event.get("words")
        if words and all(isinstance(w.get("start"), (int, float)) for w in words):
            remainder = " ".join(
                w.get("text", "") for w in words if w["start"] >= self._emitted_end
            ).strip()
        else:
            tokens = text.split()
            emitted = " ".join(self._emitted_text).split()
            if tokens[: len(emitted)] != emitted:
                # Without timestamps or a shared prefix, inserting the whole
                # session would duplicate text. Fail visibly instead of silently
                # dropping or reinserting an unidentifiable remainder.
                raise ValueError("Cannot identify the final Grok transcript remainder")
            remainder = " ".join(tokens[len(emitted) :])
        if remainder:
            self.on_final(remainder)

    async def _handle_event(self, event: dict):
        if not self._is_running:
            return
        kind = event.get("type")
        if kind == "transcript.created":
            self._ready_event.set()
            if self.on_status:
                self.on_status(STATUS_READY)
        elif kind == "error":
            # Never show server messages that may echo credentials or audio.
            self._fail("Grok rejected the stream. Check model access and credentials.")
        elif kind == "transcript.partial":
            bounds = self._bounds(event)
            if bounds and bounds[1] <= self._emitted_end:
                return
            if event.get("is_final") and event.get("speech_final"):
                self._emit_utterance(event)
            else:
                text = event.get("text", "").strip()
                if event.get("is_final") and bounds:
                    self._chunks[bounds[0]] = text
                    text = " ".join(self._chunks[k] for k in sorted(self._chunks))
                if text:
                    self.on_partial(text)
        elif kind == "transcript.done":
            self._emit_terminal_remainder(event)
            self._done_received = True
            self._has_audio = False
            self._is_running = False
            self._ready_event.clear()
            self._finalized.set()

    async def _receive_loop(self):
        try:
            async for message in self.ws:
                await self._handle_event(json.loads(message))
        except asyncio.CancelledError:
            raise
        except Exception:
            if not self._closing:
                self._fail("The Grok transcription connection failed. Please reconnect.")
        finally:
            if not self._closing and not self._done_received:
                self._fail("The Grok transcription connection closed. Please reconnect.")

    async def _do_stop(self):
        self._closing = True
        self._is_running = False
        self._ready_event.clear()
        self._finalized.set()
        ws, self.ws = self.ws, None
        task, self._receive_task = self._receive_task, None
        if task:
            task.cancel()
        try:
            if ws:
                await ws.close()
        finally:
            if task:
                await asyncio.gather(task, return_exceptions=True)
