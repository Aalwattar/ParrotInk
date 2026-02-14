import re
import tomllib
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    ValidationError,
    field_validator,
)

from .logging import get_logger
from .platform_win.paths import get_config_path
from .security import SecurityManager

logger = get_logger("Config")

# --- Profile Mappings ---

LATENCY_PROFILES = {
    "fast": {
        "openai": {"vad_threshold": 0.55, "silence_duration_ms": 300},
        "assemblyai": {
            "end_of_turn_confidence_threshold": 0.35,
            "min_end_of_turn_silence_when_confident_ms": 300,
            "max_turn_silence_ms": 800,
        },
    },
    "balanced": {
        "openai": {"vad_threshold": 0.60, "silence_duration_ms": 500},
        "assemblyai": {
            "end_of_turn_confidence_threshold": 0.4,
            "min_end_of_turn_silence_when_confident_ms": 400,
            "max_turn_silence_ms": 1000,
        },
    },
    "accurate": {
        "openai": {"vad_threshold": 0.65, "silence_duration_ms": 800},
        "assemblyai": {
            "end_of_turn_confidence_threshold": 0.5,
            "min_end_of_turn_silence_when_confident_ms": 600,
            "max_turn_silence_ms": 1500,
        },
    },
}

MIC_PROFILES = {
    "headset": "near_field",
    "laptop": "far_field",
    "none": None,
}


def migrate_config_file(path: Path | str):
    """
    Automatically migrates config file values to current best practices.
    """
    path = Path(path)
    if not path.exists():
        return

    try:
        content = path.read_text(encoding="utf-8")
        new_content = content

        # 1. capture_sample_rate -> 16000 (standard efficiency)
        new_content = re.sub(r"(\bcapture_sample_rate\s*=\s*)24000\b", r"\g<1>16000", new_content)

        # 2. providers.openai.core.input_audio_rate -> 24000 (OpenAI Realtime requirement)
        new_content = re.sub(r"(\binput_audio_rate\s*=\s*)16000\b", r"\g<1>24000", new_content)

        # 3. Handle default_provider/active_provider migration if not in transcription
        for legacy_key in ["default_provider", "active_provider"]:
            if legacy_key in new_content and "[transcription]" in new_content:
                if "provider =" not in new_content.split("[transcription]")[1].split("[")[0]:
                    match = re.search(rf'{legacy_key}\s*=\s*"([^"]+)"', new_content)
                    if match:
                        provider = match.group(1)
                        new_content = new_content.replace(
                            "[transcription]", f'[transcription]\nprovider = "{provider}"'
                        )
                        new_content = re.sub(rf'{legacy_key}\s*=\s*"[^"]+"\s*', "", new_content)

        # 4. REMOVE OBSOLETE KEYS (since extra='forbid' is active)
        obsolete_keys = [
            r"active_provider\s*=\s*\"[^\"]*\"",
            r"default_provider\s*=\s*\"[^\"]*\"",
            r"sample_rate\s*=\s*\d+",
            r"language\s*=\s*\"[^\"]*\"",
            r"model\s*=\s*\"[^\"]*\"",
            r"utterance_silence_threshold_ms\s*=\s*\d+",
            r"format_turns\s*=\s*(true|false)",
        ]

        for key_pattern in obsolete_keys:
            new_content = re.sub(rf"\b{key_pattern}\b", "", new_content)

        if new_content != content:
            path.write_text(new_content, encoding="utf-8")
            logger.info(f"Migrated {path} to new configuration schema (removed obsolete keys).")
    except Exception as e:
        logger.warning(f"Failed to migrate config file {path}: {e}")


class HotkeysConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hotkey: str = "ctrl+alt+v"
    hold_mode: bool = False


class SoundsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    volume: float = Field(default=0.5, ge=0.0, le=1.0)
    start_sound_path: str = r"C:\Windows\Media\Speech On.wav"
    stop_sound_path: str = r"C:\Windows\Media\Speech Off.wav"


class FloatingIndicatorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = False
    opacity_idle: float = 0.3
    opacity_active: float = 0.8
    y_offset: int = 60
    max_characters: int = 180
    refresh_rate_ms: int = 50


class InteractionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # From cancel_click_away_20260210
    cancel_on_click_outside_anchor: bool = True
    anchor_scope: Literal["control", "window"] = "control"

    # From auditory_feedback_20260210
    sounds: SoundsConfig = Field(default_factory=SoundsConfig)


class AudioConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    capture_sample_rate: int = 16000
    chunk_ms: int = 100
    connection_mode: Literal["on_demand", "warm", "always_on"] = "warm"
    warm_idle_timeout_seconds: int = Field(default=300, ge=30, le=1800)
    connection_timeout_seconds: float = 10.0
    voice_activity_threshold: float = 0.005


class TranscriptionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Literal["openai", "assemblyai"] = Field(
        default="openai", validation_alias=AliasChoices("provider", "active_provider")
    )
    language: str = "en"
    latency_profile: Literal["fast", "balanced", "accurate"] = "balanced"
    mic_profile: Literal["headset", "laptop", "none"] = "headset"
    format_text: bool = False


class AppTestConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = False
    openai_mock_url: str = "ws://localhost:8081"
    assemblyai_mock_url: str = "ws://localhost:8081"


class LoggingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file_enabled: bool = False
    file_path: Optional[str] = None
    file_level: int = 1


# --- OpenAI Configuration ---


class OpenAICoreConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    realtime_ws_url_base: str = "wss://api.openai.com/v1/realtime"
    realtime_model: str = "gpt-4o-realtime-preview"  # Model for transport URL
    transcription_model: str = "gpt-4o-mini-transcribe"  # Model for ASR logic
    prompt: str = ""
    input_audio_type: str = "audio/pcm16"
    input_audio_rate: int = 24000
    session_rotation_seconds: int = 3300  # 55 minutes


class OpenAIAdvancedConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    override: bool = False
    noise_reduction: str = "off"
    turn_detection_type: str = "server_vad"
    vad_threshold: float = 0.5
    prefix_padding_ms: int = 300
    silence_duration_ms: int = 350  # Reduced from 500
    include_logprobs: bool = False


class OpenAIConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    core: OpenAICoreConfig = Field(
        default_factory=OpenAICoreConfig, validation_alias=AliasChoices("core", "tier1")
    )
    advanced: OpenAIAdvancedConfig = Field(
        default_factory=OpenAIAdvancedConfig, validation_alias=AliasChoices("advanced", "tier2")
    )


# --- AssemblyAI Configuration ---


class AssemblyAICoreConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ws_url: str = "wss://streaming.assemblyai.com/v3/ws"
    region: Literal["us", "eu"] = "us"
    sample_rate: int = 16000
    vad_threshold: float = 0.4
    encoding: str = "pcm_s16le"
    speech_model: str = "universal-streaming-english"
    keyterms_prompt: List[str] = Field(default_factory=list)
    inactivity_timeout_seconds: int = 0

    @field_validator("inactivity_timeout_seconds")
    @classmethod
    def check_inactivity_timeout(cls, v):
        if v != 0 and (v < 5 or v > 3600):
            raise ValueError("Inactivity timeout must be 0 or between 5 and 3600 seconds")
        return v


class AssemblyAIAdvancedConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    override: bool = False
    end_of_turn_confidence_threshold: float = 0.4
    min_end_of_turn_silence_when_confident_ms: int = 400  # Default 400
    max_turn_silence_ms: int = 1000  # Default 1280
    language_detection: bool = False


class AssemblyAIConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    core: AssemblyAICoreConfig = Field(
        default_factory=AssemblyAICoreConfig, validation_alias=AliasChoices("core", "tier1")
    )
    advanced: AssemblyAIAdvancedConfig = Field(
        default_factory=AssemblyAIAdvancedConfig, validation_alias=AliasChoices("advanced", "tier2")
    )


class ProvidersConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    assemblyai: AssemblyAIConfig = Field(default_factory=AssemblyAIConfig)


class UIConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    floating_indicator: FloatingIndicatorConfig = Field(default_factory=FloatingIndicatorConfig)


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hotkeys: HotkeysConfig = Field(default_factory=HotkeysConfig)
    interaction: InteractionConfig = Field(default_factory=InteractionConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    transcription: TranscriptionConfig = Field(default_factory=TranscriptionConfig)
    test: AppTestConfig = Field(default_factory=AppTestConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)

    # Private list of observers (not serialized)
    _observers: List = PrivateAttr(default_factory=list)

    def register_observer(self, callback):
        """Registers a callback to be notified on config changes."""
        if callback not in self._observers:
            self._observers.append(callback)

    def _notify_observers(self):
        """Notifies all registered observers of a change."""
        for callback in self._observers:
            try:
                callback(self)
            except Exception as e:
                logger.error(f"Error notifying config observer: {e}")

    def update_and_save(self, updates: dict, path: Optional[Path | str] = None):
        """
        Performs a deep merge of updates into the current config,
        saves to disk, and notifies observers.
        """

        def deep_merge(target, source):
            for key, value in source.items():
                if isinstance(value, dict) and hasattr(target, key):
                    deep_merge(getattr(target, key), value)
                else:
                    setattr(target, key, value)

        deep_merge(self, updates)
        self.save(path)
        self._notify_observers()

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

    config_path = Path(path)
    if not config_path.exists():
        logger.info(f"No config found at {path}. Creating default config.")
        config = Config()
        config.save(path)
        return config

    return Config.from_file(path)


def explain_config(config: Config, verbose: int = 0):
    """Prints a diagnostic report of the resolved configuration."""
    import json

    print("\n--- Voice2Text Configuration Report ---")
    print(f"Active Provider: {config.transcription.provider}")
    print(f"Language:        {config.transcription.language}")
    print(f"Latency Profile: {config.transcription.latency_profile}")
    print(f"Mic Profile:     {config.transcription.mic_profile}")
    print(f"Hotkey:          {config.hotkeys.hotkey} (hold_mode={config.hotkeys.hold_mode})")
    print(f"Audio Capture:   {config.audio.capture_sample_rate}Hz")

    # Explain Latency Mapping
    profile = LATENCY_PROFILES.get(
        config.transcription.latency_profile, LATENCY_PROFILES["balanced"]
    )
    print(f"\n[Profile: {config.transcription.latency_profile}] Resolved Engineering Values:")

    print("  OpenAI:")
    print(f"    - vad_threshold:      {profile['openai']['vad_threshold']}")
    print(f"    - silence_duration_ms: {profile['openai']['silence_duration_ms']}")

    print("  AssemblyAI:")
    print(
        f"    - confidence_threshold: {profile['assemblyai']['end_of_turn_confidence_threshold']}"
    )
    print(
        f"    - min_silence_ms:       "
        f"{profile['assemblyai']['min_end_of_turn_silence_when_confident_ms']}"
    )
    print(f"    - max_silence_ms:       {profile['assemblyai']['max_turn_silence_ms']}")

    # Security Check
    print("\n[Credentials Status]")
    openai_key = config.get_openai_key()
    aai_key = config.get_assemblyai_key()
    print(f"  OpenAI API Key:     {'[SET]' if openai_key else '[MISSING]'}")
    print(f"  AssemblyAI API Key: {'[SET]' if aai_key else '[MISSING]'}")

    if verbose > 0:
        print("\n[Full Schema (Redacted)]")
        # Mask keys in the dump (though they aren't in the Config model itself)
        data = config.model_dump(exclude_none=True)
        print(json.dumps(data, indent=2))


class ConfigError(Exception):
    """Raised when there is an error in the configuration."""

    pass
