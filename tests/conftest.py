import os
from unittest.mock import patch

import pytest

from engine.config import Config

# Helper to check if running in GitHub Actions
IS_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


@pytest.fixture
def config():
    return Config()


@pytest.fixture(autouse=True)
def mock_audio_feedback():
    with patch("engine.audio_feedback.play_sound") as mock:
        yield mock


@pytest.fixture(autouse=True)
def guard_update_manager():
    """Prevent UpdateManager from starting threads or making network calls in tests."""
    with patch("engine.services.updates.UpdateManager.start"):
        yield
