import pytest
import tomli_w

from engine.config import Config, ConfigError


def test_config_reload_success(tmp_path):
    # 1. Create initial config file
    config_path = tmp_path / "config.toml"
    initial_data = {"hotkeys": {"hotkey": "ctrl+alt+v", "hold_mode": False}}
    config_path.write_text(tomli_w.dumps(initial_data), encoding="utf-8")

    # 2. Load config
    cfg = Config.from_file(config_path)
    assert cfg.hotkeys.hotkey == "ctrl+alt+v"

    # 3. Simulate manual edit on disk
    updated_data = {"hotkeys": {"hotkey": "ctrl+alt+r", "hold_mode": True}}
    config_path.write_text(tomli_w.dumps(updated_data), encoding="utf-8")

    # 4. Reload
    cfg.reload(path=config_path)

    # 5. Verify updates
    assert cfg.hotkeys.hotkey == "ctrl+alt+r"
    assert cfg.hotkeys.hold_mode is True


def test_config_reload_observer_notification(tmp_path):
    config_path = tmp_path / "config.toml"
    config_path.write_text(tomli_w.dumps({"hotkeys": {"hotkey": "v"}}), encoding="utf-8")

    cfg = Config.from_file(config_path)

    notifications = []

    def observer(c):
        notifications.append(c.hotkeys.hotkey)

    cfg.register_observer(observer)

    # Update and reload
    config_path.write_text(tomli_w.dumps({"hotkeys": {"hotkey": "r"}}), encoding="utf-8")
    cfg.reload(path=config_path)

    assert len(notifications) == 1
    assert notifications[0] == "r"


def test_config_reload_failure_preserves_state(tmp_path):
    config_path = tmp_path / "config.toml"
    config_path.write_text(tomli_w.dumps({"hotkeys": {"hotkey": "v"}}), encoding="utf-8")

    cfg = Config.from_file(config_path)

    # Corrupt the file on disk
    config_path.write_text("invalid = [toml", encoding="utf-8")

    # Reload should fail but preserve old state
    with pytest.raises(ConfigError):
        cfg.reload(path=config_path)

    assert cfg.hotkeys.hotkey == "v"
