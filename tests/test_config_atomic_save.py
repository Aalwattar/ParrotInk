import os
from unittest.mock import patch

import pytest

from engine.config import Config


def test_config_atomic_save_success(tmp_path):
    """Verify that config.save() creates a temporary file and then renames it."""
    config_path = tmp_path / "config.toml"
    config = Config()
    config.hotkeys.hotkey = "alt+f4"

    # We want to catch the os.replace call to verify the atomic swap
    with patch("os.replace", wraps=os.replace) as mock_replace:
        config.save(config_path, blocking=True)

        # Verify replace was called
        mock_replace.assert_called_once()
        args, _ = mock_replace.call_args
        src, dst = args

        assert str(dst) == str(config_path)
        assert ".tmp" in str(src)

    # Verify final file exists and has correct content
    assert config_path.exists()
    content = config_path.read_text()
    assert 'hotkey = "alt+f4"' in content


def test_config_atomic_save_failure_preserves_original(tmp_path):
    """Verify that if the write fails, the original config is untouched."""
    config_path = tmp_path / "config.toml"
    original_content = 'hotkey = "ctrl+alt+v"\n'
    config_path.write_text(original_content)

    config = Config()
    config.hotkeys.hotkey = "new+hotkey"

    # Mock write_text to fail on the temporary file
    # Note: we need to be careful with the patch scope
    with patch("pathlib.Path.write_text", side_effect=IOError("Disk Full")):
        with pytest.raises(IOError):
            config.save(config_path, blocking=True)

    # Original file should still be there with original content
    assert config_path.read_text() == original_content
    # Temporary file should not exist (ideally cleaned up or never finished)
    tmp_files = list(tmp_path.glob("*.tmp"))
    assert len(tmp_files) == 0 or not any(f.exists() for f in tmp_files)
