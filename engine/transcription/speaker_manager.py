from typing import Any, Dict, List, Optional


class SpeakerManager:
    """Manages speaker labels for streaming transcription."""

    def __init__(self):
        self.current_speaker: Optional[str] = None

    def _clean_label(self, raw_speaker: Any) -> Optional[str]:
        """
        Sanitizes speaker labels.
        - UNKNOWN or None -> None
        - 'A', 'B', 'C' -> 'S1', 'S2', 'S3'
        - int -> 'S{int}'
        """
        if raw_speaker is None:
            return None

        if isinstance(raw_speaker, str):
            upper_s = raw_speaker.upper()
            if upper_s == "UNKNOWN":
                return None
            if len(upper_s) == 1 and "A" <= upper_s <= "Z":
                # Map A->1, B->2, etc.
                num = ord(upper_s) - ord("A") + 1
                return f"S{num}"
            return upper_s

        if isinstance(raw_speaker, int):
            return f"S{raw_speaker}"

        return str(raw_speaker)

    def format_with_speaker(self, words: List[Dict[str, Any]], transcript: str) -> str:
        """
        Prepends speaker labels to the transcript.
        Iterates through words to detect mid-segment speaker changes.
        """
        if not words:
            return transcript

        result_parts = []

        for i, word_data in enumerate(words):
            raw_speaker = word_data.get("speaker")
            cleaned_label = self._clean_label(raw_speaker)
            word_text = word_data.get("text", "")

            if cleaned_label and cleaned_label != self.current_speaker:
                # Speaker change detected
                if self.current_speaker is not None:
                    # Not the very first word in the transcript
                    result_parts.append("\n")

                result_parts.append(f"[{cleaned_label}] ")
                self.current_speaker = cleaned_label

            result_parts.append(word_text)

            # Add space if not the last word AND the next word doesn't cause a speaker change
            if i < len(words) - 1:
                next_raw = words[i + 1].get("speaker")
                next_cleaned = self._clean_label(next_raw)

                # Only add space if next word has same speaker or speaker is suppressed/unknown
                if next_cleaned is None or next_cleaned == self.current_speaker:
                    result_parts.append(" ")

        return "".join(result_parts)
