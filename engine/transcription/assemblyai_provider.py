import asyncio
import json
import urllib.parse
from typing import Callable, Optional, Union

import websockets.asyncio.client
from websockets.asyncio.client import ClientConnection

from engine.audio.adapter import ProviderAudioSpec
from engine.config import LATENCY_PROFILES, Config
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
        config: Config,
    ):
        super().__init__(api_key, on_partial, on_final, "")
        self.config = config
        self.url = self._build_url()
        self.ws: Optional[ClientConnection] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._is_running = False
        self.last_transcript = ""

    @property
    def is_running(self) -> bool:
        return self._is_running

    def get_audio_spec(self) -> ProviderAudioSpec:
        return ProviderAudioSpec(
            sample_rate_hz=self.config.providers.assemblyai.core.sample_rate,
            wire_encoding="pcm16_bytes",
        )

    def get_type(self) -> str:
        return "assemblyai"

    def _build_url(self) -> str:
        if self.config.test.enabled:
            return self.config.test.assemblyai_mock_url

        core = self.config.providers.assemblyai.core
        adv = self.config.providers.assemblyai.advanced
        trans = self.config.transcription

        # 1. Resolve Region URL
        base_url = "wss://streaming.assemblyai.com/v3/ws"
        if core.region == "eu":
            base_url = "wss://streaming.eu.assemblyai.com/v3/ws"

        # 2. Resolve Latency Settings
        if adv.override:
            confidence: float = adv.end_of_turn_confidence_threshold
            min_silence: int = adv.min_end_of_turn_silence_when_confident_ms
            max_silence: int = adv.max_turn_silence_ms
        else:
            profile = LATENCY_PROFILES.get(trans.latency_profile, LATENCY_PROFILES["balanced"])
            aai_params = profile["assemblyai"]
            confidence = float(aai_params["end_of_turn_confidence_threshold"])
            min_silence = int(aai_params["min_end_of_turn_silence_when_confident_ms"])
            max_silence = int(aai_params["max_turn_silence_ms"])

        # 3. Build Query Parameters
        params = {
            "sample_rate": core.sample_rate,
            "word_boost": json.dumps(core.keyterms_prompt) if core.keyterms_prompt else None,
            "speech_model": core.speech_model,
            "encoding": core.encoding,
            "vad_threshold": core.vad_threshold,
            "inactivity_timeout": core.inactivity_timeout_seconds
            if core.inactivity_timeout_seconds > 0
            else None,
            "end_of_turn_confidence_threshold": confidence,
            "min_end_of_turn_silence_when_confident": min_silence,
            "max_turn_silence": max_silence,
            "format_turns": "true" if trans.format_text else "false",
            "detect_language": "true" if adv.language_detection else "false",
        }

        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        query_string = urllib.parse.urlencode(params)
        return f"{base_url}?{query_string}"

    async def start(self):
        """Connect to AssemblyAI and start receiving events."""
        headers = {"Authorization": self.api_key}
        logger.info(f"Connecting to AssemblyAI at {self.url}...")
        try:
            self.ws = await websockets.connect(
                self.url, additional_headers=headers if not self.config.test.enabled else None
            )
            self._is_running = True
            self._receive_task = asyncio.create_task(self._receive_loop())
            logger.info("Connected to AssemblyAI successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to AssemblyAI: {e}")
            raise

    async def stop(self):
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
            await self.ws.close()
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
                    logger.info(f"AssemblyAI Final (Turn): {text}")
                    self.on_final(text)
                    self.last_transcript = ""

            elif msg_type == "FinalTranscript":
                logger.info(f"AssemblyAI Final: {text}")
                self.on_final(text)
            elif msg_type == "PartialTranscript":
                self.on_partial(text)

        elif "error" in event:
            logger.error(f"AssemblyAI API Error: {event.get('error')}")
        elif msg_type == "SessionBegins":
            logger.info(f"AssemblyAI Session Started: {event.get('session_id')}")
