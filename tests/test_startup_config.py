from engine.config import Config


def test_config_run_at_startup_default():
    config = Config()
    assert config.interaction.run_at_startup is False


def test_config_run_at_startup_persistence(tmp_path):
    config_path = tmp_path / "config.toml"
    config = Config()
    
    # Enable and save
    config.interaction.run_at_startup = True
    config.save(config_path, blocking=True)
    
    # Load and verify
    new_config = Config.from_file(config_path)
    assert new_config.interaction.run_at_startup is True
