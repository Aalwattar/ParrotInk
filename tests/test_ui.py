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


def test_on_provider_change(mocker):
    """Test the callback for provider change."""
    mock_cb = mocker.Mock()
    mocker.patch("pystray.Icon")
    app = TrayApp(on_provider_change=mock_cb)

    # Simulate a menu item selection
    app._on_provider_selection(None, "openai")
    mock_cb.assert_called_once_with("openai")


def test_open_config(mocker, tmp_path):
    """Test the open config functionality."""
    mock_startfile = mocker.patch("os.startfile", create=True)
    mocker.patch("pystray.Icon")

    # Mock current working directory to use tmp_path
    mocker.patch("os.getcwd", return_value=str(tmp_path))
    # We need to make sure the absolute path exists for os.startfile in TrayApp
    # TrayApp does: Path("config.toml").absolute()
    # If we mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("pathlib.Path.exists", return_value=True)

    app = TrayApp()
    app._open_config(None, None)

    mock_startfile.assert_called_once()

def test_tray_app_availability(mocker):
    """Test that TrayApp stores availability status."""
    mocker.patch("pystray.Icon")
    availability = {"openai": True, "assemblyai": False}
    app = TrayApp(availability=availability)
    assert app.availability == availability
    
    # Test update
    new_availability = {"openai": False, "assemblyai": True}
    app.update_availability(new_availability)
    assert app.availability == new_availability