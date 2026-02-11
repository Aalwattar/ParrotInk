from enum import Enum
from typing import Literal


class AppState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    ERROR = "error"


ProviderType = Literal["openai", "assemblyai"]
