import tomllib
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field, ValidationError
from .security import SecurityManager


class HotkeysConfig(BaseModel):
    hotkey: str = "ctrl+alt+v"
    hold_mode: bool = True


class TranscriptionConfig(BaseModel):
    language: str = "en"
    sample_rate: int = 16000


class TestConfig(BaseModel):
    enabled: bool = False
    openai_mock_url: str = "ws://localhost:8081"
    assemblyai_mock_url: str = "ws://localhost:8081"


class AdvancedConfig(BaseModel):
    openai_url: str = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
    assemblyai_url: str = "wss://api.assemblyai.com/v2/realtime/ws"


class Config(BaseModel):
    active_provider: Literal["openai", "assemblyai"] = "openai"
    hotkeys: HotkeysConfig = Field(default_factory=HotkeysConfig)
    transcription: TranscriptionConfig = Field(default_factory=TranscriptionConfig)
    test: TestConfig = Field(default_factory=TestConfig)
    advanced: AdvancedConfig = Field(default_factory=AdvancedConfig)

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
            # instead of crashing, as keys are now elsewhere.
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
    return Config.from_file(path)


class ConfigError(Exception):
    """Raised when there is an error in the configuration."""

    pass