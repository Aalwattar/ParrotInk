from engine.config import load_config


def test_config_template_initialization(tmp_path):
    # Setup paths
    config_dir = tmp_path / "appdata"
    config_file = config_dir / "config.toml"

    # Run load_config which should copy the template
    # Note: load_config uses Path(__file__).parent.parent / "config.example.toml"
    # In this test environment, ensure the example exists relative to engine/config.py.
    config = load_config(config_file)

    # Check if file exists
    assert config_file.exists()

    # Read the content and verify the header and comments exist
    content = config_file.read_text(encoding="utf-8")
    assert "ParrotInk - Professional Voice-to-Text Configuration" in content
    # Note: Double check the actual line in config.example.toml
    # It has: # file_level = "error"
    assert '# file_level = "error"' in content

    # Verify the Pydantic model loaded it correctly
    assert config.logging.file_level == "error"
    assert config.logging.file_enabled  # Our new default in code and template


if __name__ == "__main__":
    import pytest

    pytest.main([__file__])
