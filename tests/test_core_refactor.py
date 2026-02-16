import pytest

from engine.config import Config
from engine.connection import ConnectionManager
from main import AppCoordinator


@pytest.mark.asyncio
async def test_connection_manager_uses_config_for_retries():
    config = Config()
    config.audio.max_retries = 5
    config.audio.initial_backoff_seconds = 2.0

    manager = ConnectionManager(
        config, on_partial=lambda x: None, on_final=lambda x: None, set_state_cb=lambda x: None
    )

    # These should now be available and match config
    assert manager.config.audio.max_retries == 5
    assert manager.config.audio.initial_backoff_seconds == 2.0


@pytest.mark.asyncio
async def test_app_coordinator_uses_config_for_shutdown_timeout():
    config = Config()
    config.audio.shutdown_timeout_seconds = 15.0

    coordinator = AppCoordinator(config)
    assert coordinator.config.audio.shutdown_timeout_seconds == 15.0


@pytest.mark.asyncio
async def test_app_coordinator_dead_code_removed():
    """
    Verify AppCoordinator.run is gone (this should fail until we remove it from main.py).
    """
    config = Config()
    coordinator = AppCoordinator(config)
    assert not hasattr(coordinator, "run")
