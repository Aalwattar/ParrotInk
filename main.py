from __future__ import annotations

import asyncio
import sys
import time
from typing import Literal, Optional, Set

from pynput import keyboard

from engine.anchor import Anchor
from engine.app_types import AppState
from engine.audio import AudioStreamer
from engine.audio.pipeline import AudioPipeline
from engine.audio_feedback import play_sound
from engine.config import Config
from engine.connection import ConnectionManager
from engine.credential_ui import ask_key
from engine.injection import InjectionController
from engine.interaction import InputMonitor
from engine.logging import get_logger, shutdown_logging
from engine.mouse import MouseMonitor
from engine.security import SecurityManager
from engine.ui_bridge import UIBridge

logger = get_logger("Main")


class AppCoordinator:
    def __init__(self, config: Config, ui_bridge: Optional[UIBridge] = None):
        self.config = config
        self.ui_bridge = ui_bridge or UIBridge()  # Fallback for tests

        # Calculate chunk size from ms
        sample_rate = config.audio.capture_sample_rate
        chunk_ms = config.audio.chunk_ms
        chunk_size = (sample_rate * chunk_ms) // 1000

        self.streamer = AudioStreamer(sample_rate=sample_rate, chunk_size=chunk_size)
        self.connection_manager = ConnectionManager(
            config, self.on_partial, self.on_final, self.set_state
        )
        self.pipeline = AudioPipeline(self.streamer)
        self.state = AppState.IDLE
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Hotkey state
        self.hotkey_pressed = False
        self.target_hotkey = self._parse_hotkey(config.hotkeys.hotkey)
        self.current_keys: Set[str] = set()

        # Interaction monitoring
        self.input_monitor = InputMonitor(on_press=self.on_press, on_release=self.on_release)
        self.input_monitor.set_any_key_callback(self._on_manual_stop)

        # Register for config changes
        self.config.register_observer(self._on_config_changed)

        # Mouse monitoring for click-away
        self.mouse_monitor = MouseMonitor(on_click_event=self._on_mouse_click)
        self.anchor: Optional[Anchor] = None

        self.session_cancelled = False
        self.start_time = 0

        # Injection safety
        self.injection_controller = InjectionController()

        # Shutdown orchestration
        self._shutdown_lock = asyncio.Lock()

        logger.debug(f"Target hotkey set to: {self.target_hotkey}")

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
        self.target_hotkey = self._parse_hotkey(config.hotkeys.hotkey)
        logger.debug(f"Target hotkey updated to: {self.target_hotkey}")

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

    def _on_manual_stop(self, key=None):
        """Callback for when a manual key press is detected during listening."""
        # Cooldown to avoid catching the release/repeat of the hotkey itself
        now = time.time()
        if now - self.start_time < 0.5:
            return

        # Ignore keyboard events if they are coming from our own injection
        # Increase safety window to 0.5s to account for system lag in event delivery
        if self.injection_controller.is_injecting or (
            now - self.injection_controller.last_injection_time < 0.5
        ):
            return

        # If we are in Toggle mode, ANY key press should stop the session.
        # If we are in Hold mode, only NON-hotkey keys should stop it (though
        # normally hold mode stops on release).
        if not self.config.hotkeys.hold_mode:
            # Toggle Mode: Stop on ANY key.
            logger.info(f"Manual stop triggered by key: {key}")
            self.session_cancelled = True
            if self.loop:
                asyncio.run_coroutine_threadsafe(self.stop_listening(), self.loop)
        else:
            # Hold Mode: The "Stop on Any Key" feature is DISABLED.
            # We rely strictly on the hotkey release event (handled in on_release).
            return

    def _parse_hotkey(self, hotkey_str: str) -> Set[str]:
        """Parse hotkey string into a set of canonical names."""
        parts = hotkey_str.lower().split("+")
        norm_map = {
            "ctrl": "ctrl",
            "control": "ctrl",
            "alt": "alt",
            "shift": "shift",
            "win": "cmd",
            "cmd": "cmd",
        }
        return {norm_map.get(p.strip(), p.strip()) for p in parts if p.strip()}

    def _get_canonical_name(self, key) -> str:
        """Get canonical name for a pynput key and normalize modifiers."""
        if isinstance(key, keyboard.KeyCode):
            if key.char:
                return str(key.char.lower())
            if key.vk:
                # 65-90 are A-Z
                if 65 <= key.vk <= 90:
                    return chr(key.vk).lower()
                # 160-165 are shift/ctrl/alt
                vk_map = {
                    160: "shift",
                    161: "shift",
                    162: "ctrl",
                    163: "ctrl",
                    164: "alt",
                    165: "alt",
                }
                if key.vk in vk_map:
                    return vk_map[key.vk]
                return f"<{key.vk}>"
            return ""

        name = str(key).lower()
        if name.startswith("key."):
            name = name[4:]

        mapping = {
            "ctrl_l": "ctrl",
            "ctrl_r": "ctrl",
            "alt_l": "alt",
            "alt_r": "alt",
            "alt_gr": "alt",
            "shift_l": "shift",
            "shift_r": "shift",
            "cmd_l": "cmd",
            "cmd_r": "cmd",
        }
        return mapping.get(name, name)

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
        # We don't need to await this as it runs in its own thread in engine/audio_feedback.py
        play_sound(path, volume=sounds.volume)

    def _on_mouse_click(self, x: int, y: int):
        """Callback for mouse clicks to detect click-away."""
        if not self.is_listening or self.session_cancelled:
            return

        # In Hold Mode, we rely strictly on the hotkey release.
        # Clicks (even outside the anchor) should not cancel the session.
        if self.config.hotkeys.hold_mode:
            return

        if not self.config.interaction.cancel_on_click_outside_anchor:
            return

        if self.anchor and not self.anchor.is_match(x, y):
            logger.info(f"Click away detected at ({x}, {y}) outside anchor. Cancelling session.")
            # Trigger manual stop logic
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
            self.ui_bridge.set_state(AppState.ERROR)
            return

        logger.info(f"Starting listening with {self.config.transcription.provider}...")
        self.session_cancelled = False
        self.start_time = time.time()
        self.last_injected_text = ""

        # Capture Anchor
        if self.config.interaction.cancel_on_click_outside_anchor:
            logger.debug("Capturing anchor...")
            try:
                self.anchor = Anchor.capture_current(self.config.interaction.anchor_scope)
                logger.debug(f"Anchor captured: {self.anchor}")
            except Exception as e:
                logger.error(f"Failed to capture anchor: {e}")

            logger.debug("Starting mouse monitor...")
            try:
                self.mouse_monitor.start()
                logger.debug("Mouse monitor started.")
            except Exception as e:
                logger.error(f"Failed to start mouse monitor: {e}")

        try:
            # Ensure connection
            logger.debug("Ensuring connection...")
            await self.connection_manager.ensure_connected(is_listening=True)
            logger.debug("Connection ensured.")

            # Connect voice activity signal to UI
            self.pipeline.on_voice_activity = self.ui_bridge.update_voice_activity

            # Play start sound AFTER successful connection
            self._play_feedback_sound("start")

            if self.audio_adapter and self.provider and self.loop:
                logger.debug("Starting audio pipeline...")
                await self.pipeline.start(self.audio_adapter, self.provider, self.loop)
                logger.debug("Audio pipeline started.")
            else:
                logger.warning(
                    f"Skipping pipeline start: adapter={bool(self.audio_adapter)}, "
                    f"provider={bool(self.provider)}, loop={bool(self.loop)}"
                )

            self.input_monitor.enable_any_key_monitoring(True)
            self.set_state(AppState.LISTENING)
            logger.info("Dictation session active.")
        except Exception as e:
            logger.exception(f"Error starting transcription: {e}")
            self.set_state(AppState.ERROR)
            if "401" in str(e) or "unauthorized" in str(e).lower():
                provider_title = self.config.transcription.provider.title()
                msg = f"Invalid API Key for {provider_title}. Please check your credentials."
                self.ui_bridge.notify(msg, "Authentication Failed")

    async def stop_listening(self):
        if self.state not in (AppState.LISTENING, AppState.CONNECTING):
            return

        logger.info("Stopping listening...")
        self.set_state(AppState.STOPPING)
        self.input_monitor.enable_any_key_monitoring(False)
        self.mouse_monitor.stop()
        self.anchor = None

        # 1. Stop the pipeline
        await self.pipeline.stop()

        # 2. Stop provider if on_demand
        if self.connection_manager.is_running:
            if self.config.audio.connection_mode == "on_demand":
                await self.connection_manager.stop_provider()
            else:
                # WARM or ALWAYS_ON: start idle timer if needed
                self.connection_manager.start_idle_timer()

        # Play stop sound after everything is closed
        self._play_feedback_sound("stop")

        # 4. Clean up injection state
        self.injection_controller.injector.reset()

        self.set_state(AppState.IDLE)

    async def shutdown(self, reason: str):
        """
        Centralized, idempotent shutdown orchestration.
        Ensures all resources are released in the correct order.
        """
        async with self._shutdown_lock:
            if self.state == AppState.SHUTTING_DOWN:
                return
            self.set_state(AppState.SHUTTING_DOWN)

        logger.info(f"Initiating shutdown (reason: {reason})...")

        # Set a hard deadline for the entire shutdown sequence
        try:
            async with asyncio.timeout(10.0):
                # 1. Stop listening immediately
                logger.debug("Shutdown Step 1: Stopping listening flow...")
                await self.stop_listening()
                self.input_monitor.stop()

                await self.connection_manager.shutdown()

                # 2. Stop UI components
                if self.ui_bridge and self.loop:
                    logger.debug("Shutdown Step 2: Stopping UI...")
                    try:
                        async with asyncio.timeout(2.0):
                            # This will stop the pystray icon and join the thread
                            await self.loop.run_in_executor(None, self.ui_bridge.stop)
                    except TimeoutError:
                        logger.warning("UI stop timed out.")

                # 3. Final cleanup and loop stop
                logger.debug("Shutdown Step 3: Finalizing...")
                # Any other components that need stopping go here

        except TimeoutError:
            logger.error("Shutdown deadline (10s) exceeded! Forcing exit.")
            # Last-resort escape hatch for hangs
            import os

            os._exit(1)
        except Exception as e:
            logger.exception(f"Unexpected error during shutdown: {e}")
        finally:
            logger.info("Shutdown sequence complete.")
            # Final resource cleanup
            shutdown_logging()
            # Note: The caller or main loop handler is responsible for stopping the event loop

    def on_press(self, key):
        name = self._get_canonical_name(key)
        if not name:
            return

        self.current_keys.add(name)

        if self.target_hotkey.issubset(self.current_keys):
            if self.config.hotkeys.hold_mode:
                if not self.hotkey_pressed:
                    self.hotkey_pressed = True
                    asyncio.run_coroutine_threadsafe(self.start_listening(), self.loop)
            else:
                if not self.hotkey_pressed:
                    self.hotkey_pressed = True
                    if self.is_listening:
                        asyncio.run_coroutine_threadsafe(self.stop_listening(), self.loop)
                    else:
                        asyncio.run_coroutine_threadsafe(self.start_listening(), self.loop)

    def on_release(self, key):
        name = self._get_canonical_name(key)
        if name in self.current_keys:
            self.current_keys.remove(name)

        if name in self.target_hotkey:
            if self.hotkey_pressed:
                self.hotkey_pressed = False
                if self.config.hotkeys.hold_mode:
                    asyncio.run_coroutine_threadsafe(self.stop_listening(), self.loop)


