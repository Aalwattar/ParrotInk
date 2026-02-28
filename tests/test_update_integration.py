import threading
import time
from unittest.mock import MagicMock, patch

import pytest
from engine.config import load_config
from main import AppCoordinator


@pytest.fixture
def mock_ui_bridge():
    return MagicMock()


def test_coordinator_initializes_and_starts_update_manager(mock_ui_bridge):
    config = load_config()
    with patch("engine.services.updates.UpdateManager.start") as mock_start:
        coordinator = AppCoordinator(config, mock_ui_bridge)
        
        assert hasattr(coordinator, "update_manager")
        mock_start.assert_called_once()
        
        # Shutdown to stop background threads
        import asyncio
        asyncio.run(coordinator.shutdown("test"))


def test_coordinator_callback_pushes_to_bridge(mock_ui_bridge):
    config = load_config()
    with patch("engine.services.updates.UpdateManager.start"):
        coordinator = AppCoordinator(config, mock_ui_bridge)
        
        coordinator._on_update_available("v1.2.3", "http://release")
        
        mock_ui_bridge.update_version_notification.assert_called_once_with(
            "v1.2.3", "http://release"
        )
        
        import asyncio
        asyncio.run(coordinator.shutdown("test"))


def test_shutdown_sets_stop_event(mock_ui_bridge):
    config = load_config()
    with patch("engine.services.updates.UpdateManager.start"):
        coordinator = AppCoordinator(config, mock_ui_bridge)
        
        assert not coordinator._stop_event.is_set()
        
        import asyncio
        asyncio.run(coordinator.shutdown("test"))
        
        assert coordinator._stop_event.is_set()
