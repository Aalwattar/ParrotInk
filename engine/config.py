import re
import tomllib
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import AliasChoices, BaseModel, Field, ValidationError

from .logging import get_logger
from .platform_win.paths import get_config_path
from .security import SecurityManager

logger = get_logger("Config")


def migrate_config_file(path: Path | str):
    """
    Automatically migrates config file values to current best practices.
    - Standardizes capture_sample_rate to 16000.
    - Standardizes OpenAI input_audio_rate to 24000.
    """
    path = Path(path)
    if not path.exists():
        return

    try:
        content = path.read_text(encoding="utf-8")

        # 1. capture_sample_rate -> 16000 (standard efficiency)
        new_content = re.sub(r"(\bcapture_sample_rate\s*=\s*)24000\b", r"\g<1>16000", content)

        # 2. transcription.sample_rate -> 16000
        new_content = re.sub(r"(\bsample_rate\s*=\s*)24000\b", r"\g<1>16000", new_content)

        # 3. providers.openai.core.input_audio_rate -> 24000 (OpenAI Realtime requirement)
        new_content = re.sub(r"(\binput_audio_rate\s*=\s*)16000\b", r"\g<1>24000", new_content)

        if new_content != content:
            path.write_text(new_content, encoding="utf-8")
            print(
                f"Migrated {path} to standardized sample rates (16kHz capture, 24kHz OpenAI input)."
            )
    except Exception as e:
        print(f"Warning: Failed to migrate config file {path}: {e}")


class HotkeysConfig(BaseModel):
    hotkey: str = "ctrl+alt+v"
    hold_mode: bool = False


class SoundsConfig(BaseModel):
    enabled: bool = True
    volume: float = 0.5
    start_sound_path: str = r"C:\Windows\Media\Speech On.wav"
    stop_sound_path: str = r"C:\Windows\Media\Speech Off.wav"


class FloatingIndicatorConfig(BaseModel):
    enabled: bool = True
    opacity_idle: float = 0.3
    opacity_active: float = 0.8
    y_offset: int = 60
    max_characters: int = 180
    refresh_rate_ms: int = 50


class InteractionConfig(BaseModel):
    # From cancel_click_away_20260210
    cancel_on_click_outside_anchor: bool = True
    anchor_scope: Literal["control", "window"] = "control"

    # From auditory_feedback_20260210
    sounds: SoundsConfig = Field(default_factory=SoundsConfig)


class AudioConfig(BaseModel):
    capture_sample_rate: int = 16000
    chunk_ms: int = 100
    connection_mode: Literal["on_demand", "warm", "always_on"] = "warm"
    warm_idle_timeout_seconds: int = Field(default=300, ge=30, le=1800)
    connection_timeout_seconds: float = 10.0
    voice_activity_threshold: float = 0.005


class TranscriptionConfig(BaseModel):
    language: str = "en"
    sample_rate: int = 16000


class AppTestConfig(BaseModel):
    enabled: bool = False
    openai_mock_url: str = "ws://localhost:8081"
    assemblyai_mock_url: str = "ws://localhost:8081"


class LoggingConfig(BaseModel):
    file_enabled: bool = False
    file_path: Optional[str] = None
    file_level: int = 1


# --- OpenAI Configuration ---


class OpenAICoreConfig(BaseModel):
    realtime_ws_url_base: str = "wss://api.openai.com/v1/realtime"
    model: str = "gpt-4o-mini-transcribe"  # Default transcription model
    language: str = "en"
    prompt: str = ""
    input_audio_type: str = "audio/pcm16"
    input_audio_rate: int = 24000
    session_rotation_seconds: int = 3300  # 55 minutes


class OpenAIAdvancedConfig(BaseModel):
    noise_reduction: str = "off"
    turn_detection_type: str = "server_vad"
    vad_threshold: float = 0.5
    prefix_padding_ms: int = 300
    silence_duration_ms: int = 350  # Reduced from 500
    include_logprobs: bool = False


class OpenAIConfig(BaseModel):
    core: OpenAICoreConfig = Field(
        default_factory=OpenAICoreConfig, validation_alias=AliasChoices("core", "tier1")
    )
    advanced: OpenAIAdvancedConfig = Field(
        default_factory=OpenAIAdvancedConfig, validation_alias=AliasChoices("advanced", "tier2")
    )


