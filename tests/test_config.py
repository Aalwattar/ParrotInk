import pytest
import os
from engine.config import ConfigError, load_config


def test_load_config_missing_file():
    # Now returns a default config instead of raising error
    config = load_config("non_existent.toml")
    assert config.default_provider == "openai"


def test_load_config_invalid_toml(tmp_path):
    config_file = tmp_path / "invalid.toml"
    # Missing closing quote
    config_file.write_text('default_provider = "openai')
    with pytest.raises(ConfigError, match="Invalid TOML format"):
        load_config(config_file)


def test_load_config_misspelled_value(tmp_path):
    config_file = tmp_path / "misspelled.toml"
    # Boolean value with typo
    config_file.write_text("""
default_provider = "openai"
[hotkeys]
hotkey = "v"
hold_mode = fakse
""")
    with pytest.raises(ConfigError, match="Invalid TOML format"):
        load_config(config_file)


def test_load_config_invalid_types(tmp_path):
    config_file = tmp_path / "types.toml"
    # default_provider must be a literal
    config_file.write_text("""
default_provider = "invalid_provider"
[hotkeys]
hold_mode = "true"
""")
    with pytest.raises(ConfigError, match="Configuration validation failed"):
        load_config(config_file)


def test_load_config_valid(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
default_provider = "assemblyai"

[hotkeys]
hotkey = "ctrl+v"
hold_mode = false

[transcription]
language = "es"
sample_rate = 44100
""")
    config = load_config(config_file)
    assert config.default_provider == "assemblyai"
    assert config.hotkeys.hotkey == "ctrl+v"
    assert config.hotkeys.hold_mode is False
    assert config.transcription.language == "es"
    assert config.transcription.sample_rate == 44100


def test_config_advanced_and_test_defaults(tmp_path):
    config_file = tmp_path / "default_test.toml"
    config_file.write_text("""
default_provider = "openai"
""")
    config = load_config(config_file)

    # Test section defaults
    assert config.test.enabled is False
    assert config.test.openai_mock_url == "ws://localhost:8081"
    assert config.test.assemblyai_mock_url == "ws://localhost:8081"

    # Advanced section defaults
    assert (
        config.advanced.openai_url
        == "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
    )
    assert config.advanced.assemblyai_url == "wss://api.assemblyai.com/v2/realtime/ws"


def test_config_overrides(tmp_path):
    config_file = tmp_path / "overrides.toml"
    config_file.write_text("""
default_provider = "openai"

[test]
enabled = true
openai_mock_url = "ws://127.0.0.1:9000"

[advanced]
openai_url = "ws://proxy:1234"
""")
    config = load_config(config_file)

    assert config.test.enabled is True
    assert config.test.openai_mock_url == "ws://127.0.0.1:9000"
    assert config.test.assemblyai_mock_url == "ws://localhost:8081"  # default
    assert config.advanced.openai_url == "ws://proxy:1234"
    assert config.advanced.assemblyai_url == "wss://api.assemblyai.com/v2/realtime/ws"  # default

def test_config_key_resolution(mocker):
    config = load_config("non_existent.toml")
    
    mock_get = mocker.patch("engine.security.SecurityManager.get_key")
    mock_get.side_effect = lambda x: "secret-key" if x == "openai_api_key" else None
    
    assert config.get_openai_key() == "secret-key"
    assert config.get_assemblyai_key() is None

def test_config_backward_compatibility(tmp_path):
    """Should still load if using legacy 'active_provider' name."""
    config_file = tmp_path / "legacy.toml"
    config_file.write_text('active_provider = "assemblyai"')
    config = load_config(config_file)
    assert config.default_provider == "assemblyai"
