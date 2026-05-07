from engine.transcription.speaker_manager import SpeakerManager


def test_speaker_manager_formats_compact():
    """Verifies that [S1] Hello world is returned for speaker 1."""
    manager = SpeakerManager()
    words = [{"text": "Hello", "speaker": 1}, {"text": "world", "speaker": 1}]
    transcript = "Hello world"

    result = manager.format_with_speaker(words, transcript)
    assert result == "[S1] Hello world"
    assert manager.current_speaker == 1


def test_speaker_manager_tracks_speaker_change():
    """Verifies that it updates correctly when the speaker changes."""
    manager = SpeakerManager()

    # First segment: Speaker 1
    words1 = [{"text": "Hello", "speaker": 1}]
    transcript1 = "Hello"
    result1 = manager.format_with_speaker(words1, transcript1)
    assert result1 == "[S1] Hello"
    assert manager.current_speaker == 1

    # Second segment: Speaker 2
    words2 = [{"text": "Hi", "speaker": 2}]
    transcript2 = "Hi"
    result2 = manager.format_with_speaker(words2, transcript2)
    assert result2 == "[S2] Hi"
    assert manager.current_speaker == 2


def test_speaker_manager_no_words():
    """Verifies it returns original transcript if words list is empty."""
    manager = SpeakerManager()
    result = manager.format_with_speaker([], "Hello")
    assert result == "Hello"
    assert manager.current_speaker is None


def test_speaker_manager_no_speaker_in_words():
    """Verifies it returns original transcript if no speaker field is present."""
    manager = SpeakerManager()
    words = [{"text": "Hello"}]
    result = manager.format_with_speaker(words, "Hello")
    assert result == "Hello"
    assert manager.current_speaker is None
