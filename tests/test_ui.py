from engine.ui import AppState, TrayApp


def test_app_state_enum():
    """Verify that the AppState enum has the required states."""
    assert AppState.IDLE.value == "idle"
    assert AppState.LISTENING.value == "listening"
    assert AppState.ERROR.value == "error"


def test_tray_app_initialization(mocker):
    """Test that TrayApp initializes with the IDLE state."""
    # Mock pystray.Icon to avoid opening a real tray icon in tests
    mocker.patch("pystray.Icon")
    app = TrayApp()
    assert app.state == AppState.IDLE


def test_tray_app_state_change(mocker):
    """Test that changing the app state works correctly."""
    mocker.patch("pystray.Icon")
    app = TrayApp()
    app.set_state(AppState.LISTENING)
    assert app.state == AppState.LISTENING