# --- AssemblyAI Configuration ---


class AssemblyAICoreConfig(BaseModel):
    ws_url: str = "wss://streaming.assemblyai.com/v3/ws"
    sample_rate: int = 16000
    vad_threshold: float = 0.4
    encoding: str = "pcm_s16le"
    speech_model: str = "universal-streaming-english"
    keyterms_prompt: List[str] = Field(default_factory=list)
    inactivity_timeout_seconds: int = 0


class AssemblyAIAdvancedConfig(BaseModel):
    end_of_turn_confidence_threshold: float = 0.4
    min_end_of_turn_silence_when_confident_ms: int = 400  # Default 400
    max_turn_silence_ms: int = 1000  # Default 1280
    utterance_silence_threshold_ms: int = 700
    format_turns: bool = False
    language_detection: bool = False


class AssemblyAIConfig(BaseModel):
    core: AssemblyAICoreConfig = Field(
        default_factory=AssemblyAICoreConfig, validation_alias=AliasChoices("core", "tier1")
    )
    advanced: AssemblyAIAdvancedConfig = Field(
        default_factory=AssemblyAIAdvancedConfig, validation_alias=AliasChoices("advanced", "tier2")
    )


class ProvidersConfig(BaseModel):
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    assemblyai: AssemblyAIConfig = Field(default_factory=AssemblyAIConfig)


class UIConfig(BaseModel):
    floating_indicator: FloatingIndicatorConfig = Field(default_factory=FloatingIndicatorConfig)


class Config(BaseModel):
    default_provider: Literal["openai", "assemblyai"] = Field(
        default="openai", validation_alias=AliasChoices("default_provider", "active_provider")
    )
    hotkeys: HotkeysConfig = Field(default_factory=HotkeysConfig)
    interaction: InteractionConfig = Field(default_factory=InteractionConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    transcription: TranscriptionConfig = Field(default_factory=TranscriptionConfig)
    test: AppTestConfig = Field(default_factory=AppTestConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)

    def get_openai_key(self) -> Optional[str]:
        """Resolves OpenAI API key."""
        return SecurityManager.get_key("openai_api_key")

    def get_assemblyai_key(self) -> Optional[str]:
        """Resolves AssemblyAI API key."""
        return SecurityManager.get_key("assemblyai_api_key")

    def save(self, path: Optional[Path | str] = None):
        """Saves the current configuration to a TOML file."""
        import tomli_w

        if path is None:
            path = get_config_path()
        path = Path(path)
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # We convert to dict, but Pydantic's model_dump is better
        # Use exclude_none=True to avoid issues with tomli_w and NoneType
        data = self.model_dump(exclude_none=True)

        try:
            content = tomli_w.dumps(data)
            path.write_text(content, encoding="utf-8")
            logger.debug(f"Configuration saved to {path}")
        except Exception as e:
            print(f"Error saving config: {e}")

    @classmethod
    def from_file(cls, path: Path | str) -> "Config":
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
            return cls(**data)
        except FileNotFoundError:
            # If config doesn't exist, we return a default config
            return cls()
        except tomllib.TOMLDecodeError as e:
            raise ConfigError(f"Invalid TOML format in {path}: {e}") from e
        except ValidationError as e:
            # Format pydantic validation errors into a more readable summary
            error_messages = []
            for error in e.errors():
                loc = ".".join(str(item) for item in error["loc"])
                msg = error["msg"]
                error_messages.append(f"{loc}: {msg}")
            error_summary = "\n".join(error_messages)
            raise ConfigError(f"Configuration validation failed:\n{error_summary}") from e
        except Exception as e:
            raise ConfigError(f"An unexpected error occurred while loading config: {e}") from e


def load_config(path: Optional[str | Path] = None) -> Config:
    """Helper function to load the configuration from a file."""
    if path is None:
        path = get_config_path()
    migrate_config_file(path)
    return Config.from_file(path)


class ConfigError(Exception):
    """Raised when there is an error in the configuration."""

    pass
