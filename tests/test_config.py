import pytest

from engine.config import ConfigError, load_config


def test_load_config_missing_file():
    with pytest.raises(ConfigError, match="Configuration file not found"):
        load_config("non_existent.toml")


def test_load_config_invalid_toml(tmp_path):
    config_file = tmp_path / "invalid.toml"
    config_file.write_text("invalid = toml = format")
    with pytest.raises(ConfigError, match="Invalid TOML format"):
        load_config(config_file)


def test_load_config_valid(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
active_provider = "assemblyai"
openai_api_key = "op_key"
assemblyai_api_key = "as_key"

[hotkeys]
hotkey = "ctrl+v"
hold_mode = false

[transcription]
language = "es"
sample_rate = 44100
""")
    config = load_config(config_file)
    assert config.active_provider == "assemblyai"
    assert config.openai_api_key == "op_key"
    assert config.assemblyai_api_key == "as_key"
    assert config.hotkeys.hotkey == "ctrl+v"
    assert config.hotkeys.hold_mode is False
    assert config.transcription.language == "es"
    assert config.transcription.sample_rate == 44100


def test_config_validation_error(tmp_path):
    config_file = tmp_path / "invalid_values.toml"
    config_file.write_text("""
active_provider = "invalid_provider"
openai_api_key = 123
""")
    with pytest.raises(ConfigError, match="Configuration validation failed"):
        load_config(config_file)
