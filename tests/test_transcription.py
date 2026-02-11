from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from engine.config import Config
from engine.transcription.assemblyai_provider import AssemblyAIProvider


@pytest.fixture
def base_config():
    return Config()


@pytest.mark.asyncio
async def test_assemblyai_v3_turn_events(base_config):
    on_partial = MagicMock()
    on_final = MagicMock()
    provider = AssemblyAIProvider(
        api_key="test_key", on_partial=on_partial, on_final=on_final, config=base_config
    )

    # Test partial turn
    partial_turn = {"type": "Turn", "transcript": "hello world", "end_of_turn": False}
    await provider._handle_event(partial_turn)
    on_partial.assert_called_with("hello world")
    on_final.assert_not_called()

    on_partial.reset_mock()

    # Test final turn
    final_turn = {"type": "Turn", "transcript": "hello world final", "end_of_turn": True}
    await provider._handle_event(final_turn)
    # In my updated code, on_partial is called for EVERY turn message
    on_partial.assert_called_with("hello world final")
    on_final.assert_called_with("hello world final")


@pytest.mark.asyncio
async def test_assemblyai_provider_send_audio(base_config):
    on_partial = MagicMock()
    on_final = MagicMock()
    provider = AssemblyAIProvider(
        api_key="test_key", on_partial=on_partial, on_final=on_final, config=base_config
    )

    with patch("websockets.connect", new_callable=AsyncMock) as mock_connect:
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws

        await provider.start()

        # Provide bytes instead of ndarray, matching the new provider contract
        audio_chunk = b"\x00" * 2048
        await provider.send_audio(audio_chunk, 0.0)

        assert mock_ws.send.called
        sent_data = mock_ws.send.call_args[0][0]
        assert isinstance(sent_data, bytes)
