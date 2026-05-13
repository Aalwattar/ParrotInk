from typing import Any, Dict, List, Optional


class SpeakerManager:
    """
    Manages speaker labels for streaming transcription using Turn-Based Isolation.
    """

    def __init__(self):
        # We only track who is currently talking on the screen.
        self.current_speaker_on_screen: Optional[str] = None
        # tracks if the very first character of the session has been sent.
        self.has_sent_any_text: bool = False

    def reset_session(self):
        """Called when a new transcription session starts (e.g. app start)."""
        self.current_speaker_on_screen = None
        self.has_sent_any_text = False

    def _clean_label(self, raw_speaker: Any) -> Optional[str]:
        """Sanitizes speaker labels to S1, S2, etc."""
        if raw_speaker is None:
            return None

        s = str(raw_speaker).upper()

        if s == "UNKNOWN":
            return None

        if s.isdigit():
            return f"S{s}"

        if s.startswith("S") and s[1:].isdigit():
            return s

        if len(s) == 1 and "A" <= s <= "Z":
            return f"S{ord(s) - ord('A') + 1}"

        return s

    def _resolve_speaker(self, word: Dict[str, Any], turn_speaker: Any) -> Optional[str]:
        """Resolves speaker from word-level data or turn-level fallback."""
        word_speaker = self._clean_label(word.get("speaker"))
        if word_speaker:
            return word_speaker

        turn_label = self._clean_label(turn_speaker)
        if turn_label:
            return turn_label

        return self.current_speaker_on_screen

    def format_final_turn(
        self, transcript: str, words: List[Dict[str, Any]], turn_speaker: Any = None
    ) -> str:
        """
        Formats a final transcription turn with speaker labels and newlines.
        This method is deterministic and intended for append-only final injection.
        """
        transcript = (transcript or "").strip()
        if not transcript:
            return ""

        if not words:
            # Fallback for when word-level diarization is missing or delayed
            return self._format_segment(
                speaker=self._clean_label(turn_speaker),
                text=transcript,
                is_start_of_turn=True,
            )

        output = []
        current_speaker = None
        current_words: List[str] = []
        is_first_segment = True

        def flush():
            nonlocal current_words, current_speaker, is_first_segment
            if not current_words:
                return

            text = " ".join(current_words).strip()
            if text:
                output.append(
                    self._format_segment(current_speaker, text, is_start_of_turn=is_first_segment)
                )
                is_first_segment = False

            current_words = []

        for word in words:
            word_text = (word.get("text") or "").strip()
            if not word_text:
                continue

            speaker = self._resolve_speaker(word, turn_speaker)

            if current_speaker is None:
                current_speaker = speaker

            # If speaker changes mid-turn
            if speaker and current_speaker and speaker != current_speaker:
                flush()
                current_speaker = speaker

            current_words.append(word_text)

        flush()
        return "".join(output)

    def _format_segment(
        self, speaker: Optional[str], text: str, is_start_of_turn: bool = False
    ) -> str:
        """Helper to format a single speaker block."""
        if not text:
            return ""

        parts = []

        # ARCHITECTURAL RULE: Every new turn starts on a new line if text exists.
        # This prevents turns from being squashed together and ensures the 'Script' look.
        needs_newline = False
        if self.has_sent_any_text:
            if is_start_of_turn:
                needs_newline = True
            elif speaker and speaker != self.current_speaker_on_screen:
                needs_newline = True

        if needs_newline:
            parts.append("\n")

        # Add label if it's a new speaker OR the start of a new turn block.
        # We always label a new turn to maintain the visual script structure.
        if speaker and (is_start_of_turn or speaker != self.current_speaker_on_screen):
            parts.append(f"[{speaker}] ")
            self.current_speaker_on_screen = speaker

        parts.append(text)
        self.has_sent_any_text = True

        return "".join(parts)
