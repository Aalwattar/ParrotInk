"""Exercise real local WebSocket transport with current provider wire contracts."""

import base64
import json

import pytest
from websockets.asyncio.server import serve

from engine.config import Config
from engine.config_resolver import resolve_effective_config
from engine.transcription.assemblyai_provider import AssemblyAIProvider
from engine.transcription.cloudflare_provider import CloudflareProvider
from engine.transcription.openai_provider import OpenAIProvider
from tests.mock_transcription_server import mock_assemblyai_handler, mock_openai_handler


async def mock_nova(socket):
    async for message in socket:
        if isinstance(message, bytes):
            await socket.send(
                json.dumps(
                    {
                        "type": "Results",
                        "channel": {"alternatives": [{"transcript": "Local test"}]},
                        "is_final": False,
                    "start": 0.0,
                    "duration": 0.1,
                    }
                )
            )
        elif json.loads(message).get("type") == "Finalize":
            await socket.send(
                json.dumps(
                    {
                        "type": "Results",
                        "channel": {"alternatives": [{"transcript": "Local test."}]},
                        "is_final": True,
                        "from_finalize": True,
                        "start": 0.0,
                        "duration": 0.1,
                    }
                )
            )
        elif json.loads(message).get("type") == "CloseStream":
            break


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["openai", "assemblyai", "cloudflare"])
async def test_real_websocket_recording_finishes_without_losing_final(name):
    handlers = {
        "openai": mock_openai_handler,
        "assemblyai": mock_assemblyai_handler,
        "cloudflare": mock_nova,
    }
    finals = []
    errors = []
    async with serve(handlers[name], "127.0.0.1", 0) as server:
        url = f"ws://127.0.0.1:{server.sockets[0].getsockname()[1]}"
        config = Config()
        config.test.enabled = True
        setattr(config.test, f"{name}_mock_url", url)
        effective = resolve_effective_config(config)
        provider_types = {
            "openai": OpenAIProvider,
            "assemblyai": AssemblyAIProvider,
            "cloudflare": CloudflareProvider,
        }
        provider = provider_types[name](
            "", lambda text: None, finals.append, getattr(effective, name), on_error=errors.append
        )
        try:
            await provider.start()
            await provider.wait_for_ready(timeout=1)
            await provider.notify_voice_activity(True, 0.1)
            pcm = bytes(4800 if name == "openai" else 3200)
            await provider.send_audio(
                base64.b64encode(pcm).decode("ascii") if name == "openai" else pcm, 0.1
            )
            await provider.finish_utterance()
            assert len(finals) == 1
            assert finals[0].strip()
            assert provider.is_running
            assert not errors
        finally:
            await provider.stop()
        assert provider.ws is None
