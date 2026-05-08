from typing import Any, Dict, List, Optional


class SpeakerManager:
    """Manages speaker labels for streaming transcription."""

    def __init__(self):
        # We track the 'active' speaker of the PREVIOUS segment to decide if we need a label change.
        self.active_speaker: Optional[str] = None

    def _clean_label(self, raw_speaker: Any) -> Optional[str]:
        """
        Sanitizes speaker labels.
        - UNKNOWN or None -> None
        - 'A', 'B', 'C' -> 'S1', 'S2', 'S3'
        - '1', 1 -> 'S1'
        """
        if raw_speaker is None:
            return None

        s = str(raw_speaker).upper()
        if s == "UNKNOWN":
            return None

        # Fix Review Recommendation: Normalize numeric labels
        if s.isdigit():
            return f"S{s}"

        if s.startswith("S") and s[1:].isdigit():
            return s

        if len(s) == 1 and "A" <= s <= "Z":
            # Map A->1, B->2, etc.
            num = ord(s) - ord("A") + 1
            return f"S{num}"

        return s

    def format_with_speaker(self, words: List[Dict[str, Any]], transcript: str) -> str:
        """
        Prepends speaker labels to the transcript.
        Iterates through words to detect mid-segment speaker changes.

        CRITICAL: This must return a string that is CONSISTENT for the SmartInjector.

        If we send '[S1] Hello' then 'Hello How', the SmartInjector will backspace the label.
        Therefore, we must rebuild the string assuming it's a fresh turn, but using
        the speaker state from the previous turn to decide where to insert newlines.
        """
        if not words:
            return transcript

        result_parts = []
        # Local tracker for the current segment building loop
        current_segment_speaker = self.active_speaker

        for i, word_data in enumerate(words):
            raw_speaker = word_data.get("speaker")
            cleaned_label = self._clean_label(raw_speaker)
            word_text = word_data.get("text", "")

            if cleaned_label and cleaned_label != current_segment_speaker:
                # Speaker change detected
                if current_segment_speaker is not None:
                    # Not the very first speaker of the entire session
                    result_parts.append("\n")

                result_parts.append(f"[{cleaned_label}] ")
                current_segment_speaker = cleaned_label

            result_parts.append(word_text)

            # Add space if not the last word AND the next word doesn't cause a speaker change
            if i < len(words) - 1:
                next_raw = words[i + 1].get("speaker")
                next_cleaned = self._clean_label(next_raw)
                if next_cleaned is None or next_cleaned == current_segment_speaker:
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
