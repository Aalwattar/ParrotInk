import pytest

from engine.config import load_config


def test_load_config_new_audio_section(tmp_path):
    config_file = tmp_path / "audio_config.toml"
    config_file.write_text("""
default_provider = "openai"

[audio]
capture_sample_rate = 44100
chunk_ms = 50
""")
    config = load_config(config_file)
    assert config.audio.capture_sample_rate == 44100
    assert config.audio.chunk_ms == 50


def test_load_config_openai_provider(tmp_path):
    config_file = tmp_path / "openai_config.toml"
    config_file.write_text("""
default_provider = "openai"

[providers.openai.tier1]
realtime_ws_url_base = "wss://custom.openai.com"
model = "gpt-4o-transcribe"
language = "en"
prompt = "context"
input_audio_type = "audio/pcm"
input_audio_rate = 24000

[providers.openai.tier2]
noise_reduction = "off"
turn_detection_type = "server_vad"
vad_threshold = 0.8
prefix_padding_ms = 100
silence_duration_ms = 200
include_logprobs = true
""")
    config = load_config(config_file)
    # Check core (Tier 1)
    assert config.providers.openai.core.realtime_ws_url_base == "wss://custom.openai.com"
    assert config.providers.openai.core.model == "gpt-4o-transcribe"
    assert config.providers.openai.core.language == "en"
    assert config.providers.openai.core.prompt == "context"
    assert config.providers.openai.core.input_audio_type == "audio/pcm"
    assert config.providers.openai.core.input_audio_rate == 24000

    # Check advanced (Tier 2)
    assert config.providers.openai.advanced.noise_reduction == "off"
    assert config.providers.openai.advanced.turn_detection_type == "server_vad"
    assert config.providers.openai.advanced.vad_threshold == 0.8
    assert config.providers.openai.advanced.prefix_padding_ms == 100
    assert config.providers.openai.advanced.silence_duration_ms == 200
    assert config.providers.openai.advanced.include_logprobs is True


def test_load_config_assemblyai_provider(tmp_path):
    config_file = tmp_path / "assemblyai_config.toml"
    config_file.write_text("""
default_provider = "assemblyai"

[providers.assemblyai.tier1]
ws_url = "wss://custom.assemblyai.com"
sample_rate = 48000
vad_threshold = 0.3
encoding = "pcm_mulaw"
speech_model = "universal-streaming-multilingual"
keyterms_prompt = ["foo", "bar"]
inactivity_timeout_seconds = 60

[providers.assemblyai.tier2]
end_of_turn_confidence_threshold = 0.6
min_end_of_turn_silence_when_confident_ms = 300
max_turn_silence_ms = 1000
format_turns = true
language_detection = true
""")
    config = load_config(config_file)

    # Check core (Tier 1)
    assert config.providers.assemblyai.core.ws_url == "wss://custom.assemblyai.com"
    assert config.providers.assemblyai.core.sample_rate == 48000
    assert config.providers.assemblyai.core.vad_threshold == 0.3
    assert config.providers.assemblyai.core.encoding == "pcm_mulaw"
    assert config.providers.assemblyai.core.speech_model == "universal-streaming-multilingual"
    assert config.providers.assemblyai.core.keyterms_prompt == ["foo", "bar"]
    assert config.providers.assemblyai.core.inactivity_timeout_seconds == 60

    # Check advanced (Tier 2)
    assert config.providers.assemblyai.advanced.end_of_turn_confidence_threshold == 0.6
    assert config.providers.assemblyai.advanced.min_end_of_turn_silence_when_confident_ms == 300
    assert config.providers.assemblyai.advanced.max_turn_silence_ms == 1000
    assert config.providers.assemblyai.advanced.format_turns is True
    assert config.providers.assemblyai.advanced.language_detection is True


def test_legacy_advanced_removed(tmp_path):
    config_file = tmp_path / "legacy.toml"
    config_file.write_text("""
default_provider = "openai"
[advanced]
openai_url = "old"
""")
    # It should load but 'advanced' attribute should not exist or not have old fields
    config = load_config(config_file)
    with pytest.raises(AttributeError):
        _ = config.advanced.openai_url
