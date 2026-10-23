import argparse
import asyncio
import ctypes
import sys
import threading
import time
from concurrent.futures import Future
from typing import Literal, Optional

from engine.anchor import Anchor
from engine.app_types import AppState, AudioHardwareError, TranscriptionError
from engine.audio.pipeline import AudioPipeline
from engine.audio.streamer import AudioStreamer
from engine.audio_feedback import play_sound
from engine.config import Config, ConfigError, load_config
from engine.connection import ConnectionManager
from engine.constants import (
    COOLDOWN_INJECTION,
    COOLDOWN_MANUAL_STOP,
    INTENT_LOCKOUT_DURATION,
)
from engine.credential_ui import ask_key
from engine.injection import InjectionController
from engine.interaction import InputMonitor
from engine.logging import configure_logging, get_logger, set_global_level
from engine.mouse import MouseMonitor
from engine.platform_win.constants import MUTEX_NAME_TEMPLATE
from engine.platform_win.instance import SingleInstance
from engine.platform_win.paths import APP_NAME
from engine.security import SecurityManager
from engine.services.updates import UpdateManager, UpdateState
from engine.transcription.catalog import get_model, get_selected_model
from engine.ui_bridge import UIBridge
from engine.ui_utils import show_startup_toast

logger = get_logger("App")


