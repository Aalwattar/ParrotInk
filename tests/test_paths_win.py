import os

from engine.platform_win.paths import (
    APP_NAME,
    get_app_dir,
    get_config_path,
    get_log_path,
    get_runtime_root,
)


def test_get_config_path():
    config_path = get_config_path()
    assert config_path.endswith("config.toml")
    # In tests, get_app_dir is mocked to a temp path
    assert get_app_dir() in config_path


def test_get_log_path():
    log_path = get_log_path()
    assert log_path.endswith("parrotink.log")
    # In tests, log path is mocked to a temp path
    assert "ParrotInk" in log_path
    # Note: Our global_test_env mock for user_log_dir might not include 'Logs'
    # unless we explicitly add it in the mock, which we don't currently.
    assert os.path.basename(log_path) == "parrotink.log"


def test_get_runtime_root():
    root = get_runtime_root()
    assert root.exists()
    assert root.is_dir()
    # In development, it should be the project root
    assert (root / "pyproject.toml").exists()


def test_app_name_is_correct():
    assert APP_NAME == "ParrotInk"
