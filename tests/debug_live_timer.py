import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Ensure the project root is in sys.path
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
LOG_FILE = "live_debug_results.json"
DURATION = 20  # Total test duration in seconds


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


async def main():
    model = "u3-rt-pro"
    # Adding a simple prompt to test the feature
    prompt = "Transcribe clearly with punctuation."
    url = (
        f"wss://streaming.assemblyai.com/v3/ws?sample_rate={SAMPLE_RATE}"
        f"&speech_model={model}"
        f"&prompt={prompt.replace(' ', '+')}"
        f"&min_turn_silence=100"
    )
    headers = {"Authorization": API_KEY}

    print(f"Connecting to {url}...")
    start_time = time.time()

    with open(LOG_FILE, "w") as f:
        try:
            async with websockets.connect(url, additional_headers=headers) as ws:
                print("Session started. Talk now for 20 seconds...")

                # Setup audio capture
                loop = asyncio.get_running_loop()
                audio_count = 0

                def callback(indata, frames, time_info, status):
                    nonlocal audio_count
                    if ws.state == websockets.protocol.State.OPEN:
                        audio_count += 1
                        if audio_count % 10 == 0:
                            print(".", end="", flush=True)  # Print a dot every 1s of audio
                        audio_bytes = (indata * 32767).astype(np.int16).tobytes()
                        loop.call_soon_threadsafe(lambda: asyncio.create_task(ws.send(audio_bytes)))

                stream = sd.InputStream(
                    samplerate=SAMPLE_RATE,
                    channels=1,
                    dtype="float32",
                    callback=callback,
                    blocksize=CHUNK_SIZE,
                )
                stream.start()

                while (time.time() - start_time) < DURATION:
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=0.5)
                        data = json.loads(message)
                        elapsed = time.time() - start_time
                        data["_elapsed_s"] = elapsed

                        f.write(json.dumps(data) + "\n")
                        f.flush()

                        if data.get("type") == "Turn":
                            status = "FINAL" if data.get("end_of_turn") else "PARTIAL"
                            transcript = data.get("transcript", "")
                            if transcript:
                                print(f"[{elapsed:6.2f}s] [{status:10}] {transcript}")
                    except asyncio.TimeoutError:
                        continue

                print(f"\n--- {DURATION} seconds reached, shutting down ---")
                stream.stop()
                stream.close()
                await ws.close()

        except Exception as e:
            print(f"Error during test: {e}")

    print("Test finished. Closing process.")
    os._exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        os._exit(0)
