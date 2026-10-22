import asyncio
import ctypes
from unittest.mock import MagicMock, patch

import pytest

from engine.hotkey_ui import HotkeyRecorder
from engine.hotkeys import KEY_VKS, MODIFIER_BASE, MODIFIER_VKS, key_name, parse_hotkey
from engine.injector import inject_backspaces, inject_text
from engine.interaction import STATE_DICTATING, STATE_IDLE, Win32InputMonitor
from engine.platform_win.keys import (
    INPUT,
    KBDLLHOOKSTRUCT,
    KEYEVENTF_KEYUP,
    LLKHF_INJECTED,
    PARROTINK_INPUT_TAG,
    WM_KEYDOWN,
    WM_KEYUP,
)


@pytest.fixture
def monitor():
    monitor = Win32InputMonitor(MagicMock(), MagicMock())
    monitor.set_hotkey("ctrl+alt+v")
    with (
        patch("engine.interaction.user32.CallNextHookEx", return_value=0),
        patch("engine.interaction.user32.GetAsyncKeyState", return_value=0x8000),
    ):
        yield monitor


def send(monitor, vk, message=WM_KEYDOWN, tag=0, injected=False):
    event = KBDLLHOOKSTRUCT(vkCode=vk, flags=LLKHF_INJECTED if injected else 0, dwExtraInfo=tag)
    return monitor._ll_keyboard_handler(0, message, ctypes.addressof(event))


def drain(monitor):
    events = []
    while not monitor._event_queue.empty():
        events.append(monitor._event_queue.get_nowait())
    return events


@pytest.mark.parametrize("injected", [False, True])
@pytest.mark.parametrize("hold", [False, True])
def test_shared_keyboard_start_and_stop(monitor, injected, hold):
    monitor.set_hotkey("ctrl+alt+v", hold_mode=hold)
    for vk in (0xA2, 0xA4, 0x56):
        send(monitor, vk, injected=injected)
    assert drain(monitor) == ["start"]
    send(monitor, 0x56, WM_KEYUP, injected=injected)
    if hold:
        assert drain(monitor) == ["stop"]
    else:
        send(monitor, 0x56, injected=injected)
        assert drain(monitor) == ["start"]


def test_own_input_does_not_start_or_stop_dictation(monitor):
    for vk in (0xA2, 0xA4, 0x56):
        send(monitor, vk, tag=PARROTINK_INPUT_TAG, injected=True)
    assert monitor._pressed_keys == set()
    assert drain(monitor) == []
    monitor._state = STATE_DICTATING
    monitor.enable_any_key_monitoring(True)
    send(monitor, 0x41, tag=PARROTINK_INPUT_TAG, injected=True)
    assert drain(monitor) == []
    send(monitor, 0x41, injected=True)
    assert drain(monitor) == ["any_key:a"]


def test_repeats_require_release_even_after_session_cleanup(monitor):
    for vk in (0xA2, 0xA4, 0x56, 0x56):
        send(monitor, vk)
    assert drain(monitor) == ["start"]
    monitor.reset_state()
    monitor._last_toggle_ts = 0
    send(monitor, 0x56)
    assert drain(monitor) == []
    send(monitor, 0x56, WM_KEYUP)
    send(monitor, 0x56)
    assert drain(monitor) == ["start"]


