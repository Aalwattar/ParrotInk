import os
import threading
from pathlib import Path
from typing import List, Literal, Optional

import tomlkit
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
    volume: int = Field(default=30, ge=0, le=100)  # Percent (0-100)
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
    cancel_on_click_outside_anchor: bool = True
    anchor_scope: Literal["control", "window"] = "control"
    stop_on_any_key: bool = True
    sounds: SoundsConfig = Field(default_factory=SoundsConfig)
    run_at_startup: bool = False


class AudioConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    capture_sample_rate: int = 16000
    chunk_ms: int = 100
    connection_mode: Literal["on_demand", "warm", "always_on"] = "warm"
    warm_idle_timeout_seconds: int = Field(default=300, ge=30, le=1800)
    inactivity_timeout_seconds: int = Field(default=30, ge=5, le=3600)
    connection_timeout_seconds: float = 20.0
    shutdown_timeout_seconds: float = 10.0
    provider_stop_timeout_seconds: float = 7.0
    voice_activity_threshold: float = 0.005
    max_retries: int = 3
    initial_backoff_seconds: float = 1.0
    max_backoff_seconds: float = 60.0


class TranscriptionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Literal["openai", "assemblyai"] = Field(
        default="openai", validation_alias=AliasChoices("provider", "active_provider")
    )
    latency_profile: Literal["fast", "balanced", "accurate"] = "balanced"
    mic_profile: Literal["headset", "laptop", "none"] = "none"
    partial_results: bool = False


class AppTestConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = False
    openai_mock_url: str = "ws://localhost:8081"
    assemblyai_mock_url: str = "ws://localhost:8081"


class LoggingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file_enabled: bool = True
    file_path: Optional[str] = None
    file_level: Literal["error", "info", "verbose"] = "error"
    file_max_bytes: int = Field(default=5242880, ge=1024)  # Default 5MB
    file_backup_count: int = Field(default=5, ge=0, le=50)


class OpenAICoreConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    realtime_ws_url_base: str = "wss://api.openai.com/v1/realtime"
    transcription_model: str = "gpt-4o-mini-transcribe"
    language: str = "en"
    session_rotation_seconds: int = 3300

    @field_validator("transcription_model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        if v.startswith("gpt-realtime"):
            raise ValueError("Conversational models not supported. Use 'gpt-4o-mini-transcribe'.")
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


class AssemblyAICoreConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ws_url: str = "wss://streaming.assemblyai.com/v3/ws"
    region: Literal["us", "eu"] = "us"
    language_code: str = "en"
    vad_threshold: float = 0.4
    speech_model: str = "u3-rt-pro"
    prompt: str = ""
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
    min_end_of_turn_silence_when_confident_ms: int = 400
    max_turn_silence_ms: int = 1000
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
    show_onboarding_popup: bool = True
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

    _observers: List = PrivateAttr(default_factory=list)
    _update_lock: threading.Lock = PrivateAttr(default_factory=threading.Lock)

    def register_observer(self, callback):
        if callback not in self._observers:
            self._observers.append(callback)

    def _notify_observers(self):
        for callback in self._observers:
            try:
                callback(self)
            except Exception as e:
                logger.error(f"Error notifying config observer: {e}")

    def update_and_save(
        self, updates: dict, path: Optional[Path | str] = None, blocking: bool = False
    ):
        """
        Atomically merges updates into the current configuration after validation.
        Ensures Pydantic validation is NOT bypassed during partial updates.
        """
        with self._update_lock:
            # 1. Start with current validated state as a dictionary
            # exclude_none=True ensures we don't accidentally overwrite with nulls
            data = self.model_dump(exclude_none=True)

            # 2. Senior Architecture: Merge updates into data dictionary
            # While Pydantic doesn't have a built-in 'deep merge' for dicts,
            # using model_validate(data) after merging is the Global optimization
            # to ensure the final result is 100% valid before application.
            def merge_dict(target, source):
                for k, v in source.items():
                    if isinstance(v, dict) and k in target and isinstance(target[k], dict):
                        merge_dict(target[k], v)
                    else:
                        target[k] = v

            merge_dict(data, updates)

            # 3. Validate entire merged configuration
            # This is the 'First Principle' check: never trust raw input.
            try:
                new_cfg = type(self).model_validate(data)
            except ValidationError as e:
                # Re-raise as ConfigError to prevent exposing internal Pydantic details
                raise ConfigError(f"Update validation failed: {e}") from e

            # 4. Apply validated values to self
            # We use model_fields to ensure we only set known attributes
            for field in type(self).model_fields:
                setattr(self, field, getattr(new_cfg, field))

        # 5. Save and Notify
        self.save(path, blocking=blocking)
        self._notify_observers()

    def get_openai_key(self) -> Optional[str]:
        return SecurityManager.get_key("openai_api_key")

    def get_assemblyai_key(self) -> Optional[str]:
        return SecurityManager.get_key("assemblyai_api_key")

    def reload(self, path: Optional[Path | str] = None):
        """
        Reloads the configuration from disk in-place.
        If the file is invalid, it raises ConfigError and preserves existing state.
        """
        if path is None:
            path = get_config_path()
        path = Path(path)

        # Load into a fresh instance first to validate
        new_cfg = self.from_file(path)

        # Apply updates in-place atomically
        with self._update_lock:
            # Senior Architecture: We iterate public fields only.
            # This preserves private internal state like _observers and _update_lock
            # while ensuring all live settings are synced to the current instance.
            for field in type(self).model_fields:
                setattr(self, field, getattr(new_cfg, field))

        logger.info(f"Configuration reloaded from {path}")
        self._notify_observers()

    def save(self, path: Optional[Path | str] = None, blocking: bool = False):
        """
        Saves the configuration to a TOML file atomically, preserving comments and style.
        """
        if path is None:
            path = get_config_path()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Get the current data to write
        data = self.model_dump(exclude_none=True)

        def perform_write():
            temp_path = path.with_suffix(path.suffix + ".tmp")
            try:
                # Senior Architecture: Style-preserving round-trip
                if path.exists():
                    try:
                        doc = tomlkit.parse(path.read_text(encoding="utf-8"))
                    except Exception as e:
                        logger.warning(f"Could not parse config for style preservation: {e}")
                        doc = tomlkit.document()
                else:
                    doc = tomlkit.document()

                # Senior Architecture: Logic-preserving TOML updater
                def update_toml_doc(target, source, model_cls) -> bool:
                    """
                    Recursively updates a tomlkit document while preserving style.
                    Returns True if any non-default values were added or updated.
                    """
                    from tomlkit.container import Container
                    from tomlkit.items import Comment, Table

                    try:
                        default_instance = model_cls()
                    except Exception:
                        default_instance = None

                    changed = False

                    for key, value in source.items():
                        if key.startswith("_"):
                            continue

                        if isinstance(value, dict):
                            field = model_cls.model_fields.get(key)
                            if not field:
                                continue

                            # Ensure the section exists in TOML if we're about to add to it
                            if key not in target:
                                # We only create the table if it contains non-default values
                                # We use a temporary table to check this
                                temp_table = tomlkit.table()
                                if update_toml_doc(temp_table, value, field.annotation):
                                    target[key] = temp_table
                                    changed = True
                            else:
                                if update_toml_doc(target[key], value, field.annotation):
                                    changed = True
                        else:
                            # Scalar value update logic
                            is_default = False
                            if default_instance and hasattr(default_instance, key):
                                if value == getattr(default_instance, key):
                                    is_default = True

                            if key in target:
                                # Existing key: always update to match live config
                                # (preserves comments and position)
                                if target[key] != value:
                                    target[key] = value
                                    changed = True
                            elif not is_default:
                                # New key: only add if it's a non-default value
                                # SMART PLACEMENT: Insert before its commented-out default
                                container = target.value if isinstance(target, Table) else target
                                insertion_idx = None

                                if isinstance(container, Container):
                                    for i, (_item_key, item_val) in enumerate(container.body):
                                        if isinstance(item_val, Comment):
                                            ct = item_val.trivia.comment.strip()
                                            if (
                                                ct.startswith(f"# {key} =")
                                                or ct.startswith(f"#{key} =")
                                                or ct.startswith(f"# {key}=")
                                                or ct.startswith(f"#{key}=")
                                            ):
                                                insertion_idx = i
                                                break

                                if insertion_idx is not None and hasattr(container, "_insert_at"):
                                    try:
                                        container._insert_at(insertion_idx, key, value)
                                    except Exception:
                                        target[key] = value
                                else:
                                    target[key] = value
                                changed = True

                    return changed

                update_toml_doc(doc, data, type(self))

                # Add a helpful header if it's a new file
                if not path.exists() or not doc.as_string().strip().startswith("#"):
                    header = (
                        "# ParrotInk Configuration\n"
                        "# This file is updated automatically when you change settings.\n"
                        "# You can also edit it manually while the app is closed.\n\n"
                    )
                    content = header + doc.as_string()
                else:
                    content = doc.as_string()

                temp_path.write_text(content, encoding="utf-8")
                os.replace(temp_path, path)
                logger.debug(f"Configuration saved atomically (preserving style) to {path}")
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
            threading.Thread(target=perform_write, daemon=True).start()

    @classmethod
    def from_file(cls, path: Path | str) -> "Config":
        try:
            content = Path(path).read_text(encoding="utf-8")
            data = tomlkit.parse(content)
            return cls(**data)
        except FileNotFoundError:
            return cls()
        except Exception as e:
            # Senior Architecture: Map tomlkit exceptions to ConfigError
            # to keep the interface consistent.
            from tomlkit.exceptions import TOMLKitError

            if isinstance(e, TOMLKitError):
                raise ConfigError(f"Invalid TOML format: {e}") from e
            if isinstance(e, ValidationError):
                error_messages = []
                for err in e.errors():
                    loc = ".".join(str(i) for i in err["loc"])
                    msg = err["msg"]
                    error_messages.append(f"{loc}: {msg}")
                error_summary = "\n".join(error_messages)
                raise ConfigError(f"Configuration validation failed:\n{error_summary}") from e
            raise ConfigError(f"Unexpected error loading config: {e}") from e


def load_config(path: Optional[str | Path] = None) -> Config:
    if path is None:
        path = get_config_path()
    config_path = Path(path)
    if not config_path.exists():
        # Senior Architecture: Use config.example.toml as a template to provide
        # a documented experience for the user on first launch.
        import shutil

        from .ui_utils import get_resource_path

        example_path = Path(get_resource_path("config.example.toml"))
        logger.info(f"Config not found. Looking for template at: {example_path}")

        if example_path.exists():
            try:
                config_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(example_path, config_path)
                logger.info(f"Initialized new configuration from template: {config_path}")
            except Exception as e:
                logger.error(f"Failed to copy template config: {e}. Falling back to bare defaults.")
                config = Config()
                config.save(path, blocking=True)
        else:
            # Fallback to programmatic default if example is missing (e.g. in some builds)
            logger.warning(f"Template not found at {example_path}. Using bare defaults.")
            config = Config()
            config.save(path, blocking=True)

    return Config.from_file(path)


def explain_config(config: Config, verbose: int = 0):
    from .config_resolver import resolve_effective_config

    eff = resolve_effective_config(config)
    print("\n--- ParrotInk Configuration Report ---")
    print(f"Active Provider: {eff.provider_type}")
    print(f"Hotkey:          {eff.hotkey}")


class ConfigError(Exception):
    pass
