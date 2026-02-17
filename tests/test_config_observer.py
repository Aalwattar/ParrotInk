from engine.config import Config


def test_config_observer_notification():
    """Verify that observers are notified of changes."""
    config = Config()
    notified = []

    def on_change(cfg):
        notified.append(cfg.interaction.sounds.volume)

    config.register_observer(on_change)

    config.update_and_save(
        {"interaction": {"sounds": {"volume": 90.0}}}, path="test_observer.toml", blocking=True
    )

    assert len(notified) == 1
    assert notified[0] == 90.0

    # Cleanup
    import os

    if os.path.exists("test_observer.toml"):
        os.remove("test_observer.toml")
