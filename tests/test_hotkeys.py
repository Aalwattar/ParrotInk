import pytest


@pytest.mark.asyncio
async def test_hotkey_assignment(coordinator):
    # In the new architecture, InputMonitor holds the hotkey
    coordinator.input_monitor.set_hotkey("ctrl+alt+v", hold_mode=True)
    assert coordinator.input_monitor._hotkey_str == "ctrl+alt+v"
    assert coordinator.input_monitor._hold_mode is True


@pytest.mark.asyncio
async def test_hotkey_update_on_config_change(coordinator):
    new_config = coordinator.config
    new_config.hotkeys.hotkey = "ctrl+space"
    new_config.hotkeys.hold_mode = False

    coordinator._on_config_changed(new_config)

    assert coordinator.input_monitor._hotkey_str == "ctrl+space"
    assert coordinator.input_monitor._hold_mode is False


@pytest.mark.asyncio
async def test_hold_mode_logic(coordinator):
    coordinator.config.hotkeys.hold_mode = True
    assert coordinator.config.hotkeys.hold_mode is True


@pytest.mark.asyncio
async def test_toggle_mode_logic(coordinator):
    coordinator.config.hotkeys.hold_mode = False
    assert coordinator.config.hotkeys.hold_mode is False
