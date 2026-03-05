import pytest

from engine.config import Config


def test_config_smart_placement(tmp_path):
    """Verify that new keys are inserted before their commented-out defaults."""
    config_path = tmp_path / "config.toml"

    # Create a TOML file with commented-out defaults
    content = """[hotkeys]
# The key combination used to trigger dictation.
# hotkey = "ctrl+alt+v"

# If true, you must HOLD the hotkey while talking.
# hold_mode = false
"""
    config_path.write_text(content, encoding="utf-8")

    # Load and change a non-default value (hotkey defaults to ctrl+alt+v, so change it)
    config = Config.from_file(config_path)
    config.hotkeys.hotkey = "ctrl+shift+z"
    config.save(config_path, blocking=True)

    # Check placement
    saved_content = config_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in saved_content.splitlines() if line.strip()]

    # Find indices
    try:
        # We need to find the ACTIVE line (not a comment)
        hotkey_idx = next(i for i, ln in enumerate(lines) if ln.startswith("hotkey ="))
        # We need to find the COMMENTED line
        comment_idx = next(i for i, ln in enumerate(lines) if ln.startswith("# hotkey ="))

        # Should be BEFORE the comment
        msg = f"Hotkey should be before comment. Content:\n{saved_content}"
        assert hotkey_idx < comment_idx, msg
    except StopIteration:
        pytest.fail(f"Could not find expected lines in:\n{saved_content}")


def test_config_smart_placement_nested(tmp_path):
    """Verify smart placement works in nested tables."""
    config_path = tmp_path / "config.toml"

    content = """[interaction.sounds]
# Volume of the feedback sounds.
# volume = 30
"""
    config_path.write_text(content, encoding="utf-8")

    config = Config.from_file(config_path)
    config.interaction.sounds.volume = 50
    config.save(config_path, blocking=True)

    saved_content = config_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in saved_content.splitlines() if line.strip()]

    vol_idx = next(i for i, ln in enumerate(lines) if ln.startswith("volume ="))
    comment_idx = next(i for i, ln in enumerate(lines) if ln.startswith("# volume ="))

    assert vol_idx < comment_idx
