from typing import Any, Dict, List, Optional


class SpeakerManager:
    """Manages speaker labels for streaming transcription."""

    def __init__(self):
        # We only track who is currently talking on the screen.
        self.current_speaker_on_screen: Optional[str] = None
        # tracks if the very first character of the session has been sent.
        self.is_first_injection: bool = True

    def _clean_label(self, raw_speaker: Any) -> Optional[str]:
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
            num = ord(s) - ord("A") + 1
            return f"S{num}"
        return s

    def reset_session(self):
        """No longer used. We persist speaker state across turns."""
        pass

    def format_with_speaker(self, words: List[Dict[str, Any]], transcript: str) -> str:
        """
        Groups words by speaker and prepends labels/newlines.
        """
        if not words:
            return transcript

        result_parts = []

        # We start by checking the very first word's speaker
        first_word_speaker = self._clean_label(words[0].get("speaker"))

        # If the first word's speaker is DIFFERENT than who is on screen,
        # we MUST insert a newline and the label.
        if first_word_speaker and first_word_speaker != self.current_speaker_on_screen:
            if not self.is_first_injection:
                result_parts.append("\r\n")
            result_parts.append(f"[{first_word_speaker}] ")
            self.current_speaker_on_screen = first_word_speaker
            self.is_first_injection = False

        # Process the rest of the words for mid-turn speaker changes (rare)
        current_running_speaker = self.current_speaker_on_screen

        for i, word_data in enumerate(words):
            raw_speaker = word_data.get("speaker")
            cleaned_label = self._clean_label(raw_speaker)
            word_text = word_data.get("text", "")

            # If speaker changes mid-segment
            if cleaned_label and cleaned_label != current_running_speaker:
                result_parts.append("\r\n")
                result_parts.append(f"[{cleaned_label}] ")
                current_running_speaker = cleaned_label
                self.current_speaker_on_screen = cleaned_label

            result_parts.append(word_text)

            # Add spaces between words
            if i < len(words) - 1:
                next_cleaned = self._clean_label(words[i + 1].get("speaker"))
                if next_cleaned is None or next_cleaned == current_running_speaker:
                    result_parts.append(" ")

        return "".join(result_parts)

    def commit_speaker(self, words: List[Dict[str, Any]]):
        """Commits the final speaker of a segment."""
        if not words:
            return
        last_word = words[-1]
        raw_speaker = last_word.get("speaker")
        cleaned = self._clean_label(raw_speaker)
        if cleaned:
            self.current_speaker_on_screen = cleaned
            self.is_first_injection = False
