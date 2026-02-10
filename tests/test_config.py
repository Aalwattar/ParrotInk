import pytest

from engine.config import ConfigError, load_config


def test_load_config_missing_file():
    with pytest.raises(ConfigError, match="Configuration file not found"):
        load_config("non_existent.toml")


def test_load_config_invalid_toml(tmp_path):
    config_file = tmp_path / "invalid.toml"
    # Misspelled key or corrupted structure
    config_file.write_text(
        'active_provider = "openai\nopenai_api_key = "test"'
    )  # Missing closing quote
    with pytest.raises(ConfigError, match="Invalid TOML format"):
        load_config(config_file)


def test_load_config_misspelled_value(tmp_path):
    config_file = tmp_path / "misspelled.toml"
    # Boolean value with typo
    config_file.write_text("""
active_provider = "openai"
openai_api_key = "key"
assemblyai_api_key = "key"
[hotkeys]
hotkey = "v"
hold_mode = fakse
""")
    with pytest.raises(ConfigError, match="Invalid TOML format"):
        load_config(config_file)


def test_load_config_invalid_types(tmp_path):
    config_file = tmp_path / "types.toml"
    # active_provider must be a literal
    config_file.write_text("""
active_provider = "invalid_provider"
openai_api_key = 123
[hotkeys]
hold_mode = "true"
""")
    with pytest.raises(ConfigError, match="Configuration validation failed"):
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


def test_config_advanced_and_test_defaults(tmp_path):
    config_file = tmp_path / "default_test.toml"
    config_file.write_text("""
active_provider = "openai"
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
active_provider = "openai"

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
