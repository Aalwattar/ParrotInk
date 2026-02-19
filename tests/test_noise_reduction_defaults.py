from engine.config import Config
from engine.config_resolver import resolve_effective_config


def test_mic_profile_default_is_headset():
    """Verify that a fresh config defaults to 'headset'."""
    cfg = Config()
    # This should FAIL initially as it's currently 'none'
    assert cfg.transcription.mic_profile == "headset"


def test_effective_config_noise_reduction_is_enabled_by_default():
    """Verify that the effective config has noise reduction enabled by default for OpenAI."""
    cfg = Config()
    effective = resolve_effective_config(cfg)

    # 'headset' maps to 'near_field'
    assert effective.openai.noise_reduction_type == "near_field"
