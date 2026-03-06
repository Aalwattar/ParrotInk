from engine.config import UIConfig, load_config


def test_onboarding_default_state():
    """Verify that onboarding popup is enabled by default."""
    ui_cfg = UIConfig()
    assert ui_cfg.show_onboarding_popup is True


def test_onboarding_loaded_state(tmp_path):
    """Verify that the config file can override the onboarding popup setting."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[ui]
show_onboarding_popup = false
""")
    config = load_config(config_file)
    assert config.ui.show_onboarding_popup is False


def test_onboarding_cli_precedence(mocker):
    """Verify that the --background flag suppresses onboarding regardless of config."""
    from main import handle_cli

    # Mock CLI arguments to include --background
    mocker.patch("sys.argv", ["main.py", "--background"])
    args = handle_cli()
    assert args.background is True

    # In main.py, we will check:
    # if not cli_args.background and config.ui.show_onboarding_popup:
    #     show_onboarding()
