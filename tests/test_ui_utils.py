import pytest
from engine.ui_utils import get_app_version
from pathlib import Path
from unittest.mock import patch, mock_open

def test_get_app_version_success():
    # Mock pyproject.toml content
    pyproject_content = b"""
[project]
name = "voice2text"
version = "0.2.0-alpha"
"""
    with patch("builtins.open", mock_open(read_data=pyproject_content)):
        with patch("pathlib.Path.exists", return_value=True):
            version = get_app_version()
            assert version == "0.2.0-alpha"

def test_get_app_version_not_found():
    with patch("pathlib.Path.exists", return_value=False):
        version = get_app_version()
        assert version == "unknown"
