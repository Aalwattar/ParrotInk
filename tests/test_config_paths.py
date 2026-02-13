import engine.config
import engine.platform_win.paths
from engine.config import Config, load_config


def test_load_config_default_path(tmp_path, monkeypatch):
    # Mock both locations where get_config_path might be accessed
    fake_config_path = tmp_path / "fake_config.toml"
    monkeypatch.setattr(engine.config, "get_config_path", lambda: str(fake_config_path))
    monkeypatch.setattr(engine.platform_win.paths, "get_config_path", lambda: str(fake_config_path))

    # Create the fake config file
    fake_config_path.write_text('default_provider = "assemblyai"', encoding="utf-8")

    # load_config() with no args should now use our fake path
    config = load_config()
    assert config.default_provider == "assemblyai"


def test_config_save_default_path(tmp_path, monkeypatch):
    # Mock both locations where get_config_path might be accessed
    fake_config_path = tmp_path / "subdir" / "saved_config.toml"
    monkeypatch.setattr(engine.config, "get_config_path", lambda: str(fake_config_path))
    monkeypatch.setattr(engine.platform_win.paths, "get_config_path", lambda: str(fake_config_path))

    c = Config(default_provider="openai")
    # save() with no args should use fake_config_path and create directories
    c.save()

    assert fake_config_path.exists()
    content = fake_config_path.read_text(encoding="utf-8")
    assert 'default_provider = "openai"' in content
