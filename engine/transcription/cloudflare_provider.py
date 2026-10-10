"""Deepgram streaming speech recognition through Cloudflare AI Gateway.

This adapter implements the Nova and Flux wire protocols documented by
Cloudflare and Deepgram.
"""

import asyncio
import json
import time
from collections import deque
from typing import Callable, Optional, Union

import websockets.asyncio.client as websockets

from engine.app_types import EffectiveCloudflareConfig, TranscriptionError
from engine.audio.adapter import ProviderAudioSpec
from engine.constants import STATUS_READY
from engine.logging import get_logger
from engine.security import SecurityManager

from .base import BaseProvider

logger = get_logger("Cloudflare")


class CloudflareProvider(BaseProvider):
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
        self._receive_task = None
        self._keepalive_task = None
        self._finalized = asyncio.Event()
        self._has_audio = False
        self._pending_result = False
        self._pending_results: set[tuple] = set()
        self._flush_acknowledged = False
        self._has_final_result = False
        self._last_audio = time.monotonic()
        self._seen: set[tuple] = set()
        self._seen_order: deque[tuple] = deque()
        self._finish_lock = asyncio.Lock()

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
        self._closing = False
        self._has_audio = False
        self._pending_result = False
        self._pending_results.clear()
        self._flush_acknowledged = False
        self._has_final_result = False
        self._seen.clear()
        self._seen_order.clear()
        if not SecurityManager.is_url_trusted(self.base_url, is_test=self.effective_config.is_test):
            raise ConnectionError("Untrusted Cloudflare Gateway endpoint")
        headers = {
            "cf-aig-authorization": f"Bearer {self.api_key}",
            "cf-aig-collect-log-payload": "false",
        }
        self.ws = await websockets.connect(
            self.base_url,
            additional_headers=None if self.effective_config.is_test else headers,
            proxy=None if self.effective_config.is_test else True,
        )
        self._is_running = True
        self._last_audio = time.monotonic()
        self._receive_task = asyncio.create_task(self._receive_loop())
        self._keepalive_task = asyncio.create_task(self._keepalive_loop())
        # Nova's successful HTTP upgrade is its readiness acknowledgement;
        # Flux sends Connected before it accepts its audio stream.
        if self.effective_config.protocol == "deepgram_nova":
            self._mark_ready()

    def _mark_ready(self):
        self._ready_event.set()
        if self.on_status:
            self.on_status(STATUS_READY)

    def _fail(self, message: str):
        was_running = self._is_running
        self._is_running = False
        self._failure_event.set()
        self._ready_event.clear()
        self._finalized.set()
        if was_running and not self._closing and self.on_error:
            self.on_error(TranscriptionError(title="Cloudflare AI Gateway", message=message))

    async def send_audio(self, processed_chunk: Union[bytes, str], capture_time: float):
        if not self.ws or not self._is_running:
            raise ConnectionError("Cloudflare Gateway is disconnected")
        if not isinstance(processed_chunk, bytes):
            raise TypeError("Cloudflare streaming expects PCM16 bytes")
        if not processed_chunk:
            return
        try:
            await self.ws.send(processed_chunk)
            self._has_audio = True
            self._finalized.clear()
            self._last_audio = time.monotonic()
        except Exception:
            self._fail("The audio connection closed. Please reconnect.")
            raise ConnectionError("Cloudflare audio transport failed") from None

    async def finish_utterance(self):
        async with self._finish_lock:
            if not self.ws or not self._is_running or not self._has_audio:
                return
            self._finalized.clear()
            self._flush_acknowledged = False
            message = (
                "ForceEndTurn" if self.effective_config.protocol == "deepgram_flux" else "Finalize"
            )
            try:
                await self.ws.send(json.dumps({"type": message}))
                # Finish before the coordinator's outer finalization deadline.
                await asyncio.wait_for(self._finalized.wait(), self.stop_timeout * 0.8)
            except TimeoutError:
                if (
                    self.effective_config.protocol != "deepgram_nova"
                    or self._pending_result
                    or not self._has_final_result
                ):
                    self._fail("The final transcript did not arrive. Please reconnect.")
                    raise TimeoutError("Cloudflare final transcript timed out") from None
                # Nova may omit from_finalize when its last segment was already
                # final and there is no significant buffered audio left.
            except asyncio.CancelledError:
                self._fail("Transcription finalization was interrupted. Please reconnect.")
                raise
            except Exception:
                self._fail("Could not finish transcription. Please reconnect.")
                raise ConnectionError("Cloudflare finalization failed") from None
            if not self._is_running:
                raise ConnectionError("Cloudflare disconnected before finalization")
            self._has_audio = False

    def reset_utterance(self):
        """Reset local recording state without forgetting session-wide deduplication."""
        self._has_audio = False
        self._pending_result = False
        self._pending_results.clear()
        self._flush_acknowledged = False
        self._has_final_result = False
        self._finalized.clear()

    async def _keepalive_loop(self):
        try:
            while self._is_running and not self._closing:
                await asyncio.sleep(3)
                if not self._is_running or self._closing:
                    break
                if time.monotonic() - self._last_audio >= 3:
                    if self.effective_config.protocol == "deepgram_nova":
                        await self.ws.send(json.dumps({"type": "KeepAlive"}))
                    else:
                        # Flux has no KeepAlive control message. Raw silent
                        # audio keeps an idle stream warm without forcing turns.
                        await self.ws.send(bytes(self.effective_config.sample_rate // 5))
        except asyncio.CancelledError:
            raise
        except Exception:
            self._fail("The idle audio connection closed. Please reconnect.")

    def _is_duplicate(self, key) -> bool:
        if key in self._seen:
            return True
        self._seen.add(key)
        self._seen_order.append(key)
        if len(self._seen_order) > 2048:
            self._seen.discard(self._seen_order.popleft())
        return False

    async def _handle_event(self, event: dict):
        if not self._is_running:
            return
        kind = event.get("type")
        if kind == "Connected":
            self._mark_ready()
        elif kind == "Error" or event.get("error"):
            # Server descriptions can contain echoed input or credentials.
            self._fail(
                "Gateway rejected the stream. Check credentials, model access, and settings."
            )
        elif kind == "Warning" and event.get("code") == "FORCE_END_TURN_NO_ACTIVE_TURN":
            # Flux acknowledges ForceEndTurn this way when the last turn already
            # ended naturally. The stream is drained only if no partial remains.
            if not self._pending_results:
                self._finalized.set()
        elif kind == "Results":
            alternatives = event.get("channel", {}).get("alternatives", [])
            text = alternatives[0].get("transcript", "") if alternatives else ""
            segment: tuple = (tuple(event.get("channel_index", [0])), event.get("start"))
            if event.get("is_final"):
                self._pending_results.discard(segment)
                self._has_final_result = True
                key = (
                    tuple(event.get("channel_index", [0])),
                    event.get("start"),
                    event.get("duration"),
                    text,
                )
                if text.strip() and not self._is_duplicate(key):
                    self.on_final(text)
            elif text.strip():
                self._pending_results.add(segment)
                self.on_partial(text)
            self._pending_result = bool(self._pending_results)
            # A natural speech boundary only finalizes its segment, not audio
            # already queued for another phrase. Wait for the explicit flush.
            if event.get("from_finalize"):
                self._flush_acknowledged = True
            if self._flush_acknowledged and not self._pending_result:
                self._finalized.set()
        elif kind == "TurnInfo":
            text = event.get("transcript", "")
            turn = event.get("turn_index")
            segment = ("flux", turn)
            if event.get("event") == "EndOfTurn":
                self._pending_results.discard(segment)
                self._pending_result = bool(self._pending_results)
                self._has_final_result = True
                if text.strip() and not self._is_duplicate(("flux", turn)):
                    self.on_final(text)
                if not self._pending_result:
                    self._finalized.set()
            elif text.strip() and ("flux", turn) not in self._seen:
                self._pending_results.add(segment)
                self._pending_result = True
                self.on_partial(text)

    async def _receive_loop(self):
        try:
            async for message in self.ws:
                await self._handle_event(json.loads(message))
        except asyncio.CancelledError:
            raise
        except Exception:
            if not self._closing:
                self._fail("The transcription connection failed. Please reconnect.")
        finally:
            if not self._closing:
                self._fail("The transcription connection closed. Please reconnect.")

    async def _do_stop(self):
        self._closing = True
        try:
            if self.ws:
                try:
                    if self._is_running:
                        await self.ws.send(json.dumps({"type": "CloseStream"}))
                finally:
                    await self.ws.close()
        finally:
            self._is_running = False
            self._ready_event.clear()
            self._finalized.set()
            for task in (self._keepalive_task, self._receive_task):
                if task:
                    task.cancel()
            try:
                await asyncio.gather(
                    *(t for t in (self._keepalive_task, self._receive_task) if t),
                    return_exceptions=True,
                )
            finally:
                self.ws = None
