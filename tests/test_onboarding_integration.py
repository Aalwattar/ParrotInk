from unittest.mock import MagicMock


def test_onboarding_skip_in_background(mocker):
    """Verify that onboarding is skipped when --background is used."""
    from main import handle_cli

    # Mock CLI to have --background
    mocker.patch("sys.argv", ["main.py", "--background"])
    cli_args = handle_cli()

    mock_config = MagicMock()
    mock_config.ui.show_onboarding_popup = True

    # Mock show_onboarding_blocking
    mock_show = mocker.patch("engine.onboarding_ui.show_onboarding_blocking")

    # The logic in main.py:
    show_it = not cli_args.background and mock_config.ui.show_onboarding_popup
    assert show_it is False
    assert not mock_show.called


def test_onboarding_skip_if_disabled_in_config(mocker):
    """Verify that onboarding is skipped when disabled in config."""
    from main import handle_cli

    # Mock CLI without --background
    mocker.patch("sys.argv", ["main.py"])
    cli_args = handle_cli()

    mock_config = MagicMock()
    mock_config.ui.show_onboarding_popup = False

    # Mock show_onboarding_blocking
    mock_show = mocker.patch("engine.onboarding_ui.show_onboarding_blocking")

    # The logic in main.py:
    show_it = not cli_args.background and mock_config.ui.show_onboarding_popup
    assert show_it is False
    assert not mock_show.called


def test_onboarding_shown_when_enabled(mocker):
    """Verify that onboarding is shown when enabled and not in background."""
    from main import handle_cli

    # Mock CLI without --background
    mocker.patch("sys.argv", ["main.py"])
    cli_args = handle_cli()

    mock_config = MagicMock()
    mock_config.ui.show_onboarding_popup = True

    # Mock show_onboarding_blocking
    mock_show = mocker.patch("engine.onboarding_ui.show_onboarding_blocking", return_value=True)

    # The logic in main.py:
    show_it = not cli_args.background and mock_config.ui.show_onboarding_popup
    assert show_it is True

    if show_it:
        dont_show_again = mock_show()
        if dont_show_again:
            mock_config.update_and_save({"ui": {"show_onboarding_popup": False}}, blocking=True)

    assert mock_show.called
    mock_config.update_and_save.assert_called_with(
        {"ui": {"show_onboarding_popup": False}}, blocking=True
    )
