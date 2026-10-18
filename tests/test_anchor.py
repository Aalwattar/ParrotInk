import pytest

from engine.anchor import Anchor
from engine.platform_win.editor_focus import FocusedElement


def test_anchor_initialization():
    anchor = Anchor(scope="window")
    assert anchor.scope == "window"
    assert anchor.hwnd is None


def test_anchor_match_window(mocker):
    # Mock ctypes wrappers
    mock_hwnd = 12345
    mocker.patch("engine.anchor.get_foreground_window", return_value=mock_hwnd)
    mocker.patch("engine.anchor.get_window_thread_process_id", return_value=(0, 999))

    anchor = Anchor.capture_current(scope="window")
    assert anchor.hwnd == mock_hwnd

    # Mock WindowFromPoint for is_match

    # We use a side_effect that returns the input HWND as its own ancestor (root)
    # to simulate simple windows that are their own roots.
    mocker.patch("engine.anchor.get_ancestor", side_effect=lambda h, f: h)

    # 1. Click on the same window
    mocker.patch("engine.anchor.window_from_point", return_value=mock_hwnd)
    assert anchor.is_match(100, 100) is True

    # 2. Click on a different window
    other_hwnd = 67890
    mocker.patch("engine.anchor.window_from_point", return_value=other_hwnd)
    assert anchor.is_match(500, 500) is False


def test_anchor_match_control(mocker):
    mock_hwnd = 12345
    mock_control = 55555
    mocker.patch("engine.anchor.get_foreground_window", return_value=mock_hwnd)
    mocker.patch("engine.anchor.get_window_thread_process_id", return_value=(0, 999))

    # Mock _get_focused_control to return our specific control
    mocker.patch("engine.anchor.Anchor._get_focused_control", return_value=mock_control)

    anchor = Anchor.capture_current(scope="control")
    assert anchor.control_hwnd == mock_control

    # 1. Click on the control
    mocker.patch("engine.anchor.window_from_point", return_value=mock_control)
    assert anchor.is_match(10, 10) is True

    # 2. Click on the parent window but NOT the control
    mocker.patch("engine.anchor.window_from_point", return_value=mock_hwnd)
    assert anchor.is_match(10, 10) is False


def test_editor_click_outside_shared_window_cancels(mocker):
    editor = FocusedElement((1, 2, 3), 50004, (10, 10, 300, 200), read_only=False)
    mocker.patch("engine.anchor.get_foreground_window", return_value=123)
    mocker.patch("engine.anchor.get_window_thread_process_id", return_value=(0, 999))
    mocker.patch("engine.anchor.Anchor._get_focused_control", return_value=123)
    mocker.patch("engine.anchor.window_from_point", return_value=123)
    mocker.patch("engine.anchor.read_focused_element", return_value=editor, create=True)
    anchor = Anchor.capture_current("control")
    assert anchor.is_match(50, 50)
    assert not anchor.is_match(350, 50)


def test_editor_focus_change_cancels_even_with_cursor_over_original_field(mocker):
    editor = FocusedElement((1, 2, 3), 50004, (10, 10, 300, 200), read_only=False)
    other = FocusedElement((4, 5, 6), 50004, (400, 10, 700, 200), read_only=False)
    mocker.patch("engine.anchor.get_foreground_window", return_value=123)
    mocker.patch("engine.anchor.get_window_thread_process_id", return_value=(0, 999))
    mocker.patch("engine.anchor.Anchor._get_focused_control", return_value=123)
    mocker.patch("engine.anchor.window_from_point", return_value=123)
    read = mocker.patch("engine.anchor.read_focused_element", return_value=editor, create=True)
    anchor = Anchor.capture_current("control")
    read.return_value = other
    assert not anchor.is_match(50, 50)


@pytest.mark.parametrize(
    "kind,enabled,password,read_only,expected",
    [
        (50004, True, False, False, True),
        (50004, True, False, None, True),
        (50025, True, False, False, True),
        (50003, True, False, False, True),
        (50003, True, False, True, False),
        (50030, True, False, False, True),
        (50029, True, False, False, True),
        (50029, True, False, True, False),
        (50029, True, False, None, False),
        (50004, False, False, False, False),
        (50004, True, True, False, False),
        (50004, True, False, True, False),
        (50030, True, False, True, False),
        (50030, True, False, None, False),
        (50026, True, False, None, False),
        (50032, True, False, None, False),
    ],
)
def test_target_capability_uses_editability_not_just_control_type(
    mocker, kind, enabled, password, read_only, expected
):
    focused = FocusedElement((1, 2), kind, (10, 10, 100, 100), enabled, password, read_only)
    mocker.patch("engine.anchor.get_foreground_window", return_value=123)
    mocker.patch("engine.anchor.get_window_thread_process_id", return_value=(0, 999))
    mocker.patch("engine.anchor.Anchor._get_focused_control", return_value=123)
    mocker.patch("engine.anchor.read_focused_element", return_value=focused)
    assert Anchor.capture_current("control").can_dictate is expected
    assert Anchor.capture_current("window").can_dictate is expected


@pytest.mark.parametrize("scope", ["control", "window"])
def test_editability_loss_stops_an_existing_target(mocker, scope):
    from dataclasses import replace

    writable = FocusedElement((1, 2), 50004, (10, 10, 100, 100), read_only=False)
    mocker.patch("engine.anchor.get_foreground_window", return_value=123)
    mocker.patch("engine.anchor.get_window_thread_process_id", return_value=(0, 999))
    mocker.patch("engine.anchor.get_ancestor", side_effect=lambda h, flags: h)
    mocker.patch("engine.anchor.Anchor._get_focused_control", return_value=123)
    read = mocker.patch("engine.anchor.read_focused_element", return_value=writable)
    anchor = Anchor.capture_current(scope)
    assert anchor.has_focus()
    read.return_value = replace(writable, read_only=True)
    assert not anchor.has_focus()
