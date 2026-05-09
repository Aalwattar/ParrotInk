from typing import Any, Dict, List, Optional


class SpeakerManager:
    """Manages speaker labels for streaming transcription."""

    def __init__(self):
        # active_speaker tracks the speaker across multiple turns (hotkey presses)
        self.active_speaker: Optional[str] = None
        # session_speaker tracks the speaker within the CURRENT active turn
        self.session_speaker: Optional[str] = None

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
            num = ord(s) - ord("A") + 1
            return f"S{num}"

        return s

    def reset_session(self):
        """Called when a new transcription turn starts (hotkey press)."""
        self.session_speaker = None

    def format_with_speaker(self, words: List[Dict[str, Any]], transcript: str) -> str:
        """
        Formats the transcript with speaker labels and newlines.
        Only adds a label if the speaker changes or it's the start of a turn.
        """
        if not words:
            return transcript

        result_parts = []
        # tracker for the current segment building loop
        # For the START of the turn, we use session_speaker (which is None)
        current_running_speaker = self.session_speaker

        for i, word_data in enumerate(words):
            raw_speaker = word_data.get("speaker")
            cleaned_label = self._clean_label(raw_speaker)
            word_text = word_data.get("text", "")

            # Trigger label if:
            # 1. It's the first word of the turn (current_running_speaker is None)
            # 2. The speaker changed mid-turn (cleaned_label != current_running_speaker)
            is_start_of_session = i == 0 and current_running_speaker is None
            is_speaker_change = cleaned_label and cleaned_label != current_running_speaker

            if cleaned_label and (is_start_of_session or is_speaker_change):
                # Add newline if:
                # - It's a mid-turn change (i > 0)
                # - OR it's a new turn (i == 0) and we've talked before (active_speaker is not None)
                if self.active_speaker is not None or i > 0:
                    result_parts.append("\r\n")

                result_parts.append(f"[{cleaned_label}] ")
                current_running_speaker = cleaned_label

            result_parts.append(word_text)

            # Standard space handling
            if i < len(words) - 1:
                next_cleaned = self._clean_label(words[i + 1].get("speaker"))
                if next_cleaned is None or next_cleaned == current_running_speaker:
                    result_parts.append(" ")

        return "".join(result_parts)

    def commit_speaker(self, words: List[Dict[str, Any]]):
        """Commits the final speaker of a segment to permanent state."""
        if not words:
            return
        last_word = words[-1]
        raw_speaker = last_word.get("speaker")
        cleaned = self._clean_label(raw_speaker)
        if cleaned:
            self.active_speaker = cleaned
            # Update session speaker so partials in the NEXT turn don't re-label
            self.session_speaker = cleaned
