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

# CRITICAL: Do NOT change the default models or session schemas without extreme approval.
# The application uses specialized 'transcribe' models and nested transcription-only
# session objects that are distinct from standard Realtime API flows.
CORE_MODEL_INVARIANTS = {
    "openai": "gpt-4o-mini-transcribe",
    "assemblyai": "universal-streaming-english",
}

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
    enabled: bool = True
    click_through: bool = True
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

    # From run_at_startup_20260214
    run_at_startup: bool = False


class AudioConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    capture_sample_rate: int = 16000
    chunk_ms: int = 100
    connection_mode: Literal["on_demand", "warm", "always_on"] = "warm"
    warm_idle_timeout_seconds: int = Field(default=300, ge=30, le=1800)
    connection_timeout_seconds: float = 20.0
    voice_activity_threshold: float = 0.005


class TranscriptionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Literal["openai", "assemblyai"] = Field(
        default="openai", validation_alias=AliasChoices("provider", "active_provider")
    )
    latency_profile: Literal["fast", "balanced", "accurate"] = "balanced"
    mic_profile: Literal["headset", "laptop", "none"] = "headset"


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
    transcription_model: str = "gpt-4o-mini-transcribe"  # Model for ASR logic
    language: str = "en"
    session_rotation_seconds: int = 3300  # 55 minutes

    @field_validator("transcription_model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        if v.startswith("gpt-realtime"):
            raise ValueError(
                "Conversational models (gpt-realtime*) are not supported. "
                "Use transcription models like 'gpt-4o-mini-transcribe'."
            )
        return v


class OpenAIAdvancedConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    override: bool = False
    prompt: str = ""
    noise_reduction: str = "off"
    turn_detection_type: str = "server_vad"
    vad_threshold: float = 0.6
    prefix_padding_ms: int = 300
    silence_duration_ms: int = 500


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
    language_code: str = "en"
    vad_threshold: float = 0.4
    speech_model: str = "universal-streaming-english"
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
    format_text: bool = False
    keyterms_prompt: List[str] = Field(default_factory=list)
    end_of_turn_confidence_threshold: float = 0.4
    min_end_of_turn_silence_when_confident_ms: int = 400  # Default 400
    max_turn_silence_ms: int = 1000  # Default 1280
    language_detection: bool = False

    @field_validator("keyterms_prompt")
    @classmethod
    def validate_keyterms(cls, v: List[str]) -> List[str]:
        cleaned = [term.strip() for term in v if term.strip()]
        if len(cleaned) > 100:
            raise ValueError("keyterms_prompt cannot exceed 100 terms")
        for term in cleaned:
            if len(term) > 50:
                raise ValueError(f"Keyterm too long (>50 chars): {term[:10]}...")
        return cleaned


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

    def update_and_save(
        self, updates: dict, path: Optional[Path | str] = None, blocking: bool = False
    ):
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
        self.save(path, blocking=blocking)
        self._notify_observers()

    def get_openai_key(self) -> Optional[str]:
        """Resolves OpenAI API key."""
        return SecurityManager.get_key("openai_api_key")

    def get_assemblyai_key(self) -> Optional[str]:
        """Resolves AssemblyAI API key."""
        return SecurityManager.get_key("assemblyai_api_key")

    def save(self, path: Optional[Path | str] = None, blocking: bool = False):
        """
        Saves the current configuration to a TOML file atomically.
        Uses a temporary file and renames it to ensure the target file is never corrupt.
        """
        import os
        import threading

        import tomli_w

        if path is None:
            path = get_config_path()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = self.model_dump(exclude_none=True)

        def perform_write():
            temp_path = path.with_suffix(f"{path.suffix}.tmp")
            try:
                content = tomli_w.dumps(data)
                temp_path.write_text(content, encoding="utf-8")
                # Atomic swap on Windows
                os.replace(temp_path, path)
                logger.debug(f"Configuration saved to {path}")
            except Exception as e:
                logger.error(f"Error saving config: {e}")
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except Exception:
                        pass
                if blocking:
                    raise

        if blocking:
            perform_write()
        else:
            # Execute write in a daemon thread to avoid blocking the event loop
            threading.Thread(target=perform_write, daemon=True).start()

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

    from .config_resolver import resolve_effective_config

    eff = resolve_effective_config(config)

    print("\n--- Voice2Text Configuration Report ---")
    print(f"Active Provider: {eff.provider_type}")
    print(f"Hotkey:          {eff.hotkey} (hold_mode={eff.hold_mode})")
    print(f"Audio Capture:   {eff.capture_sample_rate}Hz")

    print(f"\n[Profile: {config.transcription.latency_profile}] Resolved Engineering Values:")

    if eff.provider_type == "openai":
        print("  OpenAI:")
        print(f"    - language:           {eff.openai.language}")
        print(f"    - url:                {eff.openai.url}")
        print(f"    - vad_threshold:      {eff.openai.vad_threshold}")
        print(f"    - silence_duration_ms: {eff.openai.silence_duration_ms}")
        print(f"    - noise_reduction:    {eff.openai.noise_reduction_type}")
        prompt_preview = (
            f'"{eff.openai.prompt[:20]}..."'
            if len(eff.openai.prompt) > 20
            else f'"{eff.openai.prompt}"'
        )
        print(f"    - prompt:             {prompt_preview} (len={len(eff.openai.prompt)})")
    else:
        print("  AssemblyAI:")
        print(f"    - url:                  {eff.assemblyai.url}")
        print(f"    - confidence_threshold: {eff.assemblyai.confidence_threshold}")
        print(f"    - min_silence_ms:       {eff.assemblyai.min_silence_ms}")
        print(f"    - max_silence_ms:       {eff.assemblyai.max_silence_ms}")
        print(f"    - inactivity_timeout:   {eff.assemblyai.inactivity_timeout}")
        kt = eff.assemblyai.word_boost
        kt_preview = f"{kt[:2]}..." if kt and len(kt) > 2 else f"{kt}"
        print(f"    - keyterms_prompt:      {kt_preview} (count={len(kt) if kt else 0})")

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
        # Redact potentially sensitive prompt info even in verbose dump
        if "providers" in data:
            if "openai" in data["providers"]:
                data["providers"]["openai"]["advanced"]["prompt"] = "[REDACTED]"
            if "assemblyai" in data["providers"]:
                data["providers"]["assemblyai"]["advanced"]["keyterms_prompt"] = ["[REDACTED]"]
        print(json.dumps(data, indent=2))


class ConfigError(Exception):
    """Raised when there is an error in the configuration."""

    pass
