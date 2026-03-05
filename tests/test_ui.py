from unittest.mock import patch


def test_app_state_enum():
    """Verify that the AppState enum has the required states."""
    from engine.ui import AppState

    assert AppState.IDLE.value == "idle"
    assert AppState.LISTENING.value == "listening"
    assert AppState.ERROR.value == "error"


def test_tray_app_initialization(mocker, config):
    """Test that TrayApp initializes with the IDLE state."""
    mocker.patch("engine.ui.pystray.Icon")
    from engine.ui import AppState, TrayApp

    app = TrayApp(config=config, initial_sounds_enabled=True)
    assert app.state == AppState.IDLE
    assert app.sounds_enabled is True


def test_tray_app_state_change(mocker, config):
    """Test that changing the app state works correctly."""
    mocker.patch("engine.ui.pystray.Icon")
    from engine.ui import AppState, TrayApp

    app = TrayApp(config=config, initial_sounds_enabled=True)
    app.set_state(AppState.LISTENING)
    assert app.state == AppState.LISTENING


def test_on_provider_change(mocker, config):
    """Test the callback for provider change."""
    mock_cb = mocker.Mock()
    mocker.patch("engine.ui.pystray.Icon")
    from engine.ui import TrayApp

    app = TrayApp(config=config, on_provider_change=mock_cb, initial_sounds_enabled=True)
    app._on_provider_selection(None, "openai")
    mock_cb.assert_called_once_with("openai")


def test_open_config(mocker, config, tmp_path):
    """Test the open config functionality."""
    mock_startfile = mocker.patch("os.startfile", create=True)
    mocker.patch("engine.ui.pystray.Icon")
    mocker.patch("os.getcwd", return_value=str(tmp_path))
    mocker.patch("pathlib.Path.exists", return_value=True)
    from engine.ui import TrayApp

    app = TrayApp(config=config, initial_sounds_enabled=True)
    app._open_config(None, None)
    mock_startfile.assert_called_once()


def test_tray_app_availability(mocker, config):
    """Test that TrayApp stores availability status."""
    mocker.patch("engine.ui.pystray.Icon")
    availability = {"openai": True, "assemblyai": False}
    from engine.ui import TrayApp

    app = TrayApp(config=config, availability=availability, initial_sounds_enabled=True)
    assert app.availability == availability
    new_availability = {"openai": False, "assemblyai": True}
    app.update_availability(new_availability)
    assert app.availability == new_availability


def test_tray_menu_structure(mocker, config):
    """Verify that the tray menu contains the version header and NOT the redundant Status item."""
    with patch("engine.ui.pystray.Icon") as mock_icon:
        from engine.ui import TrayApp

        TrayApp(config=config, initial_sounds_enabled=True)
        args, kwargs = mock_icon.call_args
        menu = args[3]
        items = list(menu)
        # First item should be version header
        assert "ParrotInk v" in items[0].text
        assert items[0].enabled is False
        # Second item is separator
        assert items[2].text == "Transcription"
        assert all(item.text != "Status: Ready" for item in items)

        # Check Transcription sub-menu
        trans_menu = items[2].submenu
        trans_items = list(trans_menu)
        assert trans_items[0].text == "Provider"
        # Index 1 is separator
        assert trans_items[2].text == "Performance Profile"
        assert trans_items[3].text == "Microphone Profile"
        assert trans_items[4].text == "Real-time Punctuation"

        # Check Providers sub-menu
        providers_menu = trans_items[0].submenu
        provider_items = list(providers_menu)
        assert provider_items[0].text == "OpenAI"
        assert provider_items[1].text == "AssemblyAI"


def test_tray_settings_menu_hold_mode(mocker, config):
    """Verify that the Settings menu contains the Hold to Talk toggle."""
    with patch("engine.ui.pystray.Icon") as mock_icon:
        from engine.ui import TrayApp

        TrayApp(config=config, initial_sounds_enabled=True)
        args, kwargs = mock_icon.call_args
        menu = args[3]
        items = list(menu)
        settings_item = next(item for item in items if item.text == "Settings")
        submenu_items = list(settings_item.submenu)
        hold_toggle = next(item for item in submenu_items if item.text == "Hold to Talk")
        assert hold_toggle is not None


def test_tray_settings_menu(mocker, config):
    """Verify that the Settings menu contains the sound toggle."""
    with patch("engine.ui.pystray.Icon") as mock_icon:
        from engine.ui import TrayApp

        mock_toggle = mocker.Mock()
        app = TrayApp(config=config, on_toggle_sounds=mock_toggle, initial_sounds_enabled=True)
        args, kwargs = mock_icon.call_args
        menu = args[3]
        items = list(menu)
        settings_item = next(item for item in items if item.text == "Settings")
        submenu_items = list(settings_item.submenu)
        sound_toggle = next(item for item in submenu_items if item.text == "Enable Audio Feedback")
        is_checked = sound_toggle.checked
        if callable(is_checked):
            is_checked = is_checked(sound_toggle)
        assert is_checked is True
        app._on_toggle_sounds_clicked(None, sound_toggle)
        assert app.sounds_enabled is False
        mock_toggle.assert_called_once_with(False)
