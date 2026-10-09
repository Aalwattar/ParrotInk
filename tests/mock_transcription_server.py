import asyncio
import json
import os
import time

import websockets


async def mock_openai_handler(websocket):
    print("OpenAI Client connected", flush=True)
    last_send_time = 0.0
    manual_turns = True
    has_audio = False
    turn_order = 0
    previous_item_id = None

    async def emit_turn():
        nonlocal turn_order, previous_item_id, has_audio
        item_id = f"mock-item-{turn_order}"
        await websocket.send(
            json.dumps(
                {
                    "type": "input_audio_buffer.committed",
                    "item_id": item_id,
                    "previous_item_id": previous_item_id,
                }
            )
        )
        await websocket.send(
            json.dumps(
                {
                    "type": "conversation.item.input_audio_transcription.delta",
                    "item_id": item_id,
                    "delta": "Hello from mock OpenAI!",
                }
            )
        )
        await websocket.send(
            json.dumps(
                {
                    "type": "conversation.item.input_audio_transcription.completed",
                    "item_id": item_id,
                    "transcript": "Hello from mock OpenAI!",
                }
            )
        )
        previous_item_id = item_id
        turn_order += 1
        has_audio = False

    try:
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")
            if msg_type in {"session.update", "transcription_session.update"}:
                session = data.get("session", {})
                audio_input = session.get("audio", {}).get("input", session)
                model = audio_input.get("transcription", {}).get(
                    "model", session.get("input_audio_transcription", {}).get("model", "")
                )
                manual_turns = model.startswith(("gpt-live-transcribe", "gpt-transcribe"))
                await websocket.send(json.dumps({"type": "session.updated", "session": session}))
            elif msg_type == "input_audio_buffer.append":
                has_audio = True
                current_time = asyncio.get_event_loop().time()
                if not manual_turns and current_time - last_send_time > 3.0:
                    last_send_time = current_time
                    await emit_turn()
            elif msg_type == "input_audio_buffer.commit" and has_audio:
                await emit_turn()
    except Exception as e:
        print(f"OpenAI Handler Error: {e}", flush=True)


async def mock_assemblyai_handler(websocket):
    print("AssemblyAI Client connected", flush=True)
    turn_order = 0
    has_audio = False

    async def emit_turn():
        nonlocal turn_order, has_audio
        if not has_audio:
            return
        await websocket.send(
            json.dumps(
                {
                    "type": "Turn",
                    "turn_order": turn_order,
                    "transcript": "Hello from mock AssemblyAI!",
                    "end_of_turn": True,
                    "turn_is_formatted": True,
                }
            )
        )
        turn_order += 1
        has_audio = False

    try:
        await websocket.send(
            json.dumps(
                {
                    "type": "Begin",
                    "id": "mock-assembly-session",
                    "expires_at": int(time.time()) + 3600,
                    "configuration": {"model": "universal-3-6-pro"},
                }
            )
        )
        async for message in websocket:
            if isinstance(message, bytes):
                if not has_audio:
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "Turn",
                                "turn_order": turn_order,
                                "transcript": "Hello",
                                "end_of_turn": False,
                            }
                        )
                    )
                has_audio = bool(message) or has_audio
                continue
            data = json.loads(message)
            if data.get("type") == "ForceEndpoint":
                await emit_turn()
            elif data.get("type") == "Terminate":
                await emit_turn()
                await websocket.send(
                    json.dumps(
                        {
                            "type": "Termination",
                            "audio_duration_seconds": 1,
                            "session_duration_seconds": 1,
                        }
                    )
                )
                break
    except Exception as e:
        print(f"AssemblyAI Handler Error: {e}", flush=True)


async def main():
    print(f"Starting mock servers on PID {os.getpid()}...", flush=True)
    try:
        await websockets.serve(mock_openai_handler, "127.0.0.1", 8081)
        await websockets.serve(mock_assemblyai_handler, "127.0.0.1", 8082)
        print("Mock servers are now LISTENING on 127.0.0.1:8081 and 8082", flush=True)
        await asyncio.Future()  # run forever
    except Exception as e:
        print(f"FATAL Server Error: {e}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
