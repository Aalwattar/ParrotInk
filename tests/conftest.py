import os
from unittest.mock import patch

import pytest

# Helper to check if running in GitHub Actions
IS_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


@pytest.fixture(scope="session", autouse=True)
def global_test_env(tmp_path_factory):
    """
    Surgical isolation for the entire test suite.
    Redirects AppData and LocalAppData to a temporary directory to prevent
    tests from overwriting the developer's real configuration or logs.
    """
    test_root = tmp_path_factory.mktemp("parrotink_test_root")
    test_app_data = test_root / "Roaming" / "ParrotInk"
    test_local_data = test_root / "Local" / "ParrotInk"

    test_app_data.mkdir(parents=True)
    test_local_data.mkdir(parents=True)

    # We mock at the module level to catch all imports
    with (
        patch("engine.platform_win.paths.get_app_dir", return_value=str(test_app_data)),
        patch("engine.platform_win.paths.user_log_dir", return_value=str(test_local_data)),
        patch("engine.platform_win.paths.user_data_dir", return_value=str(test_app_data.parent)),
        patch(
            "engine.platform_win.paths.get_config_path",
            return_value=str(test_app_data / "config.toml"),
        ),
        patch("engine.config.get_config_path", return_value=str(test_app_data / "config.toml")),
    ):
        # Verify the mock is active
        import engine.platform_win.paths

        if engine.platform_win.paths.get_app_dir() != str(test_app_data):
            # If standard patching failed due to early imports, we force it
            engine.platform_win.paths.get_app_dir = lambda: str(test_app_data)
            engine.platform_win.paths.get_config_path = lambda: str(test_app_data / "config.toml")
            import engine.config

            engine.config.get_config_path = lambda: str(test_app_data / "config.toml")

        yield


@pytest.fixture
def config():
    """Provides a clean Config instance isolated to the test run."""
    from engine.config import Config

    return Config()


@pytest.fixture(autouse=True)
def mock_audio_feedback():
    with patch("engine.audio_feedback.play_sound") as mock:
        yield mock


@pytest.fixture(autouse=True)
def guard_update_manager():
    """Prevent UpdateManager from starting threads or making network calls in tests."""
    with patch("engine.services.updates.UpdateManager.start"):
        yield


@pytest.fixture(autouse=True)
def guard_session_monitor():
    """Prevent SessionMonitor from starting a background thread during tests."""
    with patch("engine.platform_win.session.SessionMonitor.start"):
        yield


@pytest.fixture(autouse=True)
def guard_coordinator_watchdog():
    """Prevent AppCoordinator from starting its background watchdog task in tests."""
    with patch("main.AppCoordinator._hook_watchdog_task_run"):
        yield


@pytest.fixture
async def coordinator(config):
    """Provides a clean AppCoordinator instance with proper async shutdown."""
    from main import AppCoordinator

    coord = AppCoordinator(config)
    yield coord
    await coord.shutdown()
