import pytest

from engine.config import Config, ConfigError


def test_load_valid_config(tmp_path):
    """Test loading a valid TOML configuration."""
    config_content = """
    active_provider = "openai"
    openai_api_key = "sk-test-123"
    assemblyai_api_key = "aa-test-456"

    [hotkeys]
    hold_to_talk = "ctrl+alt+v"
    toggle_listen = "ctrl+alt+t"

    [transcription]
    language = "en"
    sample_rate = 16000
    """
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)

    config = Config.from_file(config_file)
    assert config.active_provider == "openai"
    assert config.openai_api_key == "sk-test-123"
    assert config.hotkeys.hold_to_talk == "ctrl+alt+v"
    assert config.transcription.language == "en"


def test_load_config_defaults(tmp_path):
    """Test that default values are applied when optional fields are missing."""
    config_content = """
    active_provider = "openai"
    openai_api_key = "sk-test-123"
    assemblyai_api_key = ""

    [hotkeys]
    hold_to_talk = "v"
    toggle_listen = "t"
    """
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)

    config = Config.from_file(config_file)
    assert config.transcription.language == "en"
    assert config.transcription.sample_rate == 16000


def test_missing_required_fields(tmp_path):
    """Test that missing required fields raises a ConfigError."""
    config_content = """
    active_provider = "openai"
    # missing openai_api_key
    """
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)

    with pytest.raises(ConfigError):
        Config.from_file(config_file)


def test_invalid_provider(tmp_path):
    """Test that an invalid provider raises a ConfigError."""
    config_content = """
    active_provider = "invalid_provider"
    openai_api_key = "sk-123"
    assemblyai_api_key = "aa-123"
    [hotkeys]
    hold_to_talk = "v"
    toggle_listen = "t"
    """
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)

    with pytest.raises(ConfigError):
        Config.from_file(config_file)
