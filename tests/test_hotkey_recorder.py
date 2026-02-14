from engine.platform_win.hotkey_recorder import HotkeyRecorder


def test_hotkey_recorder_initialization():
    recorder = HotkeyRecorder()
    assert recorder is not None


def test_hotkey_validation():
    recorder = HotkeyRecorder()
    # Win+L is reserved
    assert recorder.is_valid(["cmd", "l"]) is False
    # Alt+F4 is reserved
    assert recorder.is_valid(["alt", "f4"]) is False
    # ctrl+alt+v is valid
    assert recorder.is_valid(["ctrl", "alt", "v"]) is True
