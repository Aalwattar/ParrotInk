from enum import Enum
from typing import Literal


class AppState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    ERROR = "error"


class CaptureFormatError(Exception):
    """Raised when audio capture data violates expected dimensionality or types."""


ProviderType = Literal["openai", "assemblyai"]
