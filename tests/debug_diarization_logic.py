import os
import sys

sys.path.append(os.getcwd())


from engine.injector import SmartInjector
from engine.transcription.speaker_manager import SpeakerManager


def debug_session():
    print("=== Diarization Debug Log ===")
    manager = SpeakerManager()
    injector = SmartInjector()

    # Mock the physical injection to just print to console
    import engine.injector

    engine.injector.inject_text = lambda t: print(f"  [TYPING]  '{repr(t)}'")
    engine.injector.inject_backspaces = lambda c: print(f"  [BACKSPC] {c}")

    def process_update(words, transcript, is_final=False):
        print(f"\n--- Update (Final={is_final}) ---")
        formatted = manager.format_with_speaker(words, transcript)
        print(f"  [RESULT]  '{repr(formatted)}'")
        injector.inject(formatted, is_final=is_final)
        if is_final:
            manager.commit_speaker(words)

    # SCENARIO 1: Speaker 1 starts talking
    process_update([{"text": "Hello", "speaker": "A"}], "Hello")

    # SCENARIO 2: Speaker 1 continues (Partial)
    process_update(
        [{"text": "Hello", "speaker": "A"}, {"text": "this", "speaker": "A"}], "Hello this"
    )

    # SCENARIO 3: Speaker 2 starts (Partial - The "And you can see" scenario)
    # Speaker 1 finalized, Speaker 2 starts
    process_update(
        [{"text": "Hello", "speaker": "A"}, {"text": "this", "speaker": "A"}],
        "Hello this",
        is_final=True,
    )

    # Speaker 2 begins
    process_update([{"text": "And", "speaker": "B"}], "And")

    # Speaker 2 continues
    process_update([{"text": "And", "speaker": "B"}, {"text": "you", "speaker": "B"}], "And you")

    # SCENARIO 4: The "Inconsistent" transition
    # What if the speaker is UNKNOWN briefly?
    process_update(
        [
            {"text": "And", "speaker": "B"},
            {"text": "you", "speaker": "B"},
            {"text": "can", "speaker": "UNKNOWN"},
        ],
        "And you can",
    )

    # Now it identifies "can" as Speaker 1 (Tone change)
    process_update(
        [
            {"text": "And", "speaker": "B"},
            {"text": "you", "speaker": "B"},
            {"text": "can", "speaker": "A"},
        ],
        "And you can",
    )


if __name__ == "__main__":
    debug_session()
