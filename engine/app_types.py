from dataclasses import dataclass
from enum import Enum
from typing import List, Literal, Optional


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


@dataclass(frozen=True)
class EffectiveOpenAIConfig:
    url: str
    transcription_model: str
    prompt: str
    turn_detection_type: str
    vad_threshold: float
    silence_duration_ms: int
    prefix_padding_ms: int
    noise_reduction_type: Optional[str]
    language: str
    stop_timeout: float
    is_test: bool


@dataclass(frozen=True)
class EffectiveAssemblyAIConfig:
    url: str
    sample_rate: int
    encoding: str
    speech_model: str
    language_code: str
    vad_threshold: float
    confidence_threshold: float
    min_silence_ms: int
    max_silence_ms: int
    inactivity_timeout: Optional[int]
    word_boost: Optional[List[str]]
    format_text: bool
    language_detection: bool
    stop_timeout: float
    is_test: bool


@dataclass(frozen=True)
class EffectiveConfig:
    provider_type: ProviderType
    capture_sample_rate: int
    chunk_ms: int
    hotkey: str
    hold_mode: bool
    openai: EffectiveOpenAIConfig
    assemblyai: EffectiveAssemblyAIConfig
