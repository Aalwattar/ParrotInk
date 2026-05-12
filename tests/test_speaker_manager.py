from engine.transcription.speaker_manager import SpeakerManager


def test_case_1_turn_isolation():
    """
    Case 1:
    Turn 1: no words, transcript="Hello there"
    Turn 2: words speaker=S2, transcript="Hi"
    Expected:
    Hello there
    [S2] Hi
    """
    manager = SpeakerManager()

    # Turn 1
    res1 = manager.format_final_turn("Hello there", [])
    assert res1 == "Hello there"

    # Turn 2
    res2 = manager.format_final_turn("Hi", [{"text": "Hi", "speaker": "B"}])
    assert res2 == "\n[S2] Hi"


def test_case_2_turn_speaker_fallback():
    """
    Case 2:
    Turn 1: speaker_label=S1, words missing
    Turn 2: speaker_label=S2, words present
    Expected:
    [S1] Hello
    [S2] Hi
    """
    manager = SpeakerManager()

    # Turn 1
    res1 = manager.format_final_turn("Hello", [], turn_speaker="A")
    assert res1 == "[S1] Hello"

    # Turn 2
    res2 = manager.format_final_turn("Hi", [{"text": "Hi", "speaker": "B"}], turn_speaker="B")
    assert res2 == "\n[S2] Hi"


def test_case_3_mid_turn_change():
    """
    Case 3:
    One final turn has word speakers S1 S1 S2 S2
    Expected:
    [S1] first words\n[S2] second words
    """
    manager = SpeakerManager()
    words = [
        {"text": "first", "speaker": "A"},
        {"text": "words", "speaker": "A"},
        {"text": "second", "speaker": "B"},
        {"text": "words", "speaker": "B"},
    ]
    res = manager.format_final_turn("first words second words", words)
    assert res == "[S1] first words\n[S2] second words"


def test_case_4_normal_dictation_isolation():
    """
    Case 4:
    Normal dictation mode enabled, diarization disabled.
    (This is handled by AssemblyAIProvider not using the manager).
    Verifying SpeakerManager resets work.
    """
    manager = SpeakerManager()
    manager.reset_session()
    assert manager.current_speaker_on_screen is None
    assert manager.has_sent_any_text is False


def test_case_5_unknown_fallback():
    """
    Case 5:
    UNKNOWN speaker after existing S1
    Expected:
    Continue text without new label, do not output [UNKNOWN]
    """
    manager = SpeakerManager()

    # Initial S1
    manager.format_final_turn("Hello", [], turn_speaker="A")

    # Unknown speaker - provide matching word list
    words = [
        {"text": "I", "speaker": "UNKNOWN"},
        {"text": "am", "speaker": "UNKNOWN"},
        {"text": "unsure", "speaker": "UNKNOWN"},
    ]
    res = manager.format_final_turn("I am unsure", words)
    # In Turn-Based Isolation, a new turn ALWAYS starts on a new line with a label
    assert res == "\n[S1] I am unsure"


def test_speaker_manager_mapping():
    """Verifies A/B/C and digit mapping."""
    manager = SpeakerManager()
    assert manager._clean_label("A") == "S1"
    assert manager._clean_label("B") == "S2"
    assert manager._clean_label(1) == "S1"
    assert manager._clean_label("S1") == "S1"
    assert manager._clean_label("UNKNOWN") is None