def handle_cli():
    import argparse

    parser = argparse.ArgumentParser(
        description="Voice2Text: A real-time voice-to-text application.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global options for logging (shared by all subcommands)
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increase verbosity (Level 1 or 2)"
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress console output")
    parser.add_argument("--log-file", type=str, help="Override default log file path")
    parser.add_argument(
        "--background", action="store_true", help="Start without showing 'already running' warning"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: run (Default / GUI)
    subparsers.add_parser("run", help="Start the application tray icon (default)")

    # Command: eval (Headless)
    eval_parser = subparsers.add_parser("eval", help="Run headless evaluation mode with a WAV file")
    eval_parser.add_argument("--audio", required=True, help="Path to the input WAV file")
    eval_parser.add_argument(
        "--provider", required=True, choices=["openai", "assemblyai"], help="Transcription provider"
    )
    eval_parser.add_argument("--config", help="Path to a custom config.toml")
    eval_parser.add_argument("--chunk-ms", type=int, help="Chunk duration in ms")
    eval_parser.add_argument(
        "--timeout-seconds", type=int, default=120, help="Timeout for finalization"
    )

    # Command: set-key
    set_key_parser = subparsers.add_parser(
        "set-key", help="Set an API key securely in the Windows Credential Manager"
    )
    set_key_parser.add_argument(
        "provider",
        choices=["openai", "assemblyai"],
        help="The transcription provider (openai or assemblyai)",
    )

    # Command: config
    config_parser = subparsers.add_parser("config", help="Configuration utilities")
    config_parser.add_argument(
        "--explain", action="store_true", help="Print detailed mapping of resolved profiles"
    )

    args = parser.parse_args()

    # Default command is 'run'
    if not args.command:
        args.command = "run"

    return args


if __name__ == "__main__":
    import ctypes

    from engine.config import ConfigError, get_config_path, load_config
    from engine.platform_win.instance import SingleInstance

    cli_args = handle_cli()

    # Fail Fast for GUI mode
    if cli_args.command == "run":
        try:
            config = load_config()
            # Perform Startup Sync
            if config.interaction.run_at_startup:
                from engine.platform_win.startup import set_run_at_startup

                set_run_at_startup(True)
        except ConfigError as e:
            msg = (
                f"The application could not start because the configuration is invalid:\n\n{e}\n\n "
                "Please fix your config.toml or delete it to reset to defaults."
            )
            logger.error(f"[CONFIGURATION ERROR] {e}")
            ctypes.windll.user32.MessageBoxW(0, msg, "Configuration Error", 0x10)  # MB_ICONERROR
            sys.exit(1)

    # Single Instance Protection
    from engine.platform_win.paths import APP_NAME

    instance = SingleInstance(f"Global\\{APP_NAME}_Mutex_2026")
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

        print(f"Setting credential for {provider_name}...")
        key = ask_key(provider_name)

        if key:
            SecurityManager.set_key(account_id, key)
            print(f"Successfully saved API key for {provider_name}.")
        else:
            print("Operation cancelled.")
        sys.exit(0)

    elif cli_args.command == "config":
        from engine.config import ConfigError, explain_config, load_config

        try:
            config = load_config()
            if cli_args.explain:
                explain_config(config, verbose=cli_args.verbose)
        except ConfigError as e:
            print(f"\n[CONFIGURATION ERROR] {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    elif cli_args.command == "eval":
        from engine.eval_main import main_eval

        asyncio.run(main_eval(cli_args))

    else:  # run
        from engine.gui_main import main_gui

        try:
            asyncio.run(main_gui(cli_args))
        except KeyboardInterrupt:
            pass
