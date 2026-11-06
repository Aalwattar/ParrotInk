"""Recorded-audio transcription through Cloudflare's OpenRouter BYOK route."""

import asyncio
import base64
import io
import wave
from typing import Callable, Optional, Union
from urllib.parse import urlparse

import httpx

from engine.app_types import EffectiveCloudflareConfig, TranscriptionError
from engine.audio.adapter import ProviderAudioSpec
from engine.constants import STATUS_READY
from engine.logging import get_logger
from engine.security import SecurityManager

from .base import BaseProvider
from .catalog import get_model

logger = get_logger("OpenRouter")


class OpenRouterProvider(BaseProvider):
    # shortcut: cap PCM at 16 MiB for base64 JSON; use multipart for longer recordings.
    MAX_AUDIO_BYTES = 16 * 1024 * 1024

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
        self._is_running = False
        self._audio = bytearray()
        self._client: Optional[httpx.AsyncClient] = None
        self._request_task: Optional[asyncio.Task] = None
        self._finish_lock = asyncio.Lock()
        self._timeout = max(
            self.stop_timeout, get_model("cloudflare", effective_config.model).finalization_timeout
        )

    @property
    def is_running(self) -> bool:
        return self._is_running

    def get_type(self) -> str:
        return "cloudflare"

    def get_audio_spec(self) -> ProviderAudioSpec:
        return ProviderAudioSpec(sample_rate_hz=16000, wire_encoding="pcm16_bytes")

    async def start(self):
        parsed = urlparse(self.base_url)
        local_test = self.effective_config.is_test and parsed.hostname in {"localhost", "127.0.0.1"}
        if (
            not SecurityManager.is_url_trusted(self.base_url, self.effective_config.is_test)
            or parsed.scheme not in {"http", "https"}
            or (not local_test and parsed.hostname != "gateway.ai.cloudflare.com")
            or parsed.username is not None
        ):
            raise ConnectionError("Untrusted Cloudflare Gateway endpoint")
        if not self.api_key and not local_test:
            raise ConnectionError("Configure your Cloudflare API token")
        self._failure_event.clear()
        self._ready_event.clear()
        self.reset_utterance()
        headers = {
            "User-Agent": "ParrotInk/1.0",
            "cf-aig-collect-log-payload": "false",
        }
        if not local_test:
            headers["cf-aig-authorization"] = f"Bearer {self.api_key}"
        self._client = httpx.AsyncClient(
            headers=headers,
            follow_redirects=False,
            timeout=self._timeout * 0.9,
        )
        self._is_running = True
        self._ready_event.set()
        logger.info("Ready to record: model=%s rate=16000", self.effective_config.model)
        if self.on_status:
            self.on_status(STATUS_READY)

    def reset_utterance(self):
        if self._audio:
            logger.info("Discarding buffered recording: bytes=%d", len(self._audio))
        self._audio.clear()
        if self._request_task:
            self._request_task.cancel()

    def _fail(self, message: str):
        self._audio.clear()
        self._is_running = False
        self._ready_event.clear()
        self._failure_event.set()
        if self.on_error:
            self.on_error(TranscriptionError(title="OpenRouter transcription", message=message))

    async def send_audio(self, processed_chunk: Union[bytes, str], capture_time: float):
        if not self._is_running:
            raise ConnectionError("OpenRouter transcription is not ready")
        if not isinstance(processed_chunk, bytes) or len(processed_chunk) % 2:
            raise ValueError("OpenRouter expects mono PCM16 bytes")
        if len(self._audio) + len(processed_chunk) > self.MAX_AUDIO_BYTES:
            message = (
                "Recording is too long for OpenRouter. Record shorter sections (under 8 minutes)."
            )
            self._fail(message)
            raise ValueError(message)
        self._audio.extend(processed_chunk)

    async def finish_utterance(self):
        async with self._finish_lock:
            if not self._is_running or not self._audio or self._client is None:
                logger.info(
                    "No recording submitted: running=%s audio_bytes=%d",
                    self._is_running,
                    len(self._audio),
                )
                return
            logger.info(
                "Submitting recording: model=%s audio_bytes=%d duration_seconds=%.2f",
                self.effective_config.model,
                len(self._audio),
                len(self._audio) / 32000,
            )
            wav = io.BytesIO()
            with wave.open(wav, "wb") as writer:
                writer.setnchannels(1)
                writer.setsampwidth(2)
                writer.setframerate(self.get_audio_spec().sample_rate_hz)
                writer.writeframes(self._audio)
            self._audio.clear()
            payload = {
                "model": self.effective_config.model,
                "input_audio": {
                    "data": base64.b64encode(wav.getvalue()).decode("ascii"),
                    "format": "wav",
                },
            }
            if self.effective_config.language:
                payload["language"] = self.effective_config.language
            if self.on_status:
                self.on_status("Transcribing recording...")
            try:
                self._request_task = asyncio.create_task(
                    self._client.post(self.base_url, json=payload)
                )
                # Report an actionable timeout before the coordinator's outer deadline.
                async with asyncio.timeout(self._timeout * 0.9):
                    response = await self._request_task
                logger.info("Transcription response: HTTP %d", response.status_code)
                if not response.is_success:
                    messages = {
                        402: "Insufficient OpenRouter credit. Add funds to OpenRouter.",
                        401: "Check your Cloudflare token and the gateway's saved OpenRouter key.",
                        403: "Access denied. Check gateway permissions and model access.",
                        413: "Recording is too large. Record a shorter section.",
                        429: "OpenRouter is rate limited. Please try again later.",
                    }
                    raise ConnectionError(
                        messages.get(
                            response.status_code,
                            f"OpenRouter transcription failed (HTTP {response.status_code}).",
                        )
                    )
                data = response.json()
                if not isinstance(data, dict) or not isinstance(data.get("text"), str):
                    raise ValueError("Invalid transcription response")
                logger.info("Transcript received: characters=%d", len(data["text"]))
                if self._is_running and data["text"].strip():
                    self.on_final(data["text"])
                elif self._is_running and self.on_status:
                    self.on_status("No speech recognized")
            except asyncio.CancelledError:
                raise
            except (httpx.TimeoutException, TimeoutError):
                message = "OpenRouter transcription timed out. Try a shorter recording."
                self._fail(message)
                raise TimeoutError(message) from None
            except ConnectionError as exc:
                self._fail(str(exc))
                raise
            except Exception:
                message = "Could not transcribe the recording. Check your connection and try again."
                self._fail(message)
                raise ConnectionError(message) from None
            finally:
                self._request_task = None

    async def _do_stop(self):
        self._is_running = False
        self._ready_event.clear()
        self.reset_utterance()
        if self._request_task:
            await asyncio.gather(self._request_task, return_exceptions=True)
        if self._client:
            await self._client.aclose()
            self._client = None
