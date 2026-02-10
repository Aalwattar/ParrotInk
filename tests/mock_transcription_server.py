import asyncio
import json
import os

import websockets


async def mock_openai_handler(websocket):
    print("OpenAI Client connected", flush=True)
    last_send_time = 0
    try:
        async for message in websocket:
            data = json.loads(message)
            if data.get("type") == "input_audio_buffer.append":
                current_time = asyncio.get_event_loop().time()
                # Rate limit: Only send a response every 3 seconds max
                if current_time - last_send_time > 3.0:
                    last_send_time = current_time
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "conversation.item.input_audio_transcription.completed",
                                "transcript": "Hello from mock OpenAI!",
                            }
                        )
                    )
    except Exception as e:
        print(f"OpenAI Handler Error: {e}", flush=True)


async def mock_assemblyai_handler(websocket):
    print("AssemblyAI Client connected", flush=True)
    last_send_time = 0
    try:
        async for message in websocket:
            data = json.loads(message)
            if "audio_data" in data:
                current_time = asyncio.get_event_loop().time()
                if current_time - last_send_time > 3.0:
                    last_send_time = current_time
                    await websocket.send(
                        json.dumps({"message_type": "PartialTranscript", "text": "Hello"})
                    )
                    await asyncio.sleep(0.1)
                    await websocket.send(
                        json.dumps(
                            {
                                "message_type": "FinalTranscript",
                                "text": "Hello from mock AssemblyAI!",
                            }
                        )
                    )
    except Exception as e:
        print(f"AssemblyAI Handler Error: {e}", flush=True)


async def main():
    print(f"Starting mock servers on PID {os.getpid()}...", flush=True)
    try:
        server1 = await websockets.serve(mock_openai_handler, "127.0.0.1", 8081)
        server2 = await websockets.serve(mock_assemblyai_handler, "127.0.0.1", 8082)
        print("Mock servers are now LISTENING on 127.0.0.1:8081 and 8082", flush=True)
        await asyncio.Future()  # run forever
    except Exception as e:
        print(f"FATAL Server Error: {e}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
