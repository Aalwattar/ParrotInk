import asyncio
import base64
import json
import numpy as np
import websockets
from typing import Callable, Optional
from .base import BaseProvider

class AssemblyAIProvider(BaseProvider):
    """AssemblyAI real-time transcription provider."""

    def __init__(self, api_key: str, on_partial: Callable[[str], None], on_final: Callable[[str], None], sample_rate: int = 16000):
        super().__init__(api_key, on_partial, on_final)
        self.sample_rate = sample_rate
        self.url = f"ws://127.0.0.1:8082"
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self._receive_task: Optional[asyncio.Task] = None
        self.is_running = False

    async def start(self):
        """Connect to AssemblyAI and start receiving events."""
        headers = {
            "Authorization": self.api_key
        }
        try:
            self.ws = await websockets.connect(self.url)
            self.is_running = True
            
            # AssemblyAI sends a 'SessionBegins' message first
            self._receive_task = asyncio.create_task(self._receive_loop())
            print("Connected to AssemblyAI Realtime API.")
        except Exception as e:
            print(f"Failed to connect to AssemblyAI: {e}")
            raise

    async def stop(self):
        """Close connection and stop tasks."""
        self.is_running = False
        if self.ws:
            # AssemblyAI expects a 'TerminateSession' message
            try:
                await self.ws.send(json.dumps({"terminate_session": True}))
                # Wait a bit for the connection to close gracefully
                await asyncio.sleep(0.5)
            except:
                pass
            
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        if self.ws:
            await self.ws.close()
            self.ws = None
        print("Disconnected from AssemblyAI.")

    async def send_audio(self, audio_chunk: np.ndarray):
        """Send audio chunk as base64 encoded PCM16."""
        if not self.ws or not self.is_running:
            return

        # Convert float32 [-1.0, 1.0] to int16
        audio_int16 = (audio_chunk * 32767).astype(np.int16)
        audio_base64 = base64.b64encode(audio_int16.tobytes()).decode("utf-8")

        event = {
            "audio_data": audio_base64
        }
        await self.ws.send(json.dumps(event))

    async def _receive_loop(self):
        """Listen for transcription events."""
        try:
            async for message in self.ws:
                event = json.loads(message)
                await self._handle_event(event)
        except websockets.exceptions.ConnectionClosed:
            print("AssemblyAI connection closed.")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in AssemblyAI receive loop: {e}")

    async def _handle_event(self, event: dict):
        """Process incoming events."""
        message_type = event.get("message_type")
        
        if message_type == "PartialTranscript":
            transcript = event.get("text", "")
            if transcript:
                self.on_partial(transcript)
        
        elif message_type == "FinalTranscript":
            transcript = event.get("text", "")
            if transcript:
                self.on_final(transcript)
        
        elif message_type == "SessionTerminated":
            print("AssemblyAI session terminated.")
        
        elif event.get("error"):
            print(f"AssemblyAI API Error: {event.get('error')}")
