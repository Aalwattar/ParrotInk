import asyncio
import json
import os
import sys
import time
import wave
from pathlib import Path

# Ensure the project root is in sys.path
sys.path.append(str(Path(__file__).parent.parent))

import websockets

try:
    from engine.security import SecurityManager
except ImportError:
    print("ERROR: Could not import engine.security.")
    sys.exit(1)

SAMPLE_RATE = 16000
CHUNK_SIZE = 1600  # 100ms
WAV_FILE = "tests/sample.wav"
LOG_FILE = "aai_debug_u3_pro.json"


def get_api_key():
    key = os.getenv("ASSEMBLYAI_API_KEY")
    if key:
        return key
    try:
        key = SecurityManager.get_key("assemblyai_api_key")
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
    print(f"Sending audio from {WAV_FILE}...")
    with wave.open(WAV_FILE, "rb") as wf:
        # Simple wav reading logic
        if wf.getframerate() != SAMPLE_RATE:
            print(f"Warning: Wav samplerate {wf.getframerate()} != {SAMPLE_RATE}")

        data = wf.readframes(CHUNK_SIZE // 2)  # 16-bit mono
        while data:
            await ws.send(data)
            await asyncio.sleep(0.1)  # Simulate real-time streaming
            data = wf.readframes(CHUNK_SIZE // 2)

    print("Finished sending audio. Waiting for final transcripts...")
    # Send an end of audio message or just wait for the websocket to close
    # AssemblyAI V3 doesn't have an explicit 'end' message like some others,
    # but we can just wait for all turns to complete.
    await asyncio.sleep(5)


async def receive_transcripts(ws, log_handle):
    print("Listening for transcripts...")
    start_time = time.time()
    try:
        async for message in ws:
            print(f"DEBUG: Received message: {message[:100]}...")  # Log first 100 chars
            data = json.loads(message)
            elapsed = time.time() - start_time
            data["_elapsed_s"] = elapsed

            log_handle.write(json.dumps(data) + "\n")
            log_handle.flush()

            msg_type = data.get("type")
            text = data.get("transcript")
            end_of_turn = data.get("end_of_turn", False)

            if msg_type == "Turn":
                status = "FINAL" if end_of_turn else "PARTIAL"
                print(f"[{elapsed:6.2f}s] [{status:10}] {text}")
                if end_of_turn:
                    print(f"[{elapsed:6.2f}s] --- END OF TURN ---")
            elif msg_type == "Begin":
                print(f"[{elapsed:6.2f}s] Session started: {data.get('id')}")
            elif msg_type == "SpeechStarted":
                print(f"[{elapsed:6.2f}s] Speech detected")

    except websockets.exceptions.ConnectionClosed:
        print("Connection closed")


async def main():
    # V3 URL with u3-rt-pro model and instructional prompting
    model = "u3-rt-pro"

    url = f"wss://streaming.assemblyai.com/v3/ws?sample_rate={SAMPLE_RATE}&speech_model={model}"
    headers = {"Authorization": API_KEY}

    print(f"Connecting to {url}...")
    with open(LOG_FILE, "w") as f:
        try:
            async with websockets.connect(url, additional_headers=headers) as ws:
                # Use a wait_for to ensure the script doesn't hang if something fails
                await asyncio.wait_for(
                    asyncio.gather(send_audio(ws), receive_transcripts(ws, f)),
                    timeout=60,  # Max 60 seconds for the whole test
                )
        except asyncio.TimeoutError:
            print("Test timed out (intentional limit).")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
