from typing import Any, Dict, List, Optional


class SpeakerManager:
    """Manages speaker labels for streaming transcription."""

    def __init__(self):
        self.current_speaker: Optional[int] = None

    def format_with_speaker(self, words: List[Dict[str, Any]], transcript: str) -> str:
        """
        Prepends speaker label to the transcript if available.
        Uses the speaker label from the first word of the segment.
        """
        if not words:
            return transcript

        # AssemblyAI Major Upgrade: each word has its own speaker label.
        # We take the speaker from the first word of the segment.
        speaker = words[0].get("speaker")
        if speaker is None:
            return transcript

        self.current_speaker = speaker
        return f"[S{speaker}] {transcript}"
