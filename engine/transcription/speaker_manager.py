from typing import Any, Dict, List, Optional


class SpeakerManager:
    """Manages speaker labels for streaming transcription."""

    def __init__(self):
        # tracks the last speaker to decide if we need a label change.
        self.current_speaker_on_screen: Optional[str] = None
        # Tracks if ANY text (labeled or not) has been sent to the screen.
        self.has_sent_any_text: bool = False
        # tracks the speaker of the CURRENT turn
        self.session_speaker: Optional[str] = None

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
            if self.has_sent_any_text:
                result_parts.append("\n")  # Injector will convert this to VK_RETURN
            result_parts.append(f"[{first_word_speaker}] ")
            self.current_speaker_on_screen = first_word_speaker
            self.session_speaker = first_word_speaker

        # Process the rest of the words
        current_running_speaker = self.session_speaker

        for i, word_data in enumerate(words):
            raw_speaker = word_data.get("speaker")
            cleaned_label = self._clean_label(raw_speaker)
            word_text = word_data.get("text", "")

            # If speaker changes mid-segment
            if cleaned_label and cleaned_label != current_running_speaker:
                result_parts.append("\n")
                result_parts.append(f"[{cleaned_label}] ")
                current_running_speaker = cleaned_label
                self.current_speaker_on_screen = cleaned_label

            result_parts.append(word_text)

            # CRITICAL: We mark that text was sent, even if there was no label.
            self.has_sent_any_text = True

            # Add spaces between words
            if i < len(words) - 1:
                next_cleaned = self._clean_label(words[i + 1].get("speaker"))
                if next_cleaned is None or next_cleaned == current_running_speaker:
                    result_parts.append(" ")

        return "".join(result_parts)

    def commit_speaker(self, words: List[Dict[str, Any]]):
        if not words:
            return
        last_word = words[-1]
        raw_speaker = last_word.get("speaker")
        cleaned = self._clean_label(raw_speaker)
        if cleaned:
            self.current_speaker_on_screen = cleaned
            self.has_sent_any_text = True
