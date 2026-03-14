import os
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

# Helper to check if running in GitHub Actions
IS_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


@pytest.fixture(scope="session", autouse=True)
def global_test_env(tmp_path_factory):
    """
    Surgical isolation for the entire test suite.
    Redirects AppData and LocalAppData to a temporary directory.
    """
    test_root = tmp_path_factory.mktemp("parrotink_test_root")
    test_app_data = test_root / "Roaming" / "ParrotInk"
    test_local_data = test_root / "Local" / "ParrotInk"

    test_app_data.mkdir(parents=True)
    test_local_data.mkdir(parents=True)

    # We mock paths at the session level to catch all imports
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
            engine.platform_win.paths.get_app_dir = lambda: str(test_app_data)
            engine.platform_win.paths.get_config_path = lambda: str(test_app_data / "config.toml")
            import engine.config

            engine.config.get_config_path = lambda: str(test_app_data / "config.toml")

        yield


@pytest.fixture(autouse=True)
def no_non_daemon_thread_leaks():
    """
    Session-wide guard to detect and report leaked non-daemon threads.
    """
    before = {t.ident for t in threading.enumerate() if t.is_alive()}
    yield

    deadline = time.time() + 2.0
    while time.time() < deadline:
        leaked = [
            t
            for t in threading.enumerate()
            if t.is_alive() and not t.daemon and t.ident not in before
        ]
        if not leaked:
            return
        time.sleep(0.05)

    leaked = [
        t for t in threading.enumerate() if t.is_alive() and not t.daemon and t.ident not in before
    ]
    assert not leaked, f"Leaked non-daemon threads: {[t.name for t in leaked]}"


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
def mock_win11toast():
    """Globally prevent win11toast from displaying actual Windows notifications during tests."""
    with patch("win11toast.toast") as mock:
        yield mock


@pytest.fixture
def guard_ui_components():
    """
    Surgically prevents real UI threads from starting during tests.
    Used by the coordinator fixture.
    """
    with (
        patch("engine.indicator_ui.IndicatorWindow") as mock_ind,
        patch("engine.ui.TrayApp._create_icon", return_value=MagicMock()),
        patch("pystray.Icon", return_value=MagicMock()),
        patch("ttkbootstrap.Window", return_value=MagicMock()),
        patch("tkinter.Tk", return_value=MagicMock()),
    ):
        # Configure indicator mock to have safe properties
        mock_ind.return_value.is_alive = True
        mock_ind.return_value.impl = MagicMock()
        yield


@pytest.fixture
async def coordinator(config, guard_ui_components):
    """Provides a clean AppCoordinator instance with proper async shutdown."""
    from main import AppCoordinator

    # 1. Block background start calls
    with (
        patch("engine.services.updates.UpdateManager.start"),
        patch("engine.platform_win.session.SessionMonitor.start"),
        patch("main.AppCoordinator._hook_watchdog_task_run"),
    ):
        mock_bridge = MagicMock()
        coord = AppCoordinator(config, mock_bridge)
        yield coord
        await coord.shutdown()
