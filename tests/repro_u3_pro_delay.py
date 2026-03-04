import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).parent.parent))

import numpy as np
import sounddevice as sd
import websockets

try:
    from engine.security import SecurityManager
except ImportError:
    print("ERROR: Could not import engine.security.")
    sys.exit(1)

SAMPLE_RATE = 16000
CHUNK_SIZE = 1600  # 100ms


def get_api_key():
    key = os.getenv("ASSEMBLYAI_API_KEY")
    if key:
        return key
    try:
        return SecurityManager.get_key("assemblyai_api_key")
    except Exception:
        pass
    return None


API_KEY = get_api_key()
if not API_KEY:
    print("ERROR: ASSEMBLYAI_API_KEY not found.")
    sys.exit(1)


async def send_audio(ws, loop):
    print("Starting audio capture...")

    def callback(indata, frames, time_info, status):
        if status:
            print(status, file=sys.stderr)
        audio_int16 = (indata * 32767).astype(np.int16)
        loop.call_soon_threadsafe(asyncio.create_task, ws.send(audio_int16.tobytes()))

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

            # Detailed logging
            print(f"[{elapsed:7.3f}s] {msg_type:15} | {text if text else '-'}")

            if data.get("end_of_turn"):
                print(f"[{elapsed:7.3f}s] --- TURN FINALIZED ---")
    except websockets.exceptions.ConnectionClosed:
        print("Connection closed")


async def main(model, prompt=None):
    params = {
        "sample_rate": SAMPLE_RATE,
        "encoding": "pcm_s16le",
        "speech_model": model,
        "format_turns": "true",
    }
    if prompt:
        params["prompt"] = prompt

    url = f"wss://streaming.assemblyai.com/v3/ws?{urlencode(params)}"
    headers = {"Authorization": API_KEY}

    print(f"Connecting to {model}...")
    try:
        async with websockets.connect(url, additional_headers=headers) as ws:
            loop = asyncio.get_running_loop()
            await asyncio.gather(send_audio(ws, loop), receive_transcripts(ws))
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="universal-streaming-english")
    parser.add_argument("--prompt", default=None)
    args = parser.parse_args()

    try:
        asyncio.run(main(args.model, args.prompt))
    except KeyboardInterrupt:
        print("\nExiting...")
