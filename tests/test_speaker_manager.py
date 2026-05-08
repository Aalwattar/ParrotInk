from engine.transcription.speaker_manager import SpeakerManager


def test_speaker_manager_formats_compact():
    """Verifies that [S1] Hello world is returned for speaker 1."""
    manager = SpeakerManager()
    words = [{"text": "Hello", "speaker": 1}, {"text": "world", "speaker": 1}]
    transcript = "Hello world"

    result = manager.format_with_speaker(words, transcript)
    assert result == "[S1] Hello world"
    # Note: active_speaker is only updated after commit_speaker
    manager.commit_speaker(words)
    assert manager.active_speaker == "S1"


def test_speaker_manager_tracks_speaker_change():
    """Verifies that it updates correctly when the speaker changes."""
    manager = SpeakerManager()

    # First segment: Speaker 1
    words1 = [{"text": "Hello", "speaker": 1}]
    transcript1 = "Hello"
    result1 = manager.format_with_speaker(words1, transcript1)
    assert result1 == "[S1] Hello"
    manager.commit_speaker(words1)
    assert manager.active_speaker == "S1"

    # Second segment: Speaker 2
    words2 = [{"text": "Hi", "speaker": 2}]
    transcript2 = "Hi"
    result2 = manager.format_with_speaker(words2, transcript2)
    assert result2 == "\n[S2] Hi"
    manager.commit_speaker(words2)
    assert manager.active_speaker == "S2"


def test_speaker_manager_mid_segment_change():
    """Verifies speaker change within a single word list."""
    manager = SpeakerManager()
    words = [
        {"text": "Hello", "speaker": "A"},
        {"text": "How", "speaker": "B"},
    ]
    result = manager.format_with_speaker(words, "Hello How")
    assert result == "[S1] Hello\n[S2] How"
    manager.commit_speaker(words)
    assert manager.active_speaker == "S2"


def test_speaker_manager_mapping_and_unknown():
    """Verifies A/B/C mapping and UNKNOWN suppression."""
    manager = SpeakerManager()

    # UNKNOWN should be ignored
    words1 = [{"text": "Hello", "speaker": "UNKNOWN"}]
    result1 = manager.format_with_speaker(words1, "Hello")
    assert result1 == "Hello"
    manager.commit_speaker(words1)
    assert manager.active_speaker is None

    # Mapping A to S1
    words2 = [{"text": "Hi", "speaker": "A"}]
    result2 = manager.format_with_speaker(words2, "Hi")
    assert result2 == "[S1] Hi"
    manager.commit_speaker(words2)
    assert manager.active_speaker == "S1"

    # Mapping B to S2 with newline
    words3 = [{"text": "Hey", "speaker": "B"}]
    result3 = manager.format_with_speaker(words3, "Hey")
    assert result3 == "\n[S2] Hey"
    manager.commit_speaker(words3)
    assert manager.active_speaker == "S2"


def test_speaker_manager_no_words():
    """Verifies it returns original transcript if words list is empty."""
    manager = SpeakerManager()
    result = manager.format_with_speaker([], "Hello")
    assert result == "Hello"
    assert manager.active_speaker is None


def test_speaker_manager_no_speaker_in_words():
    """Verifies it returns original transcript if no speaker field is present."""
    manager = SpeakerManager()
    words = [{"text": "Hello"}]
    result = manager.format_with_speaker(words, "Hello")
    assert result == "Hello"
    manager.commit_speaker(words)
    assert manager.active_speaker is None
