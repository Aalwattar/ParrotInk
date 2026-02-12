from __future__ import annotations

import asyncio
import sys
import time
from typing import Literal, Optional, Set

from pynput import keyboard

from engine.anchor import Anchor
from engine.app_types import AppState
from engine.audio import AudioStreamer
from engine.audio.adapter import AudioAdapter
from engine.audio_feedback import play_sound
from engine.config import Config
from engine.credential_ui import ask_key
from engine.injector import SmartInjector, inject_text
from engine.interaction import InteractionMonitor
from engine.logging import get_logger
from engine.mouse import MouseMonitor
from engine.security import SecurityManager
from engine.transcription.base import BaseProvider
from engine.transcription.factory import TranscriptionFactory
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
        self.provider: Optional[BaseProvider] = None
        self.audio_adapter: Optional[AudioAdapter] = None
        self.is_listening = False
        self.is_connecting = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._audio_task: Optional[asyncio.Task] = None

        # Hotkey state
        self.hotkey_pressed = False
        self.target_hotkey = self._parse_hotkey(config.hotkeys.hotkey)
        self.current_keys: Set[str] = set()

        # Interaction monitoring
        self.interaction_monitor = InteractionMonitor()
        self.interaction_monitor.set_any_key_callback(self._on_manual_stop)

        # Mouse monitoring for click-away
        self.mouse_monitor = MouseMonitor(on_click_event=self._on_mouse_click)
        self.anchor: Optional[Anchor] = None

        self.session_cancelled = False
        self.start_time = 0

        # Injection safety
        self.injection_lock = asyncio.Lock()
        self.injector = SmartInjector()
        self.is_injecting = False  # Restored flag
        self.last_injection_time = 0.0

        # Shutdown orchestration
        self._shutdown_lock = asyncio.Lock()
        self._is_shutting_down = False

        # Connection lifecycle
        self._last_activity_time = 0.0
        self._idle_timer_task: Optional[asyncio.Task] = None
        self._session_start_time = 0.0
        self._rotation_pending = False
        self._backoff_delay = 1.0
        self._last_fail_time = 0.0

        logger.debug(f"Target hotkey set to: {self.target_hotkey}")

    def get_provider_availability(self) -> dict[str, bool]:
        """Returns a mapping of provider names to their availability status."""
        if self.config.test.enabled:
            return {"openai": True, "assemblyai": True}

        return {
            "openai": bool(self.config.get_openai_key()),
            "assemblyai": bool(self.config.get_assemblyai_key()),
        }

    def _on_manual_stop(self, key=None):
        """Callback for when a manual key press is detected during listening."""
        # Cooldown to avoid catching the release/repeat of the hotkey itself
        now = time.time()
        if now - self.start_time < 0.5:
            return

        # Ignore keyboard events if they are coming from our own injection
        # Increase safety window to 0.5s to account for system lag in event delivery
        if self.is_injecting or (now - self.last_injection_time < 0.5):
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
            asyncio.run_coroutine_threadsafe(self._smart_inject(text), self.loop)

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
                self._smart_inject(text + " ", is_final=True), self.loop
            )

    async def _smart_inject(self, text: str, is_final: bool = False):
        """Inject text using the stateful injector."""
        if self.session_cancelled:
            return

        async with self.injection_lock:
            if not self.loop:
                return

            self.is_injecting = True
            try:
                # Note: SmartInjector handles its own delta calculation
                await self.loop.run_in_executor(None, self.injector.inject, text, is_final)
            finally:
                self.is_injecting = False
                self.last_injection_time = time.time()

    async def _delayed_inject(self, text: str):
        if self.session_cancelled:
            return

        async with self.injection_lock:
            if self.loop:
                logger.debug(f"Injecting text: {text}")
                t0 = time.perf_counter()
                await self.loop.run_in_executor(None, inject_text, text)
                t1 = time.perf_counter()
                logger.debug(f"Injection call completed in {(t1 - t0) * 1000:.2f}ms")

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

    async def ensure_connected(self):
        """
        Idempotent connection management.
        Ensures the provider is connected based on connection_mode.
        """
        if self.provider and self.provider.is_running:
            # Check for rotation
            if self.config.default_provider == "openai":
                age = time.time() - self._session_start_time
                if age > 3300:  # 55 minutes
                    if self.is_listening:
                        if not self._rotation_pending:
                            logger.info("Session age > 55m, marking rotation pending.")
                            self._rotation_pending = True
                    else:
                        logger.info("Rotating OpenAI session due to age.")
                        await self.provider.stop()
                        self.provider = None
                        # Fall through to reconnect
                elif self._rotation_pending and not self.is_listening:
                    logger.info("Performing pending OpenAI session rotation.")
                    await self.provider.stop()
                    self.provider = None
                    self._rotation_pending = False
                    # Fall through to reconnect

            # NEW: Check if provider type matches configuration
            if self.provider and self.provider.get_type() != self.config.default_provider:
                logger.info(
                    f"Provider type mismatch ({self.provider.get_type()} != "
                    f"{self.config.default_provider}). Reconnecting..."
                )
                if not self.is_listening:
                    await self.provider.stop()
                    self.provider = None
                    # Fall through to reconnect
                else:
                    # If listening, we can't switch safely mid-stream without losing data.
                    # Usually on_provider_change handles this, but as a safety:
                    pass

        if self.provider and self.provider.is_running:
            return

        # Initialize provider if not exists
        if not self.provider:
            self.provider = TranscriptionFactory.create(
                self.config, on_partial=self.on_partial, on_final=self.on_final
            )
            self.audio_adapter = AudioAdapter(
                capture_rate_hz=self.config.audio.capture_sample_rate,
                provider_spec=self.provider.get_audio_spec(),
            )

        # Connect
        # Exponential backoff check
        now = time.time()
        time_since_fail = now - self._last_fail_time
        if time_since_fail < self._backoff_delay:
            wait_time = self._backoff_delay - time_since_fail
            logger.warning(f"Connection backoff active. Waiting {wait_time:.1f}s...")
            await asyncio.sleep(wait_time)

        logger.info(f"Connecting to {self.config.default_provider}...")
        self.is_connecting = True
        try:
            async with asyncio.timeout(10.0):
                await self.provider.start()
            self._session_start_time = time.time()
            self._rotation_pending = False
            self._backoff_delay = 1.0  # Reset on success
            logger.info("Connected successfully.")
        except Exception as e:
            self._last_fail_time = time.time()
            # Max 60s backoff
            self._backoff_delay = min(self._backoff_delay * 2, 60.0)
            logger.error(f"Failed to connect (backoff updated to {self._backoff_delay}s): {e}")
            self.provider = None
            self.audio_adapter = None
            raise
        finally:
            self.is_connecting = False

    async def start_listening(self):
        if self.is_listening or self.is_connecting:
            return

        # Credential check
        availability = self.get_provider_availability()
        if not availability.get(self.config.default_provider, False):
            logger.error(f"Missing API Key for {self.config.default_provider}")
            provider_title = self.config.default_provider.title()
            msg = f"Please set your {provider_title} API Key in the Credentials menu."
            self.ui_bridge.notify(msg, "Missing API Key")
            self.ui_bridge.set_state(AppState.ERROR)
            return

        logger.info(f"Starting listening with {self.config.default_provider}...")
        self.is_connecting = True
        self.session_cancelled = False
        self.start_time = time.time()
        self.last_injected_text = ""

        # Cancel idle timer if running
        if self._idle_timer_task:
            self._idle_timer_task.cancel()
            self._idle_timer_task = None

        # Capture Anchor
        if self.config.interaction.cancel_on_click_outside_anchor:
            self.anchor = Anchor.capture_current(self.config.interaction.anchor_scope)
            self.mouse_monitor.start()

        try:
            # Ensure connection
            await self.ensure_connected()

            # Play start sound AFTER successful connection
            self._play_feedback_sound("start")

            self.streamer.start(loop=self.loop)
            self.interaction_monitor.start()
            self.is_listening = True

            self.ui_bridge.set_state(AppState.LISTENING)
            self._audio_task = asyncio.create_task(self._audio_pipe())
        except Exception as e:
            logger.exception(f"Error starting transcription: {e}")
            self.is_listening = False
            self.ui_bridge.set_state(AppState.ERROR)
            if "401" in str(e) or "unauthorized" in str(e).lower():
                provider_title = self.config.default_provider.title()
                msg = f"Invalid API Key for {provider_title}. Please check your credentials."
                self.ui_bridge.notify(msg, "Authentication Failed")
        finally:
            self.is_connecting = False

    async def stop_listening(self):
        if not self.is_listening and not self.is_connecting:
            return

        logger.info("Stopping listening...")
        self.is_listening = False
        self.is_connecting = False
        self.interaction_monitor.stop()
        self.mouse_monitor.stop()
        self.anchor = None

        self.ui_bridge.set_state(AppState.IDLE)

        # 1. Stop the streamer first
        try:
            self.streamer.stop()
        except Exception as e:
            logger.error(f"Error stopping streamer: {e}")

        # 2. Cancel the pipe task
        if self._audio_task:
            self._audio_task.cancel()
            try:
                await self._audio_task
            except asyncio.CancelledError:
                pass
            self._audio_task = None

        # 3. Stop provider if on_demand
        if self.provider:
            if self.config.audio.connection_mode == "on_demand":
                try:
                    async with asyncio.timeout(5.0):
                        await self.provider.stop()
                except Exception as e:
                    logger.error(f"Error stopping provider ({type(e).__name__}): {e}")

                if self.audio_adapter:
                    self.audio_adapter.close()

                self.provider = None
                self.audio_adapter = None
            else:
                # WARM or ALWAYS_ON: start idle timer if needed
                self._last_activity_time = time.time()
                if self.config.audio.connection_mode == "warm":
                    self._idle_timer_task = asyncio.create_task(self._idle_timer_check())

        # Play stop sound after everything is closed
        self._play_feedback_sound("stop")

        # 4. Clean up injection state
        async with self.injection_lock:
            self.last_injected_text = ""
            self.is_injecting = False

    async def shutdown(self, reason: str):
        """
        Centralized, idempotent shutdown orchestration.
        Ensures all resources are released in the correct order.
        """
        async with self._shutdown_lock:
            if self._is_shutting_down:
                return
            self._is_shutting_down = True

        logger.info(f"Initiating shutdown (reason: {reason})...")

        # Set a hard deadline for the entire shutdown sequence
        try:
            async with asyncio.timeout(10.0):
                # 1. Stop listening immediately
                logger.debug("Shutdown Step 1: Stopping listening flow...")
                await self.stop_listening()

                if self.provider:
                    await self.provider.stop()
                    self.provider = None

                if self.audio_adapter:
                    self.audio_adapter.close()
                    self.audio_adapter = None

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
            # Note: The caller or main loop handler is responsible for stopping the event loop

    async def _idle_timer_check(self):
        """Task that waits for idle timeout and closes connection."""
        timeout = self.config.audio.warm_idle_timeout_seconds
        try:
            await asyncio.sleep(timeout)
            # Check if there was activity while we were sleeping
            if time.time() - self._last_activity_time >= timeout:
                if self.provider and self.provider.is_running and not self.is_listening:
                    logger.info(f"Closing warm connection after {timeout}s idle.")
                    await self.provider.stop()
                    if self.audio_adapter:
                        self.audio_adapter.close()
                    self.provider = None
                    self.audio_adapter = None
        except asyncio.CancelledError:
            pass

    async def _audio_pipe(self):
        # Finally the delay issue resolved by using an async generator
        # to avoid blocking the event loop.
        try:
            async for chunk, capture_time in self.streamer.async_generator():
                # STRICT INVARIANT: Never send audio unless in LISTENING state
                if not self.is_listening:
                    continue

                if not self.provider or not self.audio_adapter:
                    break

                processed = self.audio_adapter.process(chunk)
                await self.provider.send_audio(processed, capture_time)
        except Exception as e:
            logger.exception(f"Error in audio pipe: {e}")

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

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: run (Default / GUI)
    subparsers.add_parser("run", help="Start the application tray icon (default)")

    # Command: eval (Headless)
    eval_parser = subparsers.add_parser(
        "eval", help="Run headless evaluation mode with a WAV file"
    )
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

    args = parser.parse_args()

    # Default command is 'run'
    if not args.command:
        args.command = "run"

    return args


if __name__ == "__main__":
    from engine.config import migrate_config_file

    migrate_config_file("config.toml")

    cli_args = handle_cli()

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

    elif cli_args.command == "eval":
        from engine.eval_main import main_eval
        asyncio.run(main_eval(cli_args))

    else:  # run
        from engine.gui_main import main_gui
        try:
            asyncio.run(main_gui(cli_args))
        except KeyboardInterrupt:
            pass
