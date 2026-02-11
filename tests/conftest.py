import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_audio_feedback():
    with patch("engine.audio_feedback.play_sound") as mock:
        yield mock
