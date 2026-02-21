from engine.platform_win.paths import get_app_dir, get_config_path, get_log_path


def test_get_app_dir():
    app_dir = get_app_dir()
    # On Windows, it should contain AppData\Roaming\ParrotInk
    assert "ParrotInk" in app_dir
    assert "AppData" in app_dir
    assert "Roaming" in app_dir


def test_get_config_path():
    config_path = get_config_path()
    assert config_path.endswith("config.toml")
    assert get_app_dir() in config_path


def test_get_log_path():
    log_path = get_log_path()
    assert log_path.endswith("parrotink.log")
    # Log path should be in AppData\Local (not Roaming)
    assert "AppData" in log_path
    assert "Local" in log_path
    # Should be in a 'Logs' subdirectory (platform-specific capitalization)
    assert "Logs" in log_path or "logs" in log_path