class AppCoordinator:
    """
    Orchestrates the lifecycle of the application, connecting input triggers,
    audio capture, and transcription services.
    """

    def __init__(self, config: Config, ui_bridge: Optional[UIBridge] = None):
        self.config = config
        self.ui_bridge = ui_bridge or UIBridge()  # Fallback for tests

        # Calculate chunk size from ms
        sample_rate = config.audio.capture_sample_rate
        chunk_ms = config.audio.chunk_ms
        chunk_size = (sample_rate * chunk_ms) // 1000

        self.streamer = AudioStreamer(
            sample_rate=sample_rate,
            chunk_size=chunk_size,
            device_name=config.audio.input_device,
        )
        self.connection_manager = ConnectionManager(
            config,
            self.on_partial,
            self.on_final,
            self.set_state,
            on_status_cb=self.ui_bridge.update_status_message,
            on_error_cb=self._on_provider_error,
        )
        self.pipeline = AudioPipeline(self.streamer)
        self.state = AppState.IDLE
        self._configuration_lock = asyncio.Lock()
        self._stop_lock = asyncio.Lock()
        self._configuration_future: Optional[Future[None]] = None
        self._recording_provider = config.transcription.provider
        self._last_connection_settings = self._connection_settings(config)
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Interaction monitoring (Short Path)
        self.input_monitor = InputMonitor(
            on_press=self._on_hotkey_press, on_release=self._on_hotkey_release
        )
        self.input_monitor.set_hotkey(config.hotkeys.hotkey, config.hotkeys.hold_mode)
        self.input_monitor.set_any_key_callback(self._on_manual_stop)
        self.input_monitor.enable_any_key_monitoring(config.interaction.stop_on_any_key)

        # Register for config changes
        self.config.register_observer(self._on_config_changed)

        # Mouse monitoring for click-away
        self.mouse_monitor = MouseMonitor(on_click_event=self._on_mouse_click)
        self.start_time = 0
        self._last_manual_stop_time = 0.0
        self._last_voice_activity = 0.0
        self._inactivity_task: Optional[asyncio.Task] = None

        # Statistics tracking
        self.session_start_time = 0.0
        self.session_word_count = 0

        # Injection safety
        self.injection_controller = InjectionController(
            on_target_lost=self._on_insertion_target_lost
        )

        # v2 Reliability Architecture
        from engine.platform_win.session import SessionMonitor

        self.session_monitor = SessionMonitor(on_unlock=self._on_unlock)

        # Track provider changes for silent transitions
        self._last_provider = config.transcription.provider

        # Update checking service
        self._stop_event = threading.Event()
        self.update_manager = UpdateManager(
            on_update_available=self._on_update_available,
            stop_event=self._stop_event,
        )
        self.update_manager.start()

        # Audio Recovery
        self._retry_mic_task: Optional[asyncio.Task] = None
        self._last_audio_failure_reason: Optional[str] = None

        # Auto-Select Provider (Senior Architecture: Startup Guard)
        self._ensure_valid_provider()

        # Shutdown orchestration
        self._shutdown_lock = asyncio.Lock()

    def _on_update_available(
        self,
        version_tag: str,
        release_url: str,
        state: UpdateState = UpdateState.UPDATE_AVAILABLE,
        percent: int = 0,
    ):
        """Callback from UpdateManager when a new version is detected."""
        logger.info(
            f"Update detected: {version_tag}. State: {state.name}, "
            f"Progress: {percent}%. Notifying UI."
        )
        self.ui_bridge.update_version_notification(version_tag, release_url, state, percent)

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value):
        self._loop = value
        if value:
            self.injection_controller.loop = value
            # Start v2 reliability monitors
            self.session_monitor.start()

    @property
    def provider(self):
        return self.connection_manager.provider

    @provider.setter
    def provider(self, value):
        self.connection_manager.provider = value

    @property
    def audio_adapter(self):
        return self.connection_manager.audio_adapter

    @audio_adapter.setter
    def audio_adapter(self, value):
        self.connection_manager.audio_adapter = value

    @property
    def is_listening(self) -> bool:
        return self.state == AppState.LISTENING

    @property
    def is_connecting(self) -> bool:
        return self.state == AppState.CONNECTING

    def _on_config_changed(self, config: Config):
        """Reacts to configuration updates in-flight."""
        logger.info("Configuration changed. Reloading settings...")

        # UI-only settings must not tear down a live transcription connection.
        settings = self._connection_settings(config)
        connection_changed = settings != self._last_connection_settings
        self._last_connection_settings = settings
        self._last_provider = config.transcription.provider

        self.input_monitor.set_hotkey(config.hotkeys.hotkey, config.hotkeys.hold_mode)
        self.input_monitor.enable_any_key_monitoring(config.interaction.stop_on_any_key)

        if connection_changed and self.loop:
            self._configuration_future = asyncio.run_coroutine_threadsafe(
                self._apply_connection_config(config), self.loop
            )
        elif not self.loop:
            self.connection_manager.config = config
            self.streamer.device_name = config.audio.input_device

        # 3. Update logging level dynamically
        set_global_level(config.logging.file_level)

        # 4. Notify UI to refresh menu/labels
        self.ui_bridge.update_settings({})
        self.ui_bridge.refresh_hud()

        # Reset to IDLE if we were in ERROR state and the configuration change resolved it
        if self.state == AppState.ERROR:
            current_provider = config.transcription.provider
            if self.get_provider_availability().get(current_provider, False):
                logger.info(
                    "Configuration update resolved provider error. Resetting state to IDLE."
                )
                self.set_state(AppState.IDLE)
                self.ui_bridge.clear_hud()

    @staticmethod
    def _connection_settings(config: Config) -> dict:
        settings = config.model_dump(include={"audio", "transcription", "test"})
        provider = config.transcription.provider
        settings["provider_settings"] = getattr(config.providers, provider).model_dump()
        return settings

    async def _apply_connection_config(self, config: Config):
        async with self._configuration_lock:
            if self.is_shutting_down:
                return
            if self.is_listening or self.is_connecting or self.state == AppState.STOPPING:
                await self.stop_listening(silent=True)
            await self.connection_manager.stop_provider()
            self.connection_manager.config = config
            self.streamer.device_name = config.audio.input_device
            self.streamer.sample_rate = config.audio.capture_sample_rate
            self.streamer.chunk_size = (
                config.audio.capture_sample_rate * config.audio.chunk_ms // 1000
            )

    def _on_insertion_target_lost(self):
        if self.is_listening and self.loop:
            asyncio.run_coroutine_threadsafe(self.stop_listening(silent=True), self.loop)

    @property
    def is_shutting_down(self) -> bool:
        return self.state == AppState.SHUTTING_DOWN

    def _on_provider_error(self, error: TranscriptionError):
        """Callback from connection manager when a fatal provider error occurs."""
        logger.error(f"Fatal Provider Error: {error.title} - {error.message}")

        if self.loop:
            # Senior Architecture: Bridge error to UI thread safely
            self.loop.call_soon_threadsafe(self._handle_fatal_error, error)

    def _handle_fatal_error(self, error: TranscriptionError):
        """Internal handler for fatal errors, called on main thread."""
        # 1. Stop any active listening immediately
        if self.is_listening or self.is_connecting:
            asyncio.create_task(self.stop_listening(silent=True))

        # 2. Transition to Error state
        self.set_state(AppState.ERROR)

        # 3. Update HUD with specific error details
        self.ui_bridge.update_status_message(f"Error: {error.title}")
        self.ui_bridge.update_partial_text(error.message)

        # 4. Record statistics (as failure)
        self.ui_bridge.record_stats(
            duration=0.0,
            words=0,
            provider=self.config.transcription.provider,
            error=True,
        )

    def set_state(self, state: AppState):
        """Updates the internal state and notifies the UI."""
        if self.state == state:
            if state == AppState.ERROR:
                # Even if we are already in ERROR, guarantee the input monitor is reset
                # to prevent key hangs if a start attempt fails early.
                self.input_monitor.reset_state()
            return
        logger.debug(f"State transition: {self.state.name} -> {state.name}")

        # If we are stopping a listening session, record the time for debouncing
        if self.state == AppState.LISTENING and state != AppState.LISTENING:
            self._last_manual_stop_time = time.time()
            logger.info(f"Lockout timer set at {self._last_manual_stop_time}")

        self.state = state
        if state == AppState.ERROR:
            # Guarantee that input monitor is reset so keys do not hang
            self.input_monitor.reset_state()
        self.ui_bridge.set_state(state)

    def get_provider_availability(self) -> dict[str, bool]:
        """Returns a mapping of provider names to their availability status."""
        if self.config.test.enabled:
            return {"openai": True, "assemblyai": True, "cloudflare": True}

        def is_valid(provider: str, key: str | None) -> bool:
            """
            Senior Validation Strategy: Positive pattern matching.
            Avoids blacklisting magic numbers (like '4444') by strictly
            whitelisting known provider key formats.
            """
            if not key:
                return False
            key = key.strip()
            if not key:
                return False

            if provider == "openai":
                # OpenAI: sk- (legacy) or sk-proj- (project keys)
                return key.startswith("sk-")
            elif provider == "assemblyai":
                # AssemblyAI: 32-character hex string
                return len(key) == 32 and all(c in "0123456789abcdefABCDEF" for c in key)
            return True

        return {
            "openai": is_valid("openai", self.config.get_openai_key()),
            "assemblyai": is_valid("assemblyai", self.config.get_assemblyai_key()),
            "cloudflare": bool(
                self.config.get_cloudflare_key()
                and self.config.providers.cloudflare.core.account_id
                and self.config.providers.cloudflare.core.gateway_id
            ),
        }

    def _ensure_valid_provider(self):
        """
        Senior Architecture: Auto-Selection Logic.
        If the current provider is invalid AND exactly one other provider is valid,
        automatically switch to that provider.
        """
        if self.config.test.enabled:
            return

        availability = self.get_provider_availability()
        current_provider = self.config.transcription.provider

        # If current provider is valid, do nothing
        if availability.get(current_provider, False):
            return

        # Current is invalid. Check how many others are valid.
        valid_providers = [p for p, valid in availability.items() if valid]

        if len(valid_providers) == 1:
            new_provider = valid_providers[0]
            logger.info(f"Auto-switching provider from {current_provider} to {new_provider}")
            self.config.update_and_save({"transcription": {"provider": new_provider}})
            # Since update_and_save triggers observers, AppCoordinator will sync its internal state.

    async def ensure_connected(self):
        """Proxy to connection manager."""
        await self.connection_manager.ensure_connected(self.is_listening)

    def _on_hotkey_press(self):
        """Callback from InputMonitor when the hotkey is pressed."""
        if self.loop:
            if self.config.hotkeys.hold_mode:
                # Hold Mode: Start listening
                asyncio.run_coroutine_threadsafe(self.start_listening(), self.loop)
            else:
                # Toggle Mode: Toggle listening
                # Senior Architecture: Include CONNECTING in the toggle-stop logic.
                # This prevents rapid re-entrancy and inconsistent state transitions.
                if self.state in (AppState.LISTENING, AppState.CONNECTING):
                    logger.debug(
                        f"Toggle Mode: Hotkey pressed while {self.state.name}. Stopping..."
                    )
                    asyncio.run_coroutine_threadsafe(self.stop_listening(), self.loop)
                else:
                    # Intent Lockout: If we just stopped, ignore this trigger
                    # to prevent rapid Stop -> Start oscillation.
                    if time.time() - self._last_manual_stop_time < INTENT_LOCKOUT_DURATION:
                        logger.info("Ignoring rapid Toggle START trigger (lockout active).")
                        return
                    asyncio.run_coroutine_threadsafe(self.start_listening(), self.loop)

    def _on_hotkey_release(self):
        """Callback from InputMonitor when the hotkey is released."""
        if self.loop:
            # Senior Architecture: We always call stop_listening here.
            # In Hold Mode, this is the trigger. In Toggle Mode, this is only
            # called when the monitor explicitly sends a 'stop' event.
            asyncio.run_coroutine_threadsafe(self.stop_listening(), self.loop)

    def _on_manual_stop(self, key=None):
        """Callback for when a manual key press is detected during listening."""
        if not self.is_listening or self.injection_controller.cancelled:
            return

        now = time.time()
        # Cooldown to avoid catching the release of the hotkey itself
        # However, in Toggle Mode, if the key pressed IS the hotkey, we allow it.
        is_hotkey = False
        if key and self.config.hotkeys.hotkey:
            # Simple check if the key name is in our hotkey string
            is_hotkey = key.lower() in self.config.hotkeys.hotkey.lower()

        if not is_hotkey and (now - self.start_time < COOLDOWN_MANUAL_STOP):
            return

        # Ignore keyboard events if they are coming from our own injection
        if self.injection_controller.is_injecting or (
            now - self.injection_controller.last_injection_time < COOLDOWN_INJECTION
        ):
            return

        # If we are in Toggle mode, ANY key press (other than hotkey) should stop the session.
        if not self.config.hotkeys.hold_mode:
            logger.info(f"Manual stop triggered by key: {key}")
            if self.loop:
                asyncio.run_coroutine_threadsafe(self.stop_listening(), self.loop)

    def _on_voice_activity(self, active: bool):
        """Callback from AudioPipeline when voice activity is detected."""
        if active:
            self._last_voice_activity = time.time()
        self.ui_bridge.update_voice_activity(active)

    async def _listening_monitor_loop(self):
        """Background task that monitors pipeline health and inactivity."""
        timeout = self.config.audio.inactivity_timeout_seconds
        logger.debug(f"Listening monitor started (inactivity_timeout={timeout}s)")

        try:
            while self.state == AppState.LISTENING:
                await asyncio.sleep(0.5)  # Check twice per second
                if self.state != AppState.LISTENING:
                    break

                anchor = self.injection_controller.target
                if (
                    anchor is not None
                    and self.config.interaction.cancel_on_click_outside_anchor
                    and not self.config.hotkeys.hold_mode
                ):
                    has_focus = await asyncio.to_thread(anchor.has_focus)
                    if self.state != AppState.LISTENING:
                        break
                    if self.injection_controller.target is anchor and not has_focus:
                        self._cancel_anchor_session("Editor focus left the recording target")
                        break

                # 1. Check for Pipeline Failure (e.g. provider network error)
                if not self.pipeline.is_active:
                    logger.error("Audio pipeline stopped unexpectedly during listening.")
                    self.set_state(AppState.ERROR)
                    # Force cleanup
                    if self.loop:
                        self.loop.create_task(self.stop_listening())
                    else:
                        await self.stop_listening()
                    break

                # 2. Check for Inactivity (Toggle Mode only)
                if not self.config.hotkeys.hold_mode:
                    now = time.time()
                    elapsed = now - self._last_voice_activity
                    if elapsed >= timeout:
                        logger.info(f"Auto-stopping due to {timeout}s inactivity.")
                        if self.loop:
                            asyncio.run_coroutine_threadsafe(self.stop_listening(), self.loop)
                        break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in listening monitor loop: {e}")

    def on_partial(self, text: str):
        if self.injection_controller.cancelled:
            return

        text = text.strip()
        if not text:
            return

        # 1. Forward to floating indicator (Always show in HUD for responsiveness)
        self.ui_bridge.update_partial_text(text)

        # 2. Inject into target application (Only if enabled in config)
        if self.config.transcription.partial_results:
            if self.loop and self.injection_controller:
                self.injection_controller.queue(text)

    def on_final(self, text: str):
        if self.injection_controller.cancelled:
            logger.debug(f"Session cancelled. Discarding final text: {text}")
            return

        if not text.strip():
            return

        # Update statistics
        self.session_word_count += len(text.split())

        # Forward to floating indicator
        self.ui_bridge.update_final_text(text.strip())

        # Preserve the formatter's turn separators; the injector owns final spacing.
        if self.loop and self.injection_controller:
            self.injection_controller.queue(text, is_final=True)

    def _play_feedback_sound(self, sound_type: Literal["start", "stop"]):
        """Plays the configured sound feedback if enabled."""
        sounds = self.config.interaction.sounds
        if not sounds.enabled:
            return

        path = sounds.start_sound_path if sound_type == "start" else sounds.stop_sound_path
        play_sound(path, volume=sounds.volume)

    def _on_mouse_click(self, x: int, y: int):
        """Callback for mouse clicks to detect click-away."""
        if not self.is_listening or self.injection_controller.cancelled:
            return

        if self.config.hotkeys.hold_mode:
            return

        if not self.config.interaction.cancel_on_click_outside_anchor:
            return

        if self.injection_controller.target and not self.injection_controller.target.is_match(x, y):
            self._cancel_anchor_session("Click outside the recording target")

    def _cancel_anchor_session(self, reason: str):
        if self.injection_controller.cancelled:
            return
        logger.info("%s; cancelling dictation", reason)
        self.injection_controller.cancel()
        if self.loop:
            asyncio.run_coroutine_threadsafe(self.stop_listening(), self.loop)

    async def start_listening(self):
        if self._configuration_future and not self._configuration_future.done():
            await asyncio.wrap_future(self._configuration_future)
        if self.state not in (AppState.IDLE, AppState.ERROR):
            logger.debug(f"start_listening ignored: current state is {self.state.name}")
            return

        if (
            self.config.transcription.provider == "cloudflare"
            and get_model("cloudflare", self.config.providers.cloudflare.core.model).protocol
            == "unavailable"
        ):
            self.set_state(AppState.ERROR)
            self.ui_bridge.update_status_message("Model unavailable in Cloudflare")
            self.ui_bridge.notify(
                "Select Nova-3, Flux, or Grok STT in Cloudflare Gateway settings, "
                "or use the direct OpenAI provider.",
                "Cloudflare Model Unavailable",
            )
            return

        # 1. API Key Check
        availability = self.get_provider_availability()
        if not availability.get(self.config.transcription.provider, False):
            title = "Missing API Key"
            msg = "Provider Missing API Key. Right-click Tray Icon > Settings to configure."
            hint = "Open Tray Menu > Settings to add your key."
            if self.config.transcription.provider == "cloudflare":
                core = self.config.providers.cloudflare.core
                missing = []
                if not self.config.get_cloudflare_key():
                    missing.append("API token")
                if not core.account_id:
                    missing.append("account ID")
                if not core.gateway_id:
                    missing.append("gateway ID")
                if not missing:
                    missing.append("supported transcription model")
                title = "Cloudflare Settings Incomplete"
                msg = f"Cloudflare is missing: {', '.join(missing)}."
                hint = "Open Settings > Configure Cloudflare Gateway."
                from engine.platform_win.paths import get_config_path

                logger.error("Cloudflare configuration path: %s", get_config_path())
            logger.error(msg)
            self.ui_bridge.notify(f"{msg} {hint}", title)

            # Show onboarding instructions in HUD
            self.set_state(AppState.ERROR)
            self.ui_bridge.update_status_message(msg)
            self.ui_bridge.update_partial_text(hint)
            return

        # 2. Fast Path: If we previously failed due to privacy, check if it's still blocked
        # before attempting to open the stream to avoid the ~50ms PortAudio init cost.
        if self._last_audio_failure_reason == "privacy" and sys.platform == "win32":
            from engine.platform_win.audio_diag import is_mic_privacy_blocked

            if is_mic_privacy_blocked():
                logger.warning("Microphone access still blocked by Windows Privacy settings.")
                self.set_state(AppState.ERROR)
                self.ui_bridge.show_hardware_error_popup()
                return

        self._recording_provider = self.config.transcription.provider
        self.start_time = time.time()
        self.session_start_time = self.start_time
        self.session_word_count = 0

        # Clear HUD before CONNECTING to avoid wiping the "Connecting..." message
        self.ui_bridge.clear_hud()

        self.set_state(AppState.CONNECTING)

        try:
            # 1. Capture anchor point
            target = await asyncio.to_thread(
                Anchor.capture_current, self.config.interaction.anchor_scope
            )
            if self.state != AppState.CONNECTING:
                return
            if not target.can_dictate:
                self.injection_controller.cancel()
                self.injection_controller.release()
                self.input_monitor.reset_state()
                self.session_start_time = 0.0
                self.set_state(AppState.IDLE)
                assessment = target.assessment
                self.ui_bridge.update_status_message(
                    "Cannot verify this field; click an editable text field"
                    if assessment.decision == "unknown"
                    else "Click an editable text field"
                )
                focused = target.focused_element
                logger.info(
                    "Dictation rejected: decision=%s reason=%s control_type=%s "
                    "read_only=%s enabled=%s password=%s",
                    assessment.decision,
                    assessment.reason,
                    focused.control_type if focused else None,
                    focused.read_only if focused else None,
                    focused.enabled if focused else None,
                    focused.password if focused else None,
                )
                return
            self.injection_controller.begin(target)

            self._last_voice_activity = time.time()
            self.pipeline.on_voice_activity = self._on_voice_activity

            # 2. Initiate connection (Ensure we have provider and adapter ready)
            # Use a timeout for the overall start operation
            async with asyncio.timeout(self.config.audio.connection_timeout_seconds + 10.0):
                await self.connection_manager.ensure_connected(is_listening=True)

                # Senior Architecture: Ghost Session Guard
                # If stop_listening was called while we were awaiting connection,
                # we must abort here to prevent background recording.
                if self.state != AppState.CONNECTING:
                    logger.info("Session cancelled during connection. Aborting pipeline start.")
                    return

                has_focus = await asyncio.to_thread(target.has_focus)
                if self.state != AppState.CONNECTING:
                    return
                if not has_focus:
                    self.injection_controller.cancel()
                    await self.stop_listening(silent=True)
                    self.ui_bridge.update_status_message(
                        "Target changed; click an editable text field"
                    )
                    return

                self.connection_manager.provider.reset_utterance()

                # 3. Start pipeline with the resolved connection components
                await self.pipeline.start(
                    adapter=self.connection_manager.audio_adapter,
                    provider=self.connection_manager.provider,
                    loop=self.loop,
                )
            self._play_feedback_sound("start")

            # 4. Start mouse monitoring
            self._start_mouse_monitor()
            self.input_monitor.enable_any_key_monitoring(self.config.interaction.stop_on_any_key)

            # 5. Start listening monitor (inactivity + health)
            if self._inactivity_task:
                self._inactivity_task.cancel()
            self._inactivity_task = asyncio.create_task(self._listening_monitor_loop())

            self.set_state(AppState.LISTENING)

        except AudioHardwareError as e:
            logger.error(f"Hardware error: {e}")
            self.set_state(AppState.ERROR)
            self._handle_audio_failure(e)
            if self.loop:
                self.loop.create_task(self.stop_listening())
            else:
                await self.stop_listening()

        except Exception as e:
            logger.error(f"Error starting session: {e}")
            self.set_state(AppState.ERROR)
            # Force cleanup
            if self.loop:
                self.loop.create_task(self.stop_listening())
            else:
                await self.stop_listening()

    def _start_mouse_monitor(self):
        if (
            self.config.interaction.cancel_on_click_outside_anchor
            and not self.config.hotkeys.hold_mode
        ):
            self.mouse_monitor.start()

    def _handle_audio_failure(self, error: Exception):
        """
        Senior Diagnostic Logic:
        Differentiate between 'Privacy Block', 'Missing Device', and 'Busy Device'.
        Classify-on-failure to determine the true root cause.
        """
        import sounddevice as sd

        # Default classification
        error_type = "device"
        error_msg = "Audio Device Unavailable"
        error_sub = "Another app might be using the mic. Right-click Tray > Fix."

        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d["max_input_channels"] > 0]
            if not input_devices:
                error_type = "missing"
                error_msg = "No Microphone Detected"
                error_sub = "Please plug in a microphone and restart."
        except Exception:
            input_devices = []

        if sys.platform == "win32" and error_type != "missing":
            from engine.platform_win.audio_diag import is_mic_privacy_blocked

            if is_mic_privacy_blocked():
                error_type = "privacy"
                error_msg = "Microphone Access Denied"
                error_sub = "Blocked by Windows. Check 'Privacy & security > Microphone'."
                # Senior UX: Show unmissable popup
                self.ui_bridge.show_hardware_error_popup()
            elif (
                "permission" in str(error).lower()
                or "access denied" in str(error).lower()
                or "paerrorcode -9999" in str(error).lower()
                or "wait for device wait timed out" in str(error).lower()
            ):
                # Fallback detection if registry check missed it but driver reported it
                error_type = "privacy"
                error_msg = "Microphone Access Denied"
                error_sub = "Permission error. Check Windows Privacy settings."
                self.ui_bridge.show_hardware_error_popup()

        # Cache the reason to avoid redundant stream attempts on rapid retries
        self._last_audio_failure_reason = error_type

        self.ui_bridge.update_audio_error(error_type)
        self.ui_bridge.update_status_message(error_msg)
        self.ui_bridge.update_partial_text(error_sub)

        # Start recovery polling
        if self.loop and (not self._retry_mic_task or self._retry_mic_task.done()):
            self._retry_mic_task = self.loop.create_task(self._poll_mic_recovery())

    async def _poll_mic_recovery(self):
        """Background task that polls for mic availability to auto-clear error state."""
        import sounddevice as sd

        logger.info("Started microphone recovery polling.")
        try:
            while self.state == AppState.ERROR:
                await asyncio.sleep(5.0)  # Poll every 5 seconds
                try:

                    def check_mic():
                        # Attempt a minimal stream open to check if hardware is actually available
                        with sd.InputStream(
                            samplerate=16000, channels=1, blocksize=512, dtype="float32"
                        ):
                            pass

                    await self.loop.run_in_executor(None, check_mic)
                    # Success! Hardware is back.
                    logger.info("Microphone recovery successful. Clearing error state.")
                    self.ui_bridge.update_audio_error(None)  # Clear UI fix links
                    if self.state == AppState.ERROR:
                        self.set_state(AppState.IDLE)
                        self.ui_bridge.update_status_message("Microphone Restored")
                        self.ui_bridge.update_partial_text("You can now resume transcription.")
                    break
                except Exception:
                    # Still failing, continue polling
                    continue
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in mic recovery poll: {e}")

    async def stop_listening(self, silent: bool = False):
        async with self._stop_lock:
            await self._stop_listening(silent)

    async def _stop_listening(self, silent: bool = False):
        """Stops the current transcription session."""
        if self.state == AppState.IDLE:
            return

        was_error = self.state == AppState.ERROR
        if not was_error and not self.is_shutting_down:
            self.set_state(AppState.STOPPING)

        logger.debug("Stopping transcription session...")
        self.input_monitor.reset_state()
        self.mouse_monitor.stop()

        if self._inactivity_task:
            self._inactivity_task.cancel()
            self._inactivity_task = None

        # Do NOT call stop_provider() here!
        # ConnectionManager handles keeping the connection "warm" or rotating it.
        await self.pipeline.stop()
        self.pipeline.on_voice_activity = None
        provider = self.connection_manager.provider
        if (
            provider
            and provider.is_running
            and not self.injection_controller.cancelled
            and not was_error
        ):
            stage = "provider_finalize"
            started = time.monotonic()
            try:
                async with asyncio.timeout(self.config.audio.provider_stop_timeout_seconds):
                    await provider.finish_utterance()
                # Final callbacks queue cursor writes; drain them before a new anchor
                # or session can be selected.
                stage = "editor_insertion"
                async with asyncio.timeout(self.config.audio.provider_stop_timeout_seconds):
                    await self.injection_controller.drain()
            except Exception as exc:
                # Record the cause without echoing server payloads or transcript text.
                logger.error(
                    "Dictation stop failed: provider=%s model=%s stage=%s elapsed=%.2fs "
                    "pending_insertions=%d error=%s",
                    self._recording_provider,
                    get_selected_model(self.config, self._recording_provider),
                    stage,
                    time.monotonic() - started,
                    self.injection_controller.pending_count,
                    type(exc).__name__,
                )
                self.injection_controller.cancel()
                self.set_state(AppState.ERROR)
                self.ui_bridge.update_status_message(
                    "Could not insert final text"
                    if stage == "editor_insertion"
                    else "Final transcription failed"
                )
                await self.connection_manager.stop_provider()
        if (
            self.injection_controller.cancelled
            or was_error
            or self.state == AppState.ERROR
            or self.config.audio.connection_mode == "on_demand"
        ):
            await self.connection_manager.stop_provider()
        elif provider is not None and not provider.is_running:
            # Grok's audio.done is terminal even when the app uses warm mode.
            # Detach its old receiver and adapter before another recording starts.
            await self.connection_manager.stop_provider()
        else:
            self.connection_manager.start_idle_timer()

        self.injection_controller.release()
        if not silent:
            self._play_feedback_sound("stop")

        # Record statistics
        duration = 0.0
        if self.session_start_time > 0:
            duration = time.time() - self.session_start_time

        self.ui_bridge.record_stats(
            duration=duration,
            words=self.session_word_count,
            provider=self._recording_provider,
            error=(self.state == AppState.ERROR),
        )
        self.session_start_time = 0.0
        self.session_word_count = 0

        if self.state != AppState.ERROR:
            self.set_state(AppState.IDLE)

    def _on_unlock(self):
        """Callback from SessionMonitor when Windows is unlocked."""
        logger.info("Session Unlock detected. Refreshing hotkey hooks...")
        self.input_monitor.restart()

    async def shutdown(self, reason: Optional[str] = None):
        """Orchestrated shutdown."""
        async with self._shutdown_lock:
            if self.state == AppState.SHUTTING_DOWN:
                return
            logger.info(f"Shutting down application... Reason: {reason or 'Not specified'}")
            self.set_state(AppState.SHUTTING_DOWN)
            self._stop_event.set()

            # Stop v2 monitors
            self.session_monitor.stop()
            if self._retry_mic_task:
                self._retry_mic_task.cancel()

            try:
                # We wrap the cleanup in a timeout to prevent hanging the system on exit
                timeout = self.config.audio.shutdown_timeout_seconds
                async with asyncio.timeout(timeout):
                    # 1. Stop interactions
                    self.input_monitor.stop()
                    self.mouse_monitor.stop()

                    # 2. Stop connection and pipeline
                    await self.pipeline.stop()
                    self.injection_controller.cancel()
                    await self.connection_manager.stop_provider()
                    self.streamer.stop()

                    # 3. Final cleanup
                    self.ui_bridge.stop()
                    logger.info("Application coordinator shut down.")
            except TimeoutError:
                logger.error("Shutdown timed out. Forcing exit.")
                import os

                os._exit(1)
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
                import os

                os._exit(1)


