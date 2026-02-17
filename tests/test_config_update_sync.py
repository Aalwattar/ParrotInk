from engine.config import Config, load_config


def test_config_update_and_save(tmp_path):
    """Verify that update_and_save persists changes to disk."""
    config_file = tmp_path / "config.toml"
    config = Config()
    config.interaction.sounds.volume = 50
    config.save(config_file, blocking=True)

    # Update and save
    new_volume = 80
    config.update_and_save(
        {"interaction": {"sounds": {"volume": new_volume}}}, path=config_file, blocking=True
    )

    # Reload and verify
    reloaded = load_config(config_file)
    assert reloaded.interaction.sounds.volume == new_volume


def test_config_update_and_save_deep_merge(tmp_path):
    """Verify that update_and_save performs a deep merge correctly."""
    config_file = tmp_path / "config.toml"
    config = Config()
    config.hotkeys.hotkey = "ctrl+shift+x"
    config.interaction.sounds.enabled = False
    config.save(config_file, blocking=True)

    # Update only one field
    config.update_and_save(
        {"interaction": {"sounds": {"enabled": True}}}, path=config_file, blocking=True
    )

    # Reload and verify both fields
    reloaded = load_config(config_file)
    assert reloaded.interaction.sounds.enabled is True
    assert reloaded.hotkeys.hotkey == "ctrl+shift+x"