@pytest.mark.parametrize(
    "shortcut,modifier",
    [("ctrl+alt+v", 0xA4), ("ctrl+win+v", 0x5B), ("ctrl+win+v", 0x5C)],
)
@pytest.mark.parametrize("injected", [False, True])
@pytest.mark.parametrize("previous_session", [False, True])
def test_missed_modifier_release_cannot_turn_paste_into_hotkey(
    monitor, shortcut, modifier, injected, previous_session
):
    monitor.set_hotkey(shortcut)
    send(monitor, modifier, injected=injected)
    if previous_session:
        send(monitor, 0xA2, injected=injected)
        send(monitor, 0x56, injected=injected)
        assert drain(monitor) == ["start"]
        send(monitor, 0x56, WM_KEYUP, injected=injected)
        send(monitor, 0xA2, WM_KEYUP, injected=injected)
        monitor.reset_state()
        monitor._last_toggle_ts = 0

    # Windows has released the modifier, but its key-up never reached our hook.
    with patch(
        "engine.interaction.user32.GetAsyncKeyState",
        side_effect=lambda vk: 0x8000 if vk in (0x11, 0xA2) else 0,
    ):
        send(monitor, 0xA2, injected=injected)
        assert send(monitor, 0x56, injected=injected) == 0
        assert drain(monitor) == []
        assert modifier not in monitor._pressed_keys
        assert send(monitor, 0x56, injected=injected) == 0

    # A fresh, complete chord must still work after stale state is discarded.
    send(monitor, 0x56, WM_KEYUP, injected=injected)
    send(monitor, modifier, injected=injected)
    send(monitor, 0x56, injected=injected)
    assert drain(monitor) == ["start"]


def test_plain_paste_repeats_pass_through(monitor):
    send(monitor, 0xA2)
    assert send(monitor, 0x56) == 0
    assert send(monitor, 0x56) == 0
    assert drain(monitor) == []


@pytest.mark.parametrize("hold", [False, True])
def test_synthetic_modifier_release_does_not_break_active_hotkey(monitor, hold):
    monitor.set_hotkey("ctrl+alt+v", hold_mode=hold)
    for vk in (0xA2, 0xA4, 0x56):
        send(monitor, vk)
    assert drain(monitor) == ["start"]
    # Starting dictation releases modifiers in Windows, even while physically held.
    with patch("engine.interaction.user32.GetAsyncKeyState", return_value=0):
        send(monitor, 0x56)
        assert monitor._pressed_modifiers == {0x11, 0x12}
        send(monitor, 0x56, WM_KEYUP)
        if hold:
            assert drain(monitor) == ["stop"]
        else:
            send(monitor, 0x56)
            assert drain(monitor) == ["start"]


def test_either_control_key_can_remain_held(monitor):
    monitor.set_hotkey("ctrl+v", hold_mode=True)
    send(monitor, 0xA2)
    send(monitor, 0xA3)
    send(monitor, 0xA2, WM_KEYUP)
    send(monitor, 0x56)
    assert drain(monitor) == ["start"]
    send(monitor, 0xA2, WM_KEYUP)
    assert drain(monitor) == []
    send(monitor, 0xA3, WM_KEYUP)
    assert drain(monitor) == ["stop"]


@pytest.mark.parametrize(
    "shortcut,vk,mods",
    [
        ("f12", 0x7B, set()),
        ("ctrl+enter", 0x0D, {0x11}),
        ("win+v", 0x56, {0x5B}),
        ("ctrl+;", 0xBA, {0x11}),
        ("shift+backtick", 0xC0, {0x10}),
        ("ctrl+equals", 0xBB, {0x11}),
        ("alt+left", 0x25, {0x12}),
        ("f24", 0x87, set()),
    ],
)
def test_mapping_and_detection_agree(monitor, shortcut, vk, mods):
    assert parse_hotkey(shortcut) == (mods, vk)
    monitor.set_hotkey(shortcut)
    for modifier in mods:
        send(monitor, modifier)
    send(monitor, vk)
    assert drain(monitor) == ["start"]


def test_every_recorded_key_round_trips():
    with patch("engine.hotkey_ui.gdiplus"):
        recorder = HotkeyRecorder(lambda _: None)
    for vk in (*KEY_VKS.values(), *MODIFIER_BASE, 0xB3, 0xE2):
        name = recorder._vk_to_text(vk, 0)
        assert name == key_name(vk)
        if name in MODIFIER_VKS:
            assert not recorder._is_valid([name])
        else:
            assert recorder._is_valid([name])
            assert parse_hotkey(name) == (set(), vk)
    assert not recorder._is_valid(["a", "b"])
    assert not recorder._is_valid(["ctrl", "unknown"])


