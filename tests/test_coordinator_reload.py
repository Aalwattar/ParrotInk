from unittest.mock import MagicMock

import pytest
import tomli_w

from engine.config import Config
from main import AppCoordinator


@pytest.mark.asyncio
async def test_coordinator_handles_config_reload(tmp_path):
    config_path = tmp_path / "config.toml"
    config_path.write_text(tomli_w.dumps({"hotkeys": {"hotkey": "v"}}), encoding="utf-8")

    cfg = Config.from_file(config_path)
    # Mock components
    ui_bridge = MagicMock()

    coordinator = AppCoordinator(cfg, ui_bridge)

    # Track original monitor to verify it updated
    monitor = coordinator.input_monitor
    # We mock start/stop to avoid actually hooking the OS in tests,
    # but we don't mock the whole monitor so the set_hotkey logic runs.
    monitor.start = MagicMock()
    monitor.stop = MagicMock()
    # Force state to running so it triggers a restart on change
    monitor._is_running = True

    # Update config on disk
    updated_data = {"hotkeys": {"hotkey": "r", "hold_mode": True}}
    config_path.write_text(tomli_w.dumps(updated_data), encoding="utf-8")

    # Reload
    cfg.reload(path=config_path)

    # Verify Coordinator updated its components
    assert monitor.hotkey == "r"
    assert monitor.hold_mode is True

    # Verify input monitor was restarted (internally by set_hotkey)
    assert monitor.stop.called
    assert monitor.start.called

    # Verify UI bridge was notified
    assert ui_bridge.update_settings.called
    assert ui_bridge.refresh_hud.called
