import pytest
from pydantic import ValidationError

from engine.config import (
    AssemblyAICoreConfig,
    OpenAICoreConfig,
    SoundsConfig,
    TranscriptionConfig,
)


def test_config_profiles_exist():
    """Verify that latency_profile and mic_profile exist in TranscriptionConfig."""
    # This should fail if the fields are not yet defined
    config = TranscriptionConfig(
        provider="openai", latency_profile="balanced", mic_profile="headset"
    )
    assert config.latency_profile == "balanced"
    assert config.mic_profile == "headset"


def test_config_redundancy_removed():
    """Verify that redundant fields have been removed."""
    # TranscriptionConfig should no longer have language
    with pytest.raises(ValidationError):
        TranscriptionConfig(language="en")

    # OpenAICoreConfig should HAVE language
    config = OpenAICoreConfig(language="en")
    assert config.language == "en"


def test_volume_validation():
    """Verify that volume is restricted to 0.0 - 100.0."""
    with pytest.raises(ValidationError):
        SoundsConfig(volume=-1.0)
    with pytest.raises(ValidationError):
        SoundsConfig(volume=101.0)

    # Valid volume should pass
    sc = SoundsConfig(volume=50)
    assert sc.volume == 50


def test_aai_inactivity_timeout_validation():
    """Verify that AssemblyAI inactivity_timeout_seconds is restricted to 0 or [5..3600]."""
    # 0 is valid (off)
    assert AssemblyAICoreConfig(inactivity_timeout_seconds=0).inactivity_timeout_seconds == 0

    # [5..3600] is valid
    assert AssemblyAICoreConfig(inactivity_timeout_seconds=5).inactivity_timeout_seconds == 5
    assert AssemblyAICoreConfig(inactivity_timeout_seconds=3600).inactivity_timeout_seconds == 3600

    # Invalid values
    with pytest.raises(ValidationError):
        AssemblyAICoreConfig(inactivity_timeout_seconds=1)
    with pytest.raises(ValidationError):
        AssemblyAICoreConfig(inactivity_timeout_seconds=4)
    with pytest.raises(ValidationError):
        AssemblyAICoreConfig(inactivity_timeout_seconds=3601)


def test_global_language_removed():
    """Verify that language is NO LONGER a global transcription setting."""
    with pytest.raises(ValidationError):
        TranscriptionConfig(language="fr")
