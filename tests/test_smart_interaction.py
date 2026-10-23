import asyncio
import time

import pytest

from engine.app_types import AppState


@pytest.mark.asyncio
async def test_manual_key_press_stops_listening_and_cancels_injection(coordinator):
    coordinator.state = AppState.LISTENING
    coordinator.injection_controller.begin(None)
    coordinator.loop = asyncio.get_running_loop()
    # Bypass cooldown
    coordinator.start_time = time.time() - 1.0

    # Simulate a manual key press event from InputMonitor
    coordinator.injection_controller.cancel()
    await coordinator.stop_listening()

    assert coordinator.state == AppState.IDLE
    assert coordinator.injection_controller.cancelled is True


@pytest.mark.asyncio
async def test_coordinator_uses_input_monitor(coordinator):
    assert coordinator.input_monitor is not None
    assert coordinator.input_monitor._hotkey_str == coordinator.config.hotkeys.hotkey
