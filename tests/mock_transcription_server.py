import asyncio
import json
import websockets

async def mock_openai_handler(websocket):
    print("Mock OpenAI Client connected")
    try:
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "session.update":
                print("Mock OpenAI: Session updated")
            elif msg_type == "input_audio_buffer.append":
                # Simulate a final transcription after receiving some audio
                response = {
                    "type": "conversation.item.input_audio_transcription.completed",
                    "transcript": "Hello from mock OpenAI!"
                }
                await websocket.send(json.dumps(response))
    except websockets.exceptions.ConnectionClosed:
        print("Mock OpenAI Client disconnected")

async def mock_assemblyai_handler(websocket):
    print("Mock AssemblyAI Client connected")
    try:
        async for message in websocket:
            data = json.loads(message)
            
            if "audio_data" in data:
                # Simulate partial and then final
                partial = {
                    "message_type": "PartialTranscript",
                    "text": "Hello"
                }
                await websocket.send(json.dumps(partial))
                
                final = {
                    "message_type": "FinalTranscript",
                    "text": "Hello from mock AssemblyAI!"
                }
                await websocket.send(json.dumps(final))
    except websockets.exceptions.ConnectionClosed:
        print("Mock AssemblyAI Client disconnected")

async def main():
    async with websockets.serve(mock_openai_handler, "0.0.0.0", 8081):
        async with websockets.serve(mock_assemblyai_handler, "0.0.0.0", 8082):
            print("Mock servers running on 0.0.0.0: OpenAI on :8081, AssemblyAI on :8082")
            await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