@pytest.mark.parametrize("invalid", ["f25", "ctrl", "ctrl+unknown", "a+b", "", "vk_00"])
def test_invalid_mapping_preserves_existing_assignment(monitor, invalid):
    with pytest.raises(ValueError):
        monitor.set_hotkey(invalid)
    assert monitor.hotkey == "ctrl+alt+v"


@pytest.mark.parametrize("operation", [lambda: inject_text("a\n"), lambda: inject_backspaces(2)])
def test_generated_input_is_tagged(operation):
    inputs = []

    def capture(count, pointer, size):
        array = ctypes.cast(pointer, ctypes.POINTER(INPUT))
        inputs.extend(array[i].union.ki.dwExtraInfo for i in range(count))
        return count

    with patch("engine.injector.USER32.SendInput", side_effect=capture):
        operation()
    assert inputs == [PARROTINK_INPUT_TAG] * 4


def test_modifier_release_is_tagged(monitor):
    monitor._pressed_modifiers = {0x11, 0x12}
    tags = []

    def capture(count, pointer, size):
        event = ctypes.cast(pointer, ctypes.POINTER(INPUT)).contents
        tags.append(event.union.ki.dwExtraInfo)
        assert event.union.ki.dwFlags == KEYEVENTF_KEYUP
        return count

    with patch("engine.interaction.user32.SendInput", side_effect=capture):
        monitor._release_stuck_modifiers()
    assert tags == [PARROTINK_INPUT_TAG] * 2


@pytest.mark.asyncio
async def test_idle_input_monitoring_never_generates_input(coordinator):
    idle_tasks = []
    idle_loop = MagicMock()
    idle_loop.create_task.side_effect = lambda task: idle_tasks.append(task) or MagicMock()
    coordinator.input_monitor._is_running = True
    coordinator.input_monitor._hook = 123
    with (
        patch("main.asyncio.sleep", side_effect=[None, None, asyncio.CancelledError()]),
        patch("engine.interaction.user32.SendInput", return_value=0) as send_input,
        patch("engine.injector.USER32.SendInput", return_value=0) as inject_input,
        patch("engine.interaction.user32.keybd_event") as keybd_event,
        patch("engine.interaction.user32.mouse_event") as mouse_event,
    ):
        try:
            coordinator.loop = idle_loop
            # Advance background monitoring past two polling intervals without user input.
            for task in idle_tasks:
                await task
        finally:
            coordinator.loop = None
            for task in idle_tasks:
                task.close()
        send_input.assert_not_called()
        inject_input.assert_not_called()
        keybd_event.assert_not_called()
        mouse_event.assert_not_called()


def test_recovery_preserves_dictation_state(monitor):
    monitor._state = STATE_DICTATING
    with patch.object(monitor, "stop"), patch.object(monitor, "start"):
        monitor.restart(preserve_state=True)
        assert monitor._state == STATE_DICTATING
        monitor.restart()
        assert monitor._state == STATE_IDLE


@pytest.mark.parametrize("outcome", ["cancel", "save", "error"])
def test_recorder_always_restores_listener(mocker, config, outcome):
    from engine.ui import TrayApp

    mocker.patch("engine.ui.pystray.Icon")
    before, after, changed = MagicMock(), MagicMock(), MagicMock()
    app = TrayApp(
        config,
        on_before_hotkey_change=before,
        on_after_hotkey_change=after,
        on_hotkey_change=changed,
    )

    def record():
        if outcome == "save":
            changed("f12")
        elif outcome == "error":
            raise RuntimeError("Recorder failed")

    mocker.patch("engine.hotkey_ui.HotkeyRecorder").return_value.run.side_effect = record
    worker = mocker.patch("engine.ui.threading.Thread")
    worker.return_value.start.side_effect = lambda: worker.call_args.kwargs["target"]()
    app._on_change_hotkey_clicked(None, None)
    before.assert_called_once()
    after.assert_called_once()
    assert changed.call_count == (1 if outcome == "save" else 0)
