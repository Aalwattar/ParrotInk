from enum import Enum
from typing import Literal


class AppState(Enum):
    IDLE = "idle"
    CONNECTING = "connecting"
    LISTENING = "listening"
    STOPPING = "stopping"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"


class CaptureFormatError(Exception):
    """Raised when audio capture data violates expected dimensionality or types."""


ProviderType = Literal["openai", "assemblyai"]
