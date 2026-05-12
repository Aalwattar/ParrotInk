import os
import sys

sys.path.append(os.getcwd())


from engine.injector import SmartInjector
from engine.transcription.speaker_manager import SpeakerManager


def debug_session():
    print("=== Diarization Turn-Based Debug Log ===")
    manager = SpeakerManager()
    injector = SmartInjector()

    # Mock the physical injection to just print to console
    import engine.injector

    engine.injector.inject_text = lambda t: print(f"  [TYPING]  '{t}'")
    engine.injector.inject_backspaces = lambda c: print(f"  [BACKSPC] {c}")

    def process_update(words, transcript, is_final=False, turn_speaker=None):
        print(f"\n--- Update (Final={is_final}) ---")
        if is_final:
            # Format the final turn with labels and newlines
            text = manager.format_final_turn(transcript, words, turn_speaker)
        else:
            # HUD/Partial: Send raw, unformatted text
            text = transcript

        print(f"  [TEXT]    '{repr(text)}'")
        injector.inject(text, is_final=is_final)

    # SCENARIO: S1 starts, then S2 starts, then S1 returns mid-turn.

    # 1. S1 starts talking (Partial)
    process_update([], "Hello", is_final=False)

    # 2. S1 continues (Partial)
    process_update([], "Hello world", is_final=False)

    # 3. S1 finalized (Turn 1)
    # Architecture: format_final_turn sees has_sent_any_text is false, no leading \n
    process_update(
        [{"text": "Hello", "speaker": "A"}, {"text": "world", "speaker": "A"}],
        "Hello world",
        is_final=True,
    )

    # 4. S2 starts (Partial)
    # Injector last_text is "", so it types "How"
    process_update([], "How", is_final=False)

    # 5. S2 finalized (Turn 2)
    # Architecture: format_final_turn sees speaker S2 != S1, has_sent_any_text is true, prepends \n
    # result: "\n[S2] How are you?"
    # Injector: diffs "How" against "\n[S2] How are you?". Backspaces 3, types "\n[S2] How are you?"
    process_update(
        [
            {"text": "How", "speaker": "B"},
            {"text": "are", "speaker": "B"},
            {"text": "you", "speaker": "B"},
        ],
        "How are you",
        is_final=True,
    )

    # 6. S1 starts (Partial)
    process_update([], "I", is_final=False)

    # 7. S1 returns mid-turn (Final)
    # Final turn data: [{"text": "I", "speaker": "A"}, {"text": "agree", "speaker": "A"}]
    # result: "\n[S1] I agree"
    # Injector: diffs "I" against "\n[S1] I agree". Backspaces 1, types "\n[S1] I agree"
    process_update(
        [{"text": "I", "speaker": "A"}, {"text": "agree", "speaker": "A"}], "I agree", is_final=True
    )


if __name__ == "__main__":
    debug_session()
