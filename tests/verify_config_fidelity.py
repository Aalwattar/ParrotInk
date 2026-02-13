import json
import urllib.parse

import pytest

from engine.config import Config
from engine.transcription.assemblyai_provider import AssemblyAIProvider


@pytest.fixture
def custom_config():
    config = Config()
    config.providers.assemblyai.advanced.end_of_turn_confidence_threshold = 0.5
    config.providers.assemblyai.advanced.min_end_of_turn_silence_when_confident_ms = 500
    config.providers.assemblyai.advanced.max_turn_silence_ms = 2000
    return config


def test_assemblyai_url_honors_config(custom_config):
    provider = AssemblyAIProvider(
        api_key="test", on_partial=lambda x: None, on_final=lambda x: None, config=custom_config
    )

    url = provider._build_url()
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)

    assert params["end_of_turn_confidence_threshold"][0] == "0.5"
    assert params["min_end_of_turn_silence_when_confident"][0] == "500"
    assert params["max_turn_silence"][0] == "2000"


@pytest.fixture
def openai_config():
    config = Config()
    config.providers.openai.advanced.vad_threshold = 0.7
    config.providers.openai.advanced.prefix_padding_ms = 450
    config.providers.openai.advanced.silence_duration_ms = 600
    config.providers.openai.advanced.noise_reduction = "auto"
    return config


@pytest.mark.asyncio
async def test_openai_session_update_honors_config(openai_config):
    from unittest.mock import AsyncMock

    from engine.transcription.openai_provider import OpenAIProvider

    provider = OpenAIProvider(
        api_key="test", on_partial=lambda x: None, on_final=lambda x: None, config=openai_config
    )

    provider.ws = AsyncMock()
    await provider._update_session()

    assert provider.ws.send.called
    sent_json = json.loads(provider.ws.send.call_args[0][0])
    turn_detection = sent_json["session"]["audio"]["input"]["turn_detection"]

    assert turn_detection["threshold"] == 0.7
    assert turn_detection["prefix_padding_ms"] == 450
    assert turn_detection["silence_duration_ms"] == 600
    assert sent_json["session"]["audio"]["input"]["noise_reduction"] == "auto"
