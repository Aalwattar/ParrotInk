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


def test_background_saves_follow_update_order(tmp_path, monkeypatch):
    import os
    import threading

    path = tmp_path / "config.toml"
    config = Config()
    first_write = threading.Event()
    release_write = threading.Event()
    replace = os.replace
    calls = []

    def delayed_replace(source, destination):
        calls.append(source)
        if len(calls) == 1:
            first_write.set()
            assert release_write.wait(5)
        replace(source, destination)

    monkeypatch.setattr(os, "replace", delayed_replace)
    config.update_and_save({"hotkeys": {"hotkey": "first"}}, path)
    assert first_write.wait(5)
    second = threading.Thread(target=lambda: config.update_and_save(
        {"hotkeys": {"hotkey": "second"}}, path, blocking=True
    ))
    second.start()
    release_write.set()
    second.join(5)
    assert not second.is_alive()
    assert Config.from_file(path).hotkeys.hotkey == "second"
