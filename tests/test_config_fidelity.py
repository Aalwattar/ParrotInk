import re
from pathlib import Path

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


def test_documented_example_matches_defaults_when_uncommented():
    """Every documented default must be valid and match the actual schema."""
    example = Path(__file__).resolve().parents[1] / "config.example.toml"
    assert Config.from_file(example).model_dump() == Config().model_dump()
    text = example.read_text(encoding="utf-8")
    uncommented = re.sub(r"^# ([A-Za-z_]+\s*=.*)$", r"\1", text, flags=re.MULTILINE)
    configured = Config(**tomlkit.parse(uncommented))
    assert configured.model_dump() == Config().model_dump()


def test_legacy_aliases_round_trip_with_comments(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('''# Legacy config
[transcription]
active_provider = "assemblyai" # provider comment
[providers.openai.tier1]
language = "fr" # language comment
[providers.openai.tier2]
prompt = "hello"
[providers.assemblyai.tier1]
language_code = "es"
[providers.assemblyai.tier2]
format_text = true
''', encoding="utf-8")
    config = Config.from_file(path)
    config.save(path, blocking=True)
    assert Config.from_file(path).model_dump() == config.model_dump()
    saved = path.read_text(encoding="utf-8")
    assert "active_provider" not in saved
    assert "tier1" not in saved and "tier2" not in saved
    assert "# provider comment" in saved and "# language comment" in saved
