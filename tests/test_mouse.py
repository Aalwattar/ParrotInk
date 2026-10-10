import ctypes
from unittest.mock import MagicMock

import pytest

from engine.mouse import MSLLHOOKSTRUCT, WM_LBUTTONDOWN, MouseMonitor


def click(monitor, x=10, y=20, message=WM_LBUTTONDOWN, code=0):
    event = MSLLHOOKSTRUCT()
    event.pt.x, event.pt.y = x, y
    return monitor._on_native_mouse(code, message, ctypes.addressof(event))


def run_pumps(mocker, monitor, clicks=(), foreground=(100, 100)):
    delivered = False

    def pump(*args):
        nonlocal delivered
        if args[-1] and not delivered:
            delivered = True
            for x, y in clicks:
                click(monitor, x, y)
        return False

    mocker.patch("engine.mouse.threading.Thread")
    mocker.patch("engine.mouse._peek_message", side_effect=pump)
    mocker.patch("engine.mouse._read_foreground", side_effect=foreground)
    monitor._stop_event = MagicMock()
    monitor._stop_event.is_set.return_value = False
    monitor._stop_event.wait.side_effect = [False] * (len(foreground) - 1) + [True]
    monitor._poll()
    while not monitor._clicks.empty():
        monitor._notify(monitor._clicks.get_nowait())


def test_clicks_between_samples_keep_event_coordinates(mocker):
    callback = MagicMock()
    monitor = MouseMonitor(callback)
    run_pumps(mocker, monitor, [(100, 200), (-30, 400)])
    assert [c.args for c in callback.call_args_list] == [(100, 200), (-30, 400)]


def test_native_hook_always_passes_input_and_defers_callback(mocker):
    callback = MagicMock()
    monitor = MouseMonitor(callback)
    next_hook = mocker.patch("engine.mouse._next_hook", return_value=77)
    assert click(monitor) == 77
    assert click(monitor, message=0x0202) == 77
    assert click(monitor, code=-1) == 77
    callback.assert_not_called()
    assert monitor._clicks.get_nowait() == (10, 20)
    assert monitor._clicks.empty()
    assert next_hook.call_count == 3


def test_parse_failure_still_passes_input(mocker):
    monitor = MouseMonitor(MagicMock())
    next_hook = mocker.patch("engine.mouse._next_hook", return_value=55)
    log = mocker.patch("engine.mouse.logger.exception")
    assert monitor._on_native_mouse(0, WM_LBUTTONDOWN, 0) == 55
    next_hook.assert_called_once()
    log.assert_called_once()


def test_callback_failure_does_not_lose_following_click(mocker):
    callback = MagicMock(side_effect=[RuntimeError("callback failed"), None])
    log = mocker.patch("engine.mouse.logger.exception")
    run_pumps(mocker, MouseMonitor(callback), [(1, 2), (3, 4)])
    assert callback.call_count == 2
    log.assert_called_once()


def test_foreground_change_still_checks_anchor_without_click(mocker):
    callback = MagicMock()
    mocker.patch("engine.mouse._read_position", return_value=(30, 40))
    run_pumps(mocker, MouseMonitor(callback), foreground=(100, 200))
    callback.assert_called_once_with(30, 40)


def test_install_failure_is_reported_and_does_not_unhook(mocker):
    monitor = MouseMonitor(MagicMock())
    mocker.patch("engine.mouse._set_hook", return_value=None)
    unhook = mocker.patch("engine.mouse._unhook")
    monitor._poll()
    assert monitor._start_error
    assert monitor._ready.is_set()
    assert not monitor._is_running
    unhook.assert_not_called()


def test_worker_always_releases_native_hook(mocker):
    monitor = MouseMonitor(MagicMock())
    unhook = mocker.patch("engine.mouse._unhook")
    run_pumps(mocker, monitor)
    unhook.assert_called_once_with(123)
    assert monitor._hook is None
    assert monitor._hook_proc is None


def test_mouse_monitor_start_stop(mocker):
    factory = mocker.patch("engine.mouse.threading.Thread")
    thread = factory.return_value
    thread.is_alive.side_effect = [True, False]
    monitor = MouseMonitor(MagicMock())
    mocker.patch.object(monitor._ready, "wait", return_value=True)
    monitor.start()
    monitor.start()
    factory.assert_called_once()
    monitor.stop()
    thread.join.assert_called_once_with(timeout=monitor.STOP_TIMEOUT)
    assert monitor._thread is None
    assert not monitor._is_running


def test_failed_join_retains_worker_and_refuses_second_start(mocker):
    factory = mocker.patch("engine.mouse.threading.Thread")
    thread = MagicMock()
    thread.is_alive.return_value = True
    monitor = MouseMonitor(MagicMock())
    monitor._thread = thread
    monitor.stop()
    with pytest.raises(OSError, match="still stopping"):
        monitor.start()
    factory.assert_not_called()
    assert monitor._thread is thread
    assert monitor._stop_event.is_set()


def test_stop_from_worker_does_not_join_itself(mocker):
    thread = MagicMock()
    thread.is_alive.return_value = True
    mocker.patch("engine.mouse.threading.current_thread", return_value=thread)
    monitor = MouseMonitor(MagicMock())
    monitor._thread = thread
    monitor.stop()
    thread.join.assert_not_called()


def test_start_failure_resets_state(mocker):
    factory = mocker.patch("engine.mouse.threading.Thread")
    factory.return_value.start.side_effect = RuntimeError("start failed")
    monitor = MouseMonitor(MagicMock())
    with pytest.raises(RuntimeError, match="start failed"):
        monitor.start()
    assert monitor._thread is None
    assert not monitor._is_running


def test_start_timeout_stops_worker(mocker):
    factory = mocker.patch("engine.mouse.threading.Thread")
    factory.return_value.is_alive.return_value = False
    monitor = MouseMonitor(MagicMock())
    mocker.patch.object(monitor._ready, "wait", return_value=False)
    with pytest.raises(OSError, match="did not start"):
        monitor.start()
    assert monitor._stop_event.is_set()


def test_cursor_reader_success_and_failure(mocker):
    from engine.mouse import _read_position

    def fill(point):
        point._obj.x, point._obj.y = 123, -45
        return True

    mocker.patch("engine.mouse._get_cursor_pos", side_effect=fill)
    assert _read_position() == (123, -45)
    mocker.patch("engine.mouse._get_cursor_pos", return_value=False)
    assert _read_position() is None


def test_dispatcher_survives_callback_failure_and_stops():
    monitor = MouseMonitor(MagicMock())
    monitor._clicks.put((1, 2))
    monitor._clicks.put((3, 4))

    def notify(x, y):
        if x == 1:
            raise RuntimeError("failed callback")
        monitor._stop_event.set()

    monitor.on_click_event.side_effect = notify
    monitor._dispatch_clicks()
    assert monitor.on_click_event.call_count == 2
