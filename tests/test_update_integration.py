from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_ui_bridge():
    return MagicMock()


@pytest.mark.asyncio
async def test_coordinator_initializes_and_starts_update_manager(mock_ui_bridge, coordinator):
    with patch("engine.services.updates.UpdateManager.start") as mock_start:
        # Use a fresh coordinator for this specific test to check initialization
        from engine.config import load_config
        from main import AppCoordinator

        config = load_config()
        local_coord = AppCoordinator(config, mock_ui_bridge)

        assert hasattr(local_coord, "update_manager")
        mock_start.assert_called_once()

        # Cleanup
        await local_coord.shutdown("test")


@pytest.mark.asyncio
async def test_coordinator_callback_pushes_to_bridge(mock_ui_bridge, coordinator):
    coordinator.ui_bridge = mock_ui_bridge
    coordinator._on_update_available("v1.2.3", "http://release")

    mock_ui_bridge.update_version_notification.assert_called_once_with("v1.2.3", "http://release")


@pytest.mark.asyncio
async def test_shutdown_sets_stop_event(mock_ui_bridge, coordinator):
    assert not coordinator._stop_event.is_set()
    await coordinator.shutdown("test")
    assert coordinator._stop_event.is_set()
