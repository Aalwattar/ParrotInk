import asyncio
import base64
import json
from typing import Callable, Optional

import numpy as np
import websockets

from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    """OpenAI Realtime API transcription provider."""

    def __init__(
        self,
        api_key: str,
        on_partial: Callable[[str], None],
        on_final: Callable[[str], None],
        base_url: str,
    ):
        super().__init__(api_key, on_partial, on_final, base_url)
        self.url = base_url
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self._receive_task: Optional[asyncio.Task] = None
        self.is_running = False

    async def start(self):
        """Connect to OpenAI and start receiving events."""
        headers = {"Authorization": f"Bearer {self.api_key}", "OpenAI-Beta": "realtime=v1"}
        try:
            self.ws = await websockets.connect(self.url)
            self.is_running = True

            # Initialize session for transcription only
            await self._initialize_session()

            self._receive_task = asyncio.create_task(self._receive_loop())
            print("Connected to OpenAI Realtime API.")
        except Exception as e:
            print(f"Failed to connect to OpenAI: {e}")
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
        print("Disconnected from OpenAI.")

    async def send_audio(self, audio_chunk: np.ndarray):
        """Send audio chunk as base64 encoded PCM16."""
        if not self.ws or not self.is_running:
            return

        # Convert float32 [-1.0, 1.0] to int16
        audio_int16 = (audio_chunk * 32767).astype(np.int16)
        audio_base64 = base64.b64encode(audio_int16.tobytes()).decode("utf-8")

        event = {"type": "input_audio_buffer.append", "audio": audio_base64}
        await self.ws.send(json.dumps(event))

    async def _initialize_session(self):
        """Configure session for audio-to-text only (no voice response needed)."""
        session_update = {
            "type": "session.update",
            "session": {
                "modalities": ["text"],
                "input_audio_format": "pcm16",
                "input_audio_transcription": {"model": "whisper-1"},
                "turn_detection": None,  # We handle manual start/stop
            },
        }
        await self.ws.send(json.dumps(session_update))

    async def _receive_loop(self):
        """Listen for transcription events."""
        try:
            async for message in self.ws:
                event = json.loads(message)
                await self._handle_event(event)
        except websockets.exceptions.ConnectionClosed:
            print("OpenAI connection closed.")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in OpenAI receive loop: {e}")

    async def _handle_event(self, event: dict):
        """Process incoming events."""
        event_type = event.get("type")

        if event_type == "conversation.item.input_audio_transcription.completed":
            transcript = event.get("transcript", "")
            if transcript:
                self.on_final(transcript)

        elif event_type == "error":
            print(f"OpenAI API Error: {event.get('error')}")
