import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from engine.config import Config


@pytest.mark.asyncio
async def test_tray_callbacks_initialization_in_gui_main():
    """
    Reproduction test to verify that TrayApp is initialized with all necessary callbacks in gui_main.py.
    """
    mock_coordinator = MagicMock()
    mock_coordinator.input_monitor = MagicMock()
    mock_coordinator.shutdown = AsyncMock()  # Use AsyncMock for awaitable

    mock_config = Config()
    mock_ui_bridge = MagicMock()
    mock_cli_args = MagicMock()
    mock_cli_args.log_file = None
    mock_cli_args.verbose = 0
    mock_cli_args.quiet = False

    # We need to mock several top-level dependencies of gui_main.py
    with (
        patch("engine.gui_main.load_config", return_value=mock_config),
        patch("engine.gui_main.configure_logging"),
        patch("engine.gui_main.AppCoordinator", return_value=mock_coordinator),
        patch("engine.gui_main.UIBridge", return_value=mock_ui_bridge),
        patch("engine.ui.TrayApp") as MockTrayApp,
        patch("threading.Thread"),
        patch("asyncio.Event") as MockEvent,
    ):
        # Mock Event to return a pre-set event for the exit_event
        exit_event = MagicMock()
        exit_event.wait = AsyncMock(
            side_effect=asyncio.CancelledError
        )  # Break the loop immediately
        MockEvent.return_value = exit_event

        from engine.gui_main import main_gui

        try:
            await main_gui(mock_cli_args)
        except asyncio.CancelledError:
            pass

        # Verify TrayApp instantiation
        assert MockTrayApp.called, "TrayApp was never initialized in main_gui"
        _, kwargs = MockTrayApp.call_args

        required_callbacks = ["on_provider_change", "on_set_key", "on_toggle_sounds"]

        missing = [cb for cb in required_callbacks if cb not in kwargs]
        assert not missing, f"Missing callbacks in TrayApp initialization: {missing}"
