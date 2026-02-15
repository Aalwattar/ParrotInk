import pytest

from engine.config import ConfigError, load_config


def test_load_config_missing_file():
    # Now returns a default config instead of raising error
    config = load_config("non_existent.toml")
    assert config.transcription.provider == "openai"


def test_load_config_invalid_toml(tmp_path):
    config_file = tmp_path / "invalid.toml"
    # Missing closing quote
    config_file.write_text('transcription.provider = "openai')
    with pytest.raises(ConfigError, match="Invalid TOML format"):
        load_config(config_file)


def test_load_config_misspelled_value(tmp_path):
    config_file = tmp_path / "misspelled.toml"
    # Boolean value with typo
    config_file.write_text("""
[transcription]
provider = "openai"
[hotkeys]
hotkey = "v"
hold_mode = fakse
""")
    with pytest.raises(ConfigError, match="Invalid TOML format"):
        load_config(config_file)


def test_load_config_invalid_types(tmp_path):
    config_file = tmp_path / "types.toml"
    # provider must be a literal
    config_file.write_text("""
[transcription]
provider = "invalid_provider"
[hotkeys]
hold_mode = "true"
""")
    with pytest.raises(ConfigError, match="Configuration validation failed"):
        load_config(config_file)


def test_load_config_valid(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[transcription]
provider = "assemblyai"

[providers.openai.core]
language = "es"

[hotkeys]
hotkey = "ctrl+v"
hold_mode = false
""")
    config = load_config(config_file)
    assert config.transcription.provider == "assemblyai"
    assert config.hotkeys.hotkey == "ctrl+v"
    assert config.hotkeys.hold_mode is False
    assert config.providers.openai.core.language == "es"


def test_config_advanced_and_test_defaults(tmp_path):
    config_file = tmp_path / "default_test.toml"
    config_file.write_text("""
[transcription]
provider = "openai"
""")
    config = load_config(config_file)

    # Test section defaults
    assert config.test.enabled is False
    assert config.test.openai_mock_url == "ws://localhost:8081"
    assert config.test.assemblyai_mock_url == "ws://localhost:8081"


def test_config_overrides(tmp_path):
    config_file = tmp_path / "overrides.toml"
    config_file.write_text("""
[transcription]
provider = "openai"

[test]
enabled = true
openai_mock_url = "ws://127.0.0.1:9000"
""")
    config = load_config(config_file)

    assert config.test.enabled is True
    assert config.test.openai_mock_url == "ws://127.0.0.1:9000"
    assert config.test.assemblyai_mock_url == "ws://localhost:8081"  # default


def test_config_key_resolution(mocker):
    config = load_config("non_existent.toml")

    mock_get = mocker.patch("engine.security.SecurityManager.get_key")
    mock_get.side_effect = lambda x: "secret-key" if x == "openai_api_key" else None

    assert config.get_openai_key() == "secret-key"
    assert config.get_assemblyai_key() is None
