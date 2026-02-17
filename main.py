import argparse
import asyncio
import ctypes
import sys
import time
from typing import Literal, Optional

from engine.anchor import Anchor
from engine.app_types import AppState
from engine.audio.pipeline import AudioPipeline
from engine.audio.streamer import AudioStreamer
from engine.audio_feedback import play_sound
from engine.config import Config, ConfigError, load_config
from engine.connection import ConnectionManager
from engine.credential_ui import ask_key
from engine.injection import InjectionController
from engine.interaction import InputMonitor
from engine.logging import configure_logging, get_logger
from engine.mouse import MouseMonitor
from engine.platform_win.constants import MUTEX_NAME_TEMPLATE
from engine.platform_win.instance import SingleInstance
from engine.platform_win.paths import APP_NAME
from engine.security import SecurityManager
from engine.ui_bridge import UIBridge

logger = get_logger("App")

# Constants
COOLDOWN_MANUAL_STOP = 0.5
COOLDOWN_INJECTION = 0.5


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

        self.streamer = AudioStreamer(sample_rate=sample_rate, chunk_size=chunk_size)
        self.connection_manager = ConnectionManager(
            config,
            self.on_partial,
            self.on_final,
            self.set_state,
            on_status_cb=self.ui_bridge.update_status_message,
        )
        self.pipeline = AudioPipeline(self.streamer)
        self.state = AppState.IDLE
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Interaction monitoring (Short Path)
        self.input_monitor = InputMonitor(
            on_press=self._on_hotkey_press, on_release=self._on_hotkey_release
        )
        self.input_monitor.set_hotkey(config.hotkeys.hotkey, config.hotkeys.hold_mode)
        self.input_monitor.set_any_key_callback(self._on_manual_stop)

        # Register for config changes
        self.config.register_observer(self._on_config_changed)

        # Mouse monitoring for click-away
        self.mouse_monitor = MouseMonitor(on_click_event=self._on_mouse_click)
        self.anchor: Optional[Anchor] = None

        self.session_cancelled = False
        self.start_time = 0
        self._last_manual_stop_time = 0.0
        self._last_voice_activity = 0.0
        self._inactivity_task: Optional[asyncio.Task] = None

        # Injection safety
        self.injection_controller = InjectionController()

        # Shutdown orchestration
        self._shutdown_lock = asyncio.Lock()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value):
        self._loop = value
        if value:
            self.injection_controller.set_loop(value)

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

    def _on_config_changed(self, config: Config):
        """Reacts to configuration updates in-flight."""
        logger.info("Configuration changed. Reloading settings...")
        # 1. Update hotkey capture
        self.input_monitor.set_hotkey(config.hotkeys.hotkey, config.hotkeys.hold_mode)

        # 2. Update connection manager config (crucial for provider switching)
        self.connection_manager.config = config

        # 3. Notify UI to refresh menu/labels
        self.ui_bridge.update_settings({})

    @property
    def is_connecting(self) -> bool:
        return self.state == AppState.CONNECTING

    @property
    def is_shutting_down(self) -> bool:
        return self.state == AppState.SHUTTING_DOWN

    def set_state(self, state: AppState):
        """Updates the internal state and notifies the UI."""
        if self.state == state:
            return
        logger.debug(f"State transition: {self.state.name} -> {state.name}")

        # If we are stopping a listening session, record the time for debouncing
        if self.state == AppState.LISTENING and state != AppState.LISTENING:
            self._last_manual_stop_time = time.time()
            logger.info(f"Lockout timer set at {self._last_manual_stop_time}")

        self.state = state
        self.ui_bridge.set_state(state)

    def get_provider_availability(self) -> dict[str, bool]:
        """Returns a mapping of provider names to their availability status."""
        if self.config.test.enabled:
            return {"openai": True, "assemblyai": True}

        return {
            "openai": bool(self.config.get_openai_key()),
            "assemblyai": bool(self.config.get_assemblyai_key()),
        }

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
                # We check the actual state machine for reliable toggling
                if self.state == AppState.LISTENING:
                    logger.debug("Toggle Mode: Hotkey pressed while listening. Stopping...")
                    asyncio.run_coroutine_threadsafe(self.stop_listening(), self.loop)
                else:
                    # Intent Lockout: If we just stopped, ignore this trigger
                    # to prevent rapid Stop -> Start oscillation.
                    if time.time() - self._last_manual_stop_time < 0.3:
                        logger.info("Ignoring rapid Toggle START trigger (lockout active).")
                        self.input_monitor.reset_state()
                        return
                    asyncio.run_coroutine_threadsafe(self.start_listening(), self.loop)

    def _on_hotkey_release(self):
        """Callback from InputMonitor when the hotkey is released."""
        if self.config.hotkeys.hold_mode and self.loop:
            # Only stop in hold mode
            asyncio.run_coroutine_threadsafe(self.stop_listening(), self.loop)

    def _on_manual_stop(self, key=None):
        """Callback for when a manual key press is detected during listening."""
        if not self.is_listening or self.session_cancelled:
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
        if self.session_cancelled:
            return

        text = text.strip()
        if not text:
            return

        # Forward to floating indicator
        self.ui_bridge.update_partial_text(text)

        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self.injection_controller.smart_inject(text), self.loop
            )

    def on_final(self, text: str):
        if self.session_cancelled:
            logger.debug(f"Session cancelled. Discarding final text: {text}")
            return

        text = text.strip()
        if not text:
            return

        # Forward to floating indicator
        self.ui_bridge.update_final_text(text)

        # Ensure final text is fully synchronized and add a trailing space
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self.injection_controller.smart_inject(text + " ", is_final=True), self.loop
            )

    def _play_feedback_sound(self, sound_type: Literal["start", "stop"]):
        """Plays the configured sound feedback if enabled."""
        sounds = self.config.interaction.sounds
        if not sounds.enabled:
            return

        path = sounds.start_sound_path if sound_type == "start" else sounds.stop_sound_path
        play_sound(path, volume=sounds.volume)

    def _on_mouse_click(self, x: int, y: int):
        """Callback for mouse clicks to detect click-away."""
        if not self.is_listening or self.session_cancelled:
            return

        if self.config.hotkeys.hold_mode:
            return

        if not self.config.interaction.cancel_on_click_outside_anchor:
            return

        if self.anchor and not self.anchor.is_match(x, y):
            logger.info(f"Click away detected at ({x}, {y}) outside anchor. Cancelling session.")
            if self.loop:
                asyncio.run_coroutine_threadsafe(self.stop_listening(), self.loop)

    async def start_listening(self):
        if self.state not in (AppState.IDLE, AppState.ERROR):
            logger.debug(f"start_listening ignored: current state is {self.state.name}")
            return

        # Credential check
        availability = self.get_provider_availability()
        if not availability.get(self.config.transcription.provider, False):
            logger.error(f"Missing API Key for {self.config.transcription.provider}")
            provider_title = self.config.transcription.provider.title()
            msg = f"Please set your {provider_title} API Key in the Credentials menu."
            self.ui_bridge.notify(msg, "Missing API Key")
            return

        self.session_cancelled = False
        self.start_time = time.time()
        self.set_state(AppState.CONNECTING)

        try:
            # 1. Capture anchor point
            if self.config.interaction.cancel_on_click_outside_anchor:
                self.anchor = Anchor.capture_current(self.config.interaction.anchor_scope)

            self.ui_bridge.clear_hud()

            self._last_voice_activity = time.time()
            self.pipeline.on_voice_activity = self._on_voice_activity

            # 2. Initiate connection (Ensure we have provider and adapter ready)
            # Use a timeout for the overall start operation
            async with asyncio.timeout(self.config.audio.connection_timeout_seconds + 10.0):
                await self.connection_manager.ensure_connected(is_listening=True)

                # 3. Start pipeline with the resolved connection components
                await self.pipeline.start(
                    adapter=self.connection_manager.audio_adapter,
                    provider=self.connection_manager.provider,
                    loop=self.loop,
                )
            self._play_feedback_sound("start")

            # 4. Start mouse monitoring
            self.mouse_monitor.start()
            # Enable any-key monitoring for cancellation
            self.input_monitor.enable_any_key_monitoring(True)

            # 5. Start listening monitor (inactivity + health)
            if self._inactivity_task:
                self._inactivity_task.cancel()
            self._inactivity_task = asyncio.create_task(self._listening_monitor_loop())

            self.set_state(AppState.LISTENING)

        except Exception as e:
            logger.error(f"Error starting session: {e}")
            self.set_state(AppState.ERROR)
            # Force cleanup
            if self.loop:
                self.loop.create_task(self.stop_listening())
            else:
                await self.stop_listening()

    async def stop_listening(self):
        """Stops the current transcription session."""
        if self.state == AppState.IDLE:
            return

        logger.debug("Stopping transcription session...")
        self.input_monitor.enable_any_key_monitoring(False)
        self.input_monitor.reset_state()
        self.mouse_monitor.stop()
        self.anchor = None

        if self._inactivity_task:
            self._inactivity_task.cancel()
            self._inactivity_task = None

        # Do NOT call stop_provider() here!
        # ConnectionManager handles keeping the connection "warm" or rotating it.
        await self.pipeline.stop()
        self.pipeline.on_voice_activity = None
        self.connection_manager.start_idle_timer()

        self._play_feedback_sound("stop")

        if self.state != AppState.ERROR:
            self.set_state(AppState.IDLE)

    async def shutdown(self, reason: Optional[str] = None):
        """Orchestrated shutdown."""
        async with self._shutdown_lock:
            if self.state == AppState.SHUTTING_DOWN:
                return
            logger.info(f"Shutting down application... Reason: {reason or 'Not specified'}")
            self.set_state(AppState.SHUTTING_DOWN)

            try:
                # We wrap the cleanup in a timeout to prevent hanging the system on exit
                timeout = self.config.audio.shutdown_timeout_seconds
                async with asyncio.timeout(timeout):
                    # 1. Stop interactions
                    self.input_monitor.stop()
                    self.mouse_monitor.stop()

                    # 2. Stop connection and pipeline
                    await self.connection_manager.stop_provider()
                    await self.pipeline.stop()

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
        "--background", action="store_true", help="Start without already running warning"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    subparsers.add_parser("run", help="Start the application tray icon (default)")

    eval_parser = subparsers.add_parser("eval", help="Run evaluation mode")
    eval_parser.add_argument("--audio", required=True, help="Path to WAV file")
    eval_parser.add_argument(
        "--provider", required=True, choices=["openai", "assemblyai"], help="Provider"
    )
    eval_parser.add_argument("--config", help="Path to config.toml")
    eval_parser.add_argument("--chunk-ms", type=int, help="Chunk duration")
    eval_parser.add_argument("--timeout-seconds", type=int, default=120, help="Timeout")

    set_key_parser = subparsers.add_parser("set-key", help="Set an API key")
    set_key_parser.add_argument("provider", choices=["openai", "assemblyai"], help="Provider")

    config_parser = subparsers.add_parser("config", help="Configuration utilities")
    config_parser.add_argument("--explain", action="store_true", help="Explain profiles")

    args = parser.parse_args()
    if not args.command:
        args.command = "run"
    return args


