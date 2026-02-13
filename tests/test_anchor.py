from engine.anchor import Anchor


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
    # 1. Click on the same window
    mocker.patch("engine.anchor.window_from_point", return_value=mock_hwnd)
    mocker.patch("engine.anchor.get_ancestor", return_value=mock_hwnd)
    assert anchor.is_match(100, 100) is True

    # 2. Click on a different window
    other_hwnd = 67890
    mocker.patch("engine.anchor.window_from_point", return_value=other_hwnd)
    mocker.patch("engine.anchor.get_ancestor", return_value=other_hwnd)
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
