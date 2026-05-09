from typing import Any, Dict, List, Optional


class SpeakerManager:
    """Manages speaker labels for streaming transcription."""

    def __init__(self):
        self.active_speaker: Optional[str] = None
        self.has_sent_any_text: bool = False
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
        self.session_speaker = None

    def format_with_speaker(self, words: List[Dict[str, Any]], transcript: str) -> str:
        if not words:
            return transcript

        result_parts = []
        current_running_speaker = self.session_speaker

        for i, word_data in enumerate(words):
            raw_speaker = word_data.get("speaker")
            cleaned_label = self._clean_label(raw_speaker)
            word_text = word_data.get("text", "")

            is_turn_start = i == 0 and current_running_speaker is None
            is_mid_segment_change = cleaned_label and cleaned_label != current_running_speaker

            if cleaned_label and (is_turn_start or is_mid_segment_change):
                # Use standard Windows CRLF directly in the text stream
                if self.has_sent_any_text:
                    result_parts.append("\r\n")

                result_parts.append(f"[{cleaned_label}] ")
                current_running_speaker = cleaned_label
                self.session_speaker = cleaned_label
                self.has_sent_any_text = True

            result_parts.append(word_text)

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
            self.active_speaker = cleaned
            self.session_speaker = cleaned
            self.has_sent_any_text = True
