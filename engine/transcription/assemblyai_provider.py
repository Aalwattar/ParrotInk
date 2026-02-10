import asyncio
import base64
import json
import urllib.parse
from typing import Callable, Optional

import numpy as np
import websockets

from .base import BaseProvider
from engine.config import Config
from engine.logging import get_logger

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
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self._receive_task: Optional[asyncio.Task] = None
        self.is_running = False

    def _build_url(self) -> str:
        if self.config.test.enabled:
            return self.config.test.assemblyai_mock_url

        core = self.config.providers.assemblyai.core
        adv = self.config.providers.assemblyai.advanced
        
        # Build V3 query parameters
        params = {
            "sample_rate": core.sample_rate,
            "word_boost": json.dumps(core.keyterms_prompt) if core.keyterms_prompt else None,
            "speech_model": core.speech_model,
            "encoding": core.encoding,
            "vad_threshold": core.vad_threshold,
            "inactivity_timeout": core.inactivity_timeout_seconds if core.inactivity_timeout_seconds > 0 else None,
            "end_of_turn_confidence_threshold": adv.end_of_turn_confidence_threshold,
            "end_of_turn_silence_threshold": adv.min_end_of_turn_silence_when_confident_ms,
            "max_end_of_turn_silence": adv.max_turn_silence_ms,
            "format_turns": "true" if adv.format_turns else "false",
            "detect_language": "true" if adv.language_detection else "false",
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        query_string = urllib.parse.urlencode(params)
        return f"{core.ws_url}?{query_string}"

    async def start(self):
        """Connect to AssemblyAI and start receiving events."""
        headers = {"Authorization": self.api_key}
        logger.info(f"Connecting to AssemblyAI at {self.url}...")
        try:
            self.ws = await websockets.connect(
                self.url, 
                additional_headers=headers if not self.config.test.enabled else None
            )
            self.is_running = True
            self._receive_task = asyncio.create_task(self._receive_loop())
            logger.info("Connected to AssemblyAI successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to AssemblyAI: {e}")
            raise

    async def stop(self):
        """Close connection and stop tasks."""
        if self.ws and self.is_running:
            try:
                # Send end of stream message
                terminate_msg = json.dumps({"terminate_session": True})
                logger.debug(f"Sending termination message: {terminate_msg}")
                await self.ws.send(terminate_msg)
                # Give it a moment to process before hard close
                await asyncio.sleep(0.2)
            except Exception as e:
                logger.debug(f"Error during graceful shutdown: {e}")

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
        logger.info("Disconnected from AssemblyAI.")

    async def send_audio(self, audio_chunk: np.ndarray):
        """Send audio chunk as raw binary PCM16."""
        if not self.ws or not self.is_running:
            return

        # Convert float32 [-1.0, 1.0] to int16
        audio_int16 = (audio_chunk * 32767).astype(np.int16)
        
        # In V3, we send the raw bytes directly, not JSON.
        try:
            logger.debug(f"Sending binary audio chunk ({len(audio_int16.tobytes())} bytes)")
            await self.ws.send(audio_int16.tobytes())
        except websockets.exceptions.ConnectionClosed:
            logger.info("AssemblyAI connection closed while sending audio.")
            self.is_running = False

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

            # V3 uses 'type', while some older patterns use 'message_type'

            msg_type = event.get("type") or event.get("message_type")

            

            # Text can be in 'transcript' (V3 Turn) or 'text' (V3 Transcript types)

            text = event.get("transcript") or event.get("text")

            

            if text is not None:

                # Handle V3 'Turn' objects

                if msg_type == "Turn":

                    if event.get("end_of_turn"):

                        if text: # Only send if not empty

                            logger.info(f"Final transcript received (Turn): {text}")

                            self.on_final(text)

                    else:

                        self.on_partial(text)

                

                # Handle explicit Transcript types

                elif msg_type == "FinalTranscript":

                    logger.info(f"Final transcript received: {text}")

                    self.on_final(text)

                elif msg_type == "PartialTranscript":

                    self.on_partial(text)

    

            elif "error" in event:

                logger.error(f"AssemblyAI API Error: {event.get('error')}")

            elif msg_type == "SessionBegins":

                logger.info(f"AssemblyAI Session Started: {event.get('session_id')}")

    