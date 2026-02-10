import time

from engine.signals import ShutdownHandler


def test_shutdown_handler_first_press(mocker):
    """Verify first press sets pending state and prints message."""
    mock_print = mocker.patch("builtins.print")
    handler = ShutdownHandler(window=3)

    handler.handle(None, None)

    assert handler.shutdown_pending
    assert not handler.should_exit
    expected_msg = "\nCtrl+C received. Press Ctrl+C again within 3 seconds to force exit."
    mock_print.assert_any_call(expected_msg, flush=True)


def test_shutdown_handler_second_press_within_window(mocker):
    """Verify second press within window calls os._exit."""
    mocker.patch("builtins.print")
    mock_exit = mocker.patch("os._exit")
    handler = ShutdownHandler(window=3)

    handler.handle(None, None)  # First press
    assert handler.shutdown_pending

    handler.handle(None, None)  # Second press
    assert handler.should_exit
    mock_exit.assert_called_once_with(1)


def test_shutdown_handler_window_expiry(mocker):
    """Verify pending state clears after window expires."""
    mocker.patch("builtins.print")
    handler = ShutdownHandler(window=0.1)

    handler.handle(None, None)
    assert handler.shutdown_pending

    time.sleep(0.2)

    handler.handle(None, None)  # This should be treated as a new first press
    assert not handler.should_exit
    assert handler.shutdown_pending
