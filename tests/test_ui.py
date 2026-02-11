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
    app = TrayApp(initial_sounds_enabled=True)
    assert app.state == AppState.IDLE
    assert app.sounds_enabled is True


def test_tray_app_state_change(mocker):
    """Test that changing the app state works correctly."""
    mocker.patch("pystray.Icon")
    app = TrayApp(initial_sounds_enabled=True)
    app.set_state(AppState.LISTENING)
    assert app.state == AppState.LISTENING


def test_on_provider_change(mocker):
    """Test the callback for provider change."""
    mock_cb = mocker.Mock()
    mocker.patch("pystray.Icon")
    app = TrayApp(on_provider_change=mock_cb, initial_sounds_enabled=True)

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

    app = TrayApp(initial_sounds_enabled=True)
    app._open_config(None, None)

    mock_startfile.assert_called_once()


def test_tray_app_availability(mocker):
    """Test that TrayApp stores availability status."""
    mocker.patch("pystray.Icon")
    availability = {"openai": True, "assemblyai": False}
    app = TrayApp(availability=availability, initial_sounds_enabled=True)
    assert app.availability == availability

    # Test update
    new_availability = {"openai": False, "assemblyai": True}
    app.update_availability(new_availability)
    assert app.availability == new_availability


def test_tray_menu_structure(mocker):
    """Verify that the tray menu does NOT contain the redundant Status: Ready item."""
    mock_icon = mocker.patch("pystray.Icon")
    TrayApp(initial_sounds_enabled=True)

    args, kwargs = mock_icon.call_args
    menu = args[3]
    items = list(menu)

    # After fix: items[0].text should be "OpenAI"
    assert items[0].text == "OpenAI"
    # Ensure it's NOT the old label
    assert items[0].text != "Status: Ready"


def test_tray_settings_menu(mocker):
    """Verify that the Settings menu contains the sound toggle."""
    mock_icon = mocker.patch("pystray.Icon")
    mock_toggle = mocker.Mock()
    app = TrayApp(on_toggle_sounds=mock_toggle, initial_sounds_enabled=True)

    args, kwargs = mock_icon.call_args
    menu = args[3]
    items = list(menu)

    # Find Settings menu item
    settings_item = next(item for item in items if item.text == "Settings")

    # Use the discovered .submenu attribute
    submenu_items = list(settings_item.submenu)

    sound_toggle = next(item for item in submenu_items if item.text == "Enable Audio Feedback")
    # checked might be a callable or a bool depending on how pystray processes it
    is_checked = sound_toggle.checked
    if callable(is_checked):
        is_checked = is_checked(sound_toggle)
    assert is_checked is True

    # Simulate toggle
    app._on_toggle_sounds_clicked(None, sound_toggle)
    assert app.sounds_enabled is False
    mock_toggle.assert_called_once_with(False)
