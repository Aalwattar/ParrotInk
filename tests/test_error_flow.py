import asyncio
from unittest.mock import MagicMock

import pytest

from engine.app_types import AppState, TranscriptionError
from main import AppCoordinator


@pytest.mark.asyncio
async def test_fatal_error_propagation_to_ui():
    """
    Integration test to verify that a fatal error from a provider
    correctly transitions the AppCoordinator to ERROR state and updates the UI.
    """
    mock_config = MagicMock()
    mock_ui_bridge = MagicMock()

    # Initialize coordinator
    coordinator = AppCoordinator(mock_config, mock_ui_bridge)
    coordinator._loop = asyncio.get_running_loop()

    # Simulate a fatal error from the provider/connection manager
    fatal_error = TranscriptionError(title="Out of Credits", message="Please top up your account.")

    # Trigger the callback
    coordinator._on_provider_error(fatal_error)

    # Give it a moment to process the threadsafe call
    await asyncio.sleep(0.1)

    # Verify state transition
    assert coordinator.state == AppState.ERROR

    # Verify UI updates
    mock_ui_bridge.set_state.assert_called_with(AppState.ERROR)
    mock_ui_bridge.update_status_message.assert_called_with("Error: Out of Credits")
    mock_ui_bridge.update_partial_text.assert_called_with("Please top up your account.")

    # Verify stats recorded as error
    mock_ui_bridge.record_stats.assert_called()
    _, kwargs = mock_ui_bridge.record_stats.call_args
    assert kwargs.get("error") is True


@pytest.mark.asyncio
async def test_error_state_resets_input_monitor():
    """Verify that transitioning to AppState.ERROR resets the input monitor state."""
    mock_config = MagicMock()
    mock_ui_bridge = MagicMock()

    coordinator = AppCoordinator(mock_config, mock_ui_bridge)
    coordinator._loop = asyncio.get_running_loop()
    coordinator.input_monitor = MagicMock()

    coordinator.set_state(AppState.ERROR)

    coordinator.input_monitor.reset_state.assert_called_once()


@pytest.mark.asyncio
async def test_config_change_recovers_from_error():
    """Verify that a config change while in ERROR state transitions back to IDLE if valid."""
    mock_config = MagicMock()
    mock_config.transcription.provider = "openai"
    mock_ui_bridge = MagicMock()

    coordinator = AppCoordinator(mock_config, mock_ui_bridge)
    coordinator._loop = asyncio.get_running_loop()
    coordinator.input_monitor = MagicMock()
    coordinator.state = AppState.ERROR

    # Mock provider availability to be valid
    coordinator.get_provider_availability = MagicMock(return_value={"openai": True})

    # Trigger config change observer
    coordinator._on_config_changed(mock_config)

    assert coordinator.state == AppState.IDLE
    mock_ui_bridge.clear_hud.assert_called_once()
