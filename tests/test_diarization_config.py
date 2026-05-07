from engine.config import Config
from engine.config_resolver import resolve_effective_config


def test_assemblyai_diarization_config_resolution():
    config = Config()
    config.transcription.provider = "assemblyai"
    config.providers.assemblyai.advanced.enable_diarization = True

    eff = resolve_effective_config(config)

    assert eff.assemblyai.enable_diarization is True
    assert "speaker_labels=true" in eff.assemblyai.url


def test_assemblyai_diarization_disabled_by_default():
    config = Config()
    config.transcription.provider = "assemblyai"

    eff = resolve_effective_config(config)

    assert eff.assemblyai.enable_diarization is False
    assert "speaker_labels=true" not in eff.assemblyai.url


def test_assemblyai_diarization_toml_loading(tmp_path):
    config_file = tmp_path / "diarization.toml"
    config_file.write_text("""
[providers.assemblyai.advanced]
enable_diarization = true
""")
    from engine.config import load_config

    config = load_config(config_file)

    assert config.providers.assemblyai.advanced.enable_diarization is True

    eff = resolve_effective_config(config)
    assert eff.assemblyai.enable_diarization is True
    assert "speaker_labels=true" in eff.assemblyai.url
