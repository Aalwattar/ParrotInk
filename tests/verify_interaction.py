import asyncio
import time
from unittest.mock import MagicMock, patch
import pytest
from engine.config import Config
from main import AppCoordinator

@pytest.fixture
def coordinator():
    c = Config()
    c.hotkeys.hold_mode = False # Toggle mode
    coord = AppCoordinator(c)
    coord.loop = asyncio.get_running_loop()
    return coord

@pytest.mark.asyncio
async def test_manual_stop_toggle_mode(coordinator):
    coordinator.is_listening = True
    coordinator.start_time = time.time() - 1.0 # Past cooldown
    
    with patch.object(coordinator, 'stop_listening', new_callable=AsyncMock) as mock_stop:
        # Trigger manual stop with ANY key (e.g. 'space')
        coordinator._on_manual_stop(key='space')
        
        # Give it a tiny bit of time for the coroutine to be scheduled
        await asyncio.sleep(0.1)
        
        assert coordinator.session_cancelled is True
        assert mock_stop.called

class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)