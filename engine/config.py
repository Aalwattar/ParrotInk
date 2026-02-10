import tomllib
import re
from pathlib import Path
from typing import Literal, Optional, List, Union

from pydantic import AliasChoices, BaseModel, Field, ValidationError
from .security import SecurityManager


def migrate_config_file(path: Path | str):
    """
    Automatically migrates 16000 sample rates to 24000 in the config file
    while preserving comments.
    """
    path = Path(path)
    if not path.exists():
        return

    try:
        content = path.read_text(encoding="utf-8")
        # Replace sample rates specifically in keys that likely hold them
        # capture_sample_rate, sample_rate, input_audio_rate
        new_content = re.sub(r'(\bcapture_sample_rate\s*=\s*)16000\b', r'\g<1>24000', content)
        new_content = re.sub(r'(\bsample_rate\s*=\s*)16000\b', r'\g<1>24000', new_content)
        new_content = re.sub(r'(\binput_audio_rate\s*=\s*)16000\b', r'\g<1>24000', new_content)

        if new_content != content:
            path.write_text(new_content, encoding="utf-8")
            # We don't have a logger easily accessible here without circular imports
            # but we can print for visibility since this is a one-time migration.
            print(f"Migrated {path} from 16000Hz to 24000Hz.")
    except Exception as e:
        print(f"Warning: Failed to migrate config file {path}: {e}")


class HotkeysConfig(BaseModel):
    hotkey: str = "ctrl+alt+v"
    hold_mode: bool = True


class AudioConfig(BaseModel):
    capture_sample_rate: int = 24000
    chunk_ms: int = 100


class TranscriptionConfig(BaseModel):
    language: str = "en"
    sample_rate: int = 24000


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
    realtime_ws_model: str = "gpt-4o-realtime-preview-2024-10-01"
    transcription_model: str = "whisper-1"
    language: str = "en"
    prompt: str = ""
    input_audio_type: str = "audio/pcm16"
    input_audio_rate: int = 24000


class OpenAIAdvancedConfig(BaseModel):
    noise_reduction: str = "off"
    turn_detection_type: str = "server_vad"
    vad_threshold: float = 0.5
    prefix_padding_ms: int = 300
    silence_duration_ms: int = 500
    include_logprobs: bool = False


class OpenAIConfig(BaseModel):
    core: OpenAICoreConfig = Field(default_factory=OpenAICoreConfig, validation_alias=AliasChoices("core", "tier1"))
    advanced: OpenAIAdvancedConfig = Field(default_factory=OpenAIAdvancedConfig, validation_alias=AliasChoices("advanced", "tier2"))


# --- AssemblyAI Configuration ---

class AssemblyAICoreConfig(BaseModel):
    ws_url: str = "wss://streaming.assemblyai.com/v3/ws"
    sample_rate: int = 24000
    vad_threshold: float = 0.4
    encoding: str = "pcm_s16le"
    speech_model: str = "universal-streaming-english"
    keyterms_prompt: List[str] = Field(default_factory=list)
    inactivity_timeout_seconds: int = 0


class AssemblyAIAdvancedConfig(BaseModel):
    end_of_turn_confidence_threshold: float = 0.4
    min_end_of_turn_silence_when_confident_ms: int = 400
    max_turn_silence_ms: int = 1280
    format_turns: bool = False
    language_detection: bool = False


class AssemblyAIConfig(BaseModel):
    core: AssemblyAICoreConfig = Field(default_factory=AssemblyAICoreConfig, validation_alias=AliasChoices("core", "tier1"))
    advanced: AssemblyAIAdvancedConfig = Field(default_factory=AssemblyAIAdvancedConfig, validation_alias=AliasChoices("advanced", "tier2"))


class ProvidersConfig(BaseModel):
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    assemblyai: AssemblyAIConfig = Field(default_factory=AssemblyAIConfig)


class Config(BaseModel):
    default_provider: Literal["openai", "assemblyai"] = Field(
        default="openai", validation_alias=AliasChoices("default_provider", "active_provider")
    )
    hotkeys: HotkeysConfig = Field(default_factory=HotkeysConfig)
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


def load_config(path: str | Path = "config.toml") -> Config:
    """Helper function to load the configuration from a file."""
    migrate_config_file(path)
    return Config.from_file(path)


class ConfigError(Exception):
    """Raised when there is an error in the configuration."""

    pass
