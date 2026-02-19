import time
from unittest.mock import MagicMock
import pytest
from engine.config import Config
from main import AppCoordinator

def test_hook_recovery_on_unlock():
    """
    Verifies that the AppCoordinator correctly restarts the hotkey hook
    when a session unlock is detected.
    """
    cfg = Config()
    ui_bridge = MagicMock()
    coordinator = AppCoordinator(cfg, ui_bridge)
    
    # Mock InputMonitor.restart
    coordinator.input_monitor.restart = MagicMock()
    
    print("Simulating Session Unlock...")
    coordinator._on_unlock()
    
    # ASSERT: InputMonitor.restart was called
    assert coordinator.input_monitor.restart.called
    print("SUCCESS: Hook restart was triggered by unlock event.")

if __name__ == "__main__":
    test_hook_recovery_on_unlock()
