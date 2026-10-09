from unittest.mock import MagicMock

from engine.mouse import MouseMonitor


def test_mouse_monitor_start_stop(mocker):
    thread_factory = mocker.patch("engine.mouse.threading.Thread")
    thread = thread_factory.return_value
    thread.is_alive.side_effect = [True, False]
    monitor = MouseMonitor(on_click_event=lambda x, y: None)
    monitor.start()
    assert monitor._is_running
    monitor.start()
    thread_factory.assert_called_once()
    thread.start.assert_called_once()
    monitor.stop()
    thread.join.assert_called_once_with(timeout=monitor.STOP_TIMEOUT)
    assert monitor._thread is None
    assert not monitor._is_running


def run_samples(mocker, samples, callback=None, positions=None):
    monitor = MouseMonitor(callback or MagicMock())
    monitor._stop_event = MagicMock()
    monitor._stop_event.is_set.return_value = False
    monitor._stop_event.wait.side_effect = [False] * (len(samples) - 1) + [True]
    mocker.patch("engine.mouse._read_button", side_effect=samples)
    position = mocker.patch(
        "engine.mouse._read_position", side_effect=positions or [(10, 20)] * len(samples)
    )
    monitor._poll()
    return monitor, position


def test_only_press_edges_emit_clicks(mocker):
    callback = MagicMock()
    _, position = run_samples(mocker, [False, True, True, False, True], callback)
    assert callback.call_count == 2
    callback.assert_called_with(10, 20)
    assert position.call_count == 2


def test_initial_held_button_is_ignored(mocker):
    callback = MagicMock()
    run_samples(mocker, [True, True, False, True], callback)
    callback.assert_called_once_with(10, 20)


def test_position_failure_does_not_emit_or_repeat(mocker):
    callback = MagicMock()
    run_samples(mocker, [False, True, True, False, True], callback, [None, (30, 40)])
    callback.assert_called_once_with(30, 40)


def test_callback_failure_logged_and_worker_recovers(mocker):
    callback = MagicMock(side_effect=[RuntimeError("callback failed"), None])
    log = mocker.patch("engine.mouse.logger.exception")
    monitor, _ = run_samples(mocker, [False, True, False, True], callback)
    assert callback.call_count == 2
    log.assert_called_once()
    assert not monitor._is_running


def test_native_read_failure_logged_and_resets_baseline(mocker):
    callback = MagicMock()
    log = mocker.patch("engine.mouse.logger.exception")
    run_samples(mocker, [False, RuntimeError("read failed"), True, False, True], callback)
    callback.assert_called_once_with(10, 20)
    log.assert_called_once()


def test_failed_join_retains_worker_and_refuses_second_start(mocker):
    factory = mocker.patch("engine.mouse.threading.Thread")
    thread = MagicMock()
    thread.is_alive.return_value = True
    monitor = MouseMonitor(MagicMock())
    monitor._thread = thread
    monitor._is_running = True
    monitor.stop()
    assert monitor._thread is thread
    assert monitor._stop_event.is_set()
    monitor.start()
    factory.assert_not_called()
    assert monitor._stop_event.is_set()


def test_stop_from_worker_does_not_join_itself(mocker):
    thread = MagicMock()
    thread.is_alive.return_value = True
    mocker.patch("engine.mouse.threading.current_thread", return_value=thread)
    monitor = MouseMonitor(MagicMock())
    monitor._thread = thread
    monitor.stop()
    thread.join.assert_not_called()
    assert monitor._stop_event.is_set()


def test_start_failure_resets_state(mocker):
    factory = mocker.patch("engine.mouse.threading.Thread")
    factory.return_value.start.side_effect = RuntimeError("start failed")
    monitor = MouseMonitor(MagicMock())
    import pytest

    with pytest.raises(RuntimeError, match="start failed"):
        monitor.start()
    assert monitor._thread is None
    assert not monitor._is_running


def test_button_reader_uses_high_bit_only(mocker):
    from engine.mouse import _read_button

    reader = mocker.patch("engine.mouse._get_button_state", side_effect=[1, 0x8000])
    assert not _read_button()
    assert _read_button()
    reader.assert_called_with(1)


def test_cursor_reader_success_and_failure(mocker):
    from engine.mouse import _read_position

    def fill(point):
        point._obj.x = 123
        point._obj.y = -45
        return True

    mocker.patch("engine.mouse._get_cursor_pos", side_effect=fill)
    assert _read_position() == (123, -45)
    mocker.patch("engine.mouse._get_cursor_pos", return_value=False)
    assert _read_position() is None
