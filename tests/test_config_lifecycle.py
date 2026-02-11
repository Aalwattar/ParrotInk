import pytest
from pydantic import ValidationError

from engine.config import AudioConfig, Config


def test_audio_config_validation():
    # Valid values
    cfg = AudioConfig(connection_mode="warm", warm_idle_timeout_seconds=300)
    assert cfg.connection_mode == "warm"

    # Invalid mode
    with pytest.raises(ValidationError):
        AudioConfig(connection_mode="invalid")

    # Out of range timeout (too low)
    with pytest.raises(ValidationError):
        AudioConfig(warm_idle_timeout_seconds=10)

    # Out of range timeout (too high)
    with pytest.raises(ValidationError):
        AudioConfig(warm_idle_timeout_seconds=2000)


def test_config_defaults():
    cfg = Config()
    assert cfg.audio.connection_mode == "warm"
    assert cfg.audio.warm_idle_timeout_seconds == 300
