import engine.config
import engine.platform_win.paths
from engine.config import load_config
from engine.platform_win.paths import get_config_path


def test_get_config_path_precedence(tmp_path, monkeypatch):
    """
    Verifies that get_config_path prioritizes local config over AppData.
    """
    # 1. Setup mock AppData and Local directory
    fake_app_data = tmp_path / "AppData" / "ParrotInk"
    fake_app_data.mkdir(parents=True)
    app_data_config = fake_app_data / "config.toml"
    app_data_config.write_text("mode = 'appdata'", encoding="utf-8")

    fake_runtime_root = tmp_path / "AppDir"
    fake_runtime_root.mkdir()
    local_config = fake_runtime_root / "config.toml"

    # Mock the underlying path helpers
    monkeypatch.setattr(engine.platform_win.paths, "get_app_dir", lambda: str(fake_app_data))
    monkeypatch.setattr(engine.platform_win.paths, "get_runtime_root", lambda: fake_runtime_root)

    # 2. Test Fallback (No local config exists)
    assert get_config_path() == str(app_data_config)

    # 3. Test Portable Mode (Local config exists)
    local_config.write_text("mode = 'portable'", encoding="utf-8")
    assert get_config_path() == str(local_config)


def test_load_config_integration(tmp_path, monkeypatch):
    """
    Verifies load_config correctly picks up the prioritized path.
    """
    fake_runtime_root = tmp_path / "AppDir"
    fake_runtime_root.mkdir()
    local_config = fake_runtime_root / "config.toml"
    local_config.write_text('[transcription]\nprovider = "assemblyai"', encoding="utf-8")

    monkeypatch.setattr(engine.platform_win.paths, "get_runtime_root", lambda: fake_runtime_root)
    # Ensure load_config uses our mocked get_config_path
    monkeypatch.setattr(engine.config, "get_config_path", get_config_path)

    config = load_config()
    assert config.transcription.provider == "assemblyai"


def test_config_save_preserves_location(tmp_path, monkeypatch):
    """
    Verifies that saving a config updates the file at the resolved location.
    """
    fake_runtime_root = tmp_path / "AppDir"
    fake_runtime_root.mkdir()
    local_config = fake_runtime_root / "config.toml"
    local_config.write_text('[transcription]\nprovider = "openai"', encoding="utf-8")

    monkeypatch.setattr(engine.platform_win.paths, "get_runtime_root", lambda: fake_runtime_root)
    monkeypatch.setattr(engine.config, "get_config_path", get_config_path)

    c = load_config()
    c.transcription.provider = "assemblyai"
    c.save(blocking=True)

    # Check the local file was updated
    content = local_config.read_text(encoding="utf-8")
    assert 'provider = "assemblyai"' in content
