import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Fix: Ensure the project root is in sys.path so 'engine' can be imported
sys.path.append(str(Path(__file__).parent.parent))

import numpy as np
import sounddevice as sd
import websockets

try:
    from engine.security import SecurityManager
except ImportError:
    print("ERROR: Could not import engine.security. Please run from project root.")
    sys.exit(1)

# Constants
SAMPLE_RATE = 16000
CHUNK_SIZE = 1600  # 100ms


def get_api_key():
    # 1. Try environment
    key = os.getenv("ASSEMBLYAI_API_KEY")
    if key:
        return key

    # 2. Try Windows Credential Manager
    try:
        key = SecurityManager.get_key("assemblyai_api_key")
        if key:
            return key
    except Exception:
        pass

    # 3. Try config.toml using standard tomllib (Python 3.11+)
    try:
        import tomllib

        config_path = Path("config.toml")
        if config_path.exists():
            with open(config_path, "rb") as f:
                config = tomllib.load(f)
                key = config.get("credentials", {}).get("assemblyai_api_key")
                if key:
                    return key
    except Exception:
        pass

    return None


API_KEY = get_api_key()

if not API_KEY:
    print("ERROR: ASSEMBLYAI_API_KEY not found.")
    sys.exit(1)


async def send_audio(ws):
    print(f"Starting audio capture at {SAMPLE_RATE}Hz...")

    def callback(indata, frames, time_info, status):
        if status:
            print(status, file=sys.stderr)
        audio_int16 = (indata * 32767).astype(np.int16)
        # Use call_soon_threadsafe to send over the websocket from the audio thread
        loop.call_soon_threadsafe(asyncio.create_task, ws.send(audio_int16.tobytes()))

    loop = asyncio.get_running_loop()
    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=callback, blocksize=CHUNK_SIZE
    ):
        while True:
            await asyncio.sleep(1)


async def receive_transcripts(ws):
    print("Listening for transcripts...")
    start_time = time.time()
    try:
        async for message in ws:
            data = json.loads(message)
            msg_type = data.get("type") or data.get("message_type")
            text = data.get("transcript") or data.get("text")

            elapsed = time.time() - start_time
            if text:
                print(f"[{elapsed:6.2f}s] [{msg_type:15}] {text}")
                if data.get("end_of_turn"):
                    print(f"[{elapsed:6.2f}s] --- END OF TURN ---")
            elif msg_type == "SessionBegins":
                print(f"[{elapsed:6.2f}s] Session started: {data.get('session_id')}")

    except websockets.exceptions.ConnectionClosed:
        print("Connection closed")


async def main():
    # V3 URL
    url = (
        f"wss://streaming.assemblyai.com/v3/ws?sample_rate={SAMPLE_RATE}"
        f"&utterance_silence_threshold=300"
    )
    headers = {"Authorization": API_KEY}

    print(f"Connecting to {url}...")
    try:
        async with websockets.connect(url, additional_headers=headers) as ws:
            await asyncio.gather(send_audio(ws), receive_transcripts(ws))
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
