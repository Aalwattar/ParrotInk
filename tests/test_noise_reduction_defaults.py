from engine.config import Config
from engine.config_resolver import resolve_effective_config


def test_mic_profile_default_is_none():
    """Verify that a fresh config defaults to 'none'."""
    cfg = Config()
    assert cfg.transcription.mic_profile == "none"


def test_effective_config_noise_reduction_is_disabled_by_default():
    """Verify that the effective config has noise reduction disabled by default for OpenAI."""
    cfg = Config()
    effective = resolve_effective_config(cfg)

    # 'none' maps to None (off)
    assert effective.openai.noise_reduction_type is None