def handle_cli():
    parser = argparse.ArgumentParser(
        description="ParrotInk: A real-time voice-to-text application.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress console output")
    parser.add_argument("--log-file", type=str, help="Override default log file path")
    parser.add_argument(
        "--background",
        action="store_true",
        help="Start in background mode (suppresses onboarding and notifications)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    subparsers.add_parser("run", help="Start the application tray icon (default)")

    eval_parser = subparsers.add_parser("eval", help="Run evaluation mode")
    eval_parser.add_argument("--audio", required=True, help="Path to WAV file")
    eval_parser.add_argument(
        "--provider", required=True, choices=["openai", "assemblyai", "cloudflare"], help="Provider"
    )
    eval_parser.add_argument("--model", help="Override the selected transcription model")
    eval_parser.add_argument("--config", help="Path to config.toml")
    eval_parser.add_argument("--chunk-ms", type=int, help="Chunk duration")
    eval_parser.add_argument("--timeout-seconds", type=int, default=120, help="Timeout")

    set_key_parser = subparsers.add_parser("set-key", help="Set an API key")
    set_key_parser.add_argument(
        "provider", choices=["openai", "assemblyai", "cloudflare"], help="Provider"
    )

    config_parser = subparsers.add_parser("config", help="Configuration utilities")
    config_parser.add_argument("--explain", action="store_true", help="Explain profiles")

    args = parser.parse_args()
    if not args.command:
        args.command = "run"
    return args


if __name__ == "__main__":
    cli_args = handle_cli()

    # Senior Architecture: Load configuration exactly ONCE.
    # This prevents redundant I/O and ensures consistency between the startup check
    # and the main GUI loop.
    try:
        config = load_config()
    except ConfigError as e:
        msg = f"Configuration invalid:\n\n{e}"
        logger.error(f"[CONFIG ERROR] {e}")
        # Always show a message box for configuration failures in GUI mode
        if cli_args.command == "run":
            ctypes.windll.user32.MessageBoxW(0, msg, "Configuration Error", 0x10)
        else:
            print(f"\n[CONFIG ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    # 1. Sync Windows Startup (Authoritative Sync)
    if cli_args.command == "run" and sys.platform == "win32":
        from engine.platform_win.startup import sync_startup_with_config

        sync_startup_with_config(config.interaction.run_at_startup)

    # 2. Single Instance Protection
    instance = SingleInstance(MUTEX_NAME_TEMPLATE.format(APP_NAME=APP_NAME))
    if instance.already_running:
        if not cli_args.background:
            instance.show_warning()
        sys.exit(0)

    # 3. Command Routing
    if cli_args.command == "set-key":
        account_map = {
            "openai": ("openai_api_key", "OpenAI"),
            "assemblyai": ("assemblyai_api_key", "AssemblyAI"),
            "cloudflare": ("cloudflare_api_token", "Cloudflare Gateway API Token"),
        }
        account_id, provider_name = account_map[cli_args.provider]
        key = ask_key(None, f"Set {provider_name} Key")
        if key:
            SecurityManager.set_key(account_id, key)
            print(f"Key for {provider_name} saved.")
        sys.exit(0)

    if cli_args.command == "config":
        from engine.config import explain_config

        if cli_args.explain:
            explain_config(config, verbose=cli_args.verbose)
        sys.exit(0)

    if cli_args.command == "eval":
        from engine.eval_main import main_eval

        # We pass the already loaded config to sub-mains if they support it
        # or let them load it themselves if needed (usually they use load_config too)
        asyncio.run(main_eval(cli_args))
        sys.exit(0)

    # Standard run mode (GUI)
    configure_logging(
        config,
        verbose_count=cli_args.verbose,
        quiet=cli_args.quiet,
    )

    # 4. Onboarding Popup (Gatekeeper)
    # We run this before main_gui to ensure it blocks and acts as a pure introduction.
    if not cli_args.background and config.ui.show_onboarding_popup:
        from engine.onboarding_ui import show_onboarding_blocking

        dont_show_again = show_onboarding_blocking()
        if dont_show_again:
            logger.info("User requested to hide onboarding popup in the future.")
            config.update_and_save({"ui": {"show_onboarding_popup": False}}, blocking=True)

    from engine.gui_main import main_gui

    if not cli_args.background:
        show_startup_toast(config)

    try:
        asyncio.run(main_gui(cli_args, config=config))
    except KeyboardInterrupt:
        sys.exit(0)
