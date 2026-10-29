from unittest.mock import patch

import pytest

from engine.injector import SmartInjector, inject_backspaces, inject_text
from engine.platform_win.constants import BACKSPACE_SAFETY_CAP
from engine.platform_win.keys import KEYEVENTF_UNICODE, VK_RETURN


# We need to patch the USER32 object inside engine.injector
@patch("engine.injector.USER32")
def test_inject_text_calls_sendinput(mock_user32):
    # Setup mock
    mock_user32.SendInput.return_value = 2  # 2 inputs for 1 char

    inject_text("a")

    # Verify SendInput was called
    assert mock_user32.SendInput.called
    args = mock_user32.SendInput.call_args[0]
    # args[0] is nInputs
    assert args[0] == 2  # 1 down, 1 up
    # args[2] is cbSize
    assert args[2] > 0


@patch("engine.injector.USER32")
def test_inject_backspaces_calls_sendinput(mock_user32):
    mock_user32.SendInput.return_value = 4  # 4 inputs for 2 backspaces

    inject_backspaces(2)

    assert mock_user32.SendInput.called
    args = mock_user32.SendInput.call_args[0]
    assert args[0] == 4  # 2 down, 2 up


def test_unicode_injection_preserves_surrogate_pairs_and_newlines(mocker):
    send = mocker.patch("engine.injector.USER32.SendInput", side_effect=lambda count, *_: count)
    inject_text("a\U0001f600\r\nb")
    events = send.call_args.args[1]._obj
    assert [(event.union.ki.wVk, event.union.ki.wScan) for event in events[::2]] == [
        (0, ord("a")),
        (0, 0xD83D),
        (0, 0xDE00),
        (VK_RETURN, 0),
        (0, ord("b")),
    ]
    assert all(event.union.ki.dwFlags & KEYEVENTF_UNICODE for event in events[:6])


@pytest.mark.parametrize("sent", [0, 1])
@pytest.mark.parametrize("operation", [lambda: inject_text("a"), lambda: inject_backspaces(1)])
def test_incomplete_input_raises(mocker, sent, operation):
    mocker.patch("engine.injector.USER32.SendInput", return_value=sent)
    with pytest.raises(OSError, match="SendInput"):
        operation()


def test_failed_input_does_not_commit_partial_text(mocker):
    mocker.patch("engine.injector.USER32.SendInput", return_value=0)
    injector = SmartInjector()
    with pytest.raises(OSError):
        injector.inject("new partial")
    assert injector.last_text == ""


@pytest.mark.parametrize("replacement", ["replacement", "\nreplacement"])
def test_oversized_correction_stops_before_any_input(mocker, replacement):
    send = mocker.patch("engine.injector.USER32.SendInput")
    injector = SmartInjector()
    injector.last_text = "a" * (BACKSPACE_SAFETY_CAP + 1)
    with pytest.raises(OSError, match="safety limit"):
        injector.inject(replacement)
    send.assert_not_called()
    assert injector.last_text == "a" * (BACKSPACE_SAFETY_CAP + 1)


def test_correction_at_safety_limit_replaces_entire_suffix(mocker):
    send = mocker.patch("engine.injector.USER32.SendInput", side_effect=lambda count, *_: count)
    injector = SmartInjector()
    injector.last_text = "a" * BACKSPACE_SAFETY_CAP
    injector.inject("b")
    assert [call.args[0] for call in send.call_args_list] == [2 * BACKSPACE_SAFETY_CAP, 2]
    assert injector.last_text == "b"
