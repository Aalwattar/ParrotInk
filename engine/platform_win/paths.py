from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "Voice2Text"


def get_app_dir() -> str:
    """Returns the application data directory in %APPDATA%."""
    return user_data_dir(APP_NAME, appauthor=False, roaming=True)


def get_config_path() -> str:
    """Returns the path to the config file in the app data directory."""
    return str(Path(get_app_dir()) / "config.toml")


def get_log_path() -> str:
    """Returns the path to the log file in the app data directory."""
    return str(Path(get_app_dir()) / "voice2text.log")
