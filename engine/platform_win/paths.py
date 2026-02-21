from pathlib import Path

from platformdirs import user_data_dir, user_log_dir

APP_NAME = "ParrotInk"


def get_app_dir() -> str:
    """Returns the application data directory in %APPDATA% (Roaming)."""
    return user_data_dir(APP_NAME, appauthor=False, roaming=True)


def get_config_path() -> str:
    """Returns the path to the config file in the app data directory."""
    return str(Path(get_app_dir()) / "config.toml")


def get_log_path() -> str:
    r"""
    Returns the path to the log file in the local app data directory.
    Uses %LOCALAPPDATA%\ParrotInk\Logs\parrotink.log
    """
    return str(Path(user_log_dir(APP_NAME, appauthor=False)) / "parrotink.log")


def get_stats_path() -> str:
    """Returns the path to the statistics file in the app data directory."""
    return str(Path(get_app_dir()) / "Stats" / "stats.json")
