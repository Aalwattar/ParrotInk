import tomlkit

from engine.config import Config


def test_config_comment_preservation(tmp_path):
    """Verify that saving a config change does not strip comments."""
    config_path = tmp_path / "config.toml"

    # 1. Create a TOML file with comments
    content = """# Top level comment
[hotkeys]
# Hotkey comment
hotkey = "ctrl+alt+v" # Inline comment
hold_mode = false
"""
    config_path.write_text(content, encoding="utf-8")

    # 2. Load it
    config = Config.from_file(config_path)

    # 3. Modify a value
    config.hotkeys.hotkey = "ctrl+shift+x"

    # 4. Save it (blocking to ensure it finishes)
    config.save(config_path, blocking=True)

    # 5. Read the file back and check for comments
    saved_content = config_path.read_text(encoding="utf-8")

    assert "# Top level comment" in saved_content
    assert "# Hotkey comment" in saved_content
    assert "# Inline comment" in saved_content
    assert 'hotkey = "ctrl+shift+x"' in saved_content

    # Verify it's still valid TOML
    parsed = tomlkit.parse(saved_content)
    assert parsed["hotkeys"]["hotkey"] == "ctrl+shift+x"