if __name__ == "__main__":
    cli_args = handle_cli()

    # Fail Fast for GUI mode
    if cli_args.command == "run":
        try:
            config = load_config()
            if config.interaction.run_at_startup:
                from engine.platform_win.startup import set_run_at_startup

                set_run_at_startup(True)
        except ConfigError as e:
            msg = f"Configuration invalid:\n\n{e}"
            logger.error(f"[CONFIG ERROR] {e}")
            ctypes.windll.user32.MessageBoxW(0, msg, "Configuration Error", 0x10)
            sys.exit(1)

    instance = SingleInstance(MUTEX_NAME_TEMPLATE.format(APP_NAME=APP_NAME))
    if instance.already_running:
        if not cli_args.background:
            instance.show_warning()
        sys.exit(0)

    if cli_args.command == "set-key":
        account_map = {
            "openai": ("openai_api_key", "OpenAI"),
            "assemblyai": ("assemblyai_api_key", "AssemblyAI"),
        }
        account_id, provider_name = account_map[cli_args.provider]
        key = ask_key(provider_name)
        if key:
            SecurityManager.set_key(account_id, key)
            print(f"Key for {provider_name} saved.")
        sys.exit(0)

    if cli_args.command == "config":
        from engine.config import explain_config

        config = load_config()
        if cli_args.explain:
            explain_config(config, verbose=cli_args.verbose)
        sys.exit(0)

    if cli_args.command == "eval":
        from engine.eval_main import main_eval

        asyncio.run(main_eval(cli_args))
        sys.exit(0)

    # Standard run mode
    config = load_config()
    configure_logging(
        config,
        verbose_count=cli_args.verbose,
        quiet=cli_args.quiet,
    )

    from engine.gui_main import main_gui

    try:
        asyncio.run(main_gui(cli_args))
    except KeyboardInterrupt:
        sys.exit(0)
