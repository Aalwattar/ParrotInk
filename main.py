import asyncio
import signal
import sys
import threading
import time
from typing import Literal, Optional, Set

from pynput import keyboard

from engine.anchor import Anchor
from engine.audio import AudioStreamer
from engine.audio_feedback import play_sound
from engine.config import Config, ConfigError, load_config
from engine.credential_ui import ask_key
from engine.indicator_ui import FloatingIndicator
from engine.injector import inject_backspaces, inject_text
from engine.interaction import InteractionMonitor
from engine.logging import configure_logging, get_logger
from engine.mouse import MouseMonitor
from engine.security import SecurityManager
from engine.transcription.base import BaseProvider
from engine.transcription.factory import TranscriptionFactory
from engine.ui import AppState, TrayApp

logger = get_logger("Main")


class AppCoordinator:
    def __init__(self, config: Config):
        self.config = config

        # Calculate chunk size from ms
        sample_rate = config.audio.capture_sample_rate
        chunk_ms = config.audio.chunk_ms
        chunk_size = (sample_rate * chunk_ms) // 1000

        self.streamer = AudioStreamer(sample_rate=sample_rate, chunk_size=chunk_size)
        self.provider: Optional[BaseProvider] = None
        self.is_listening = False
        self.is_connecting = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._audio_task: Optional[asyncio.Task] = None
        self.ui: Optional[TrayApp] = None

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

        # Floating Indicator
        self.indicator: Optional[FloatingIndicator] = None
        if self.config.ui.floating_indicator.enabled:
            ind_cfg = self.config.ui.floating_indicator
            self.indicator = FloatingIndicator(
                x=ind_cfg.x,
                y=ind_cfg.y,
                opacity_idle=ind_cfg.opacity_idle,
                opacity_active=ind_cfg.opacity_active
            )
            threading.Thread(target=self.indicator.run, daemon=True).start()

        self.session_cancelled = False
        self.start_time = 0

        # Injection safety
        self.injection_lock = asyncio.Lock()
        self.is_injecting = False
        self.last_injected_text = ""
        self.last_injection_time = 0.0

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
            # We rely strictly on the hotkey release event (handled in on_release) to stop recording.
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

        if self.loop:
            asyncio.run_coroutine_threadsafe(self._smart_inject(text), self.loop)

    def on_final(self, text: str):
        if self.session_cancelled:
            logger.debug(f"Session cancelled. Discarding final text: {text}")
            return

        text = text.strip()
        if not text:
            return

        # Ensure final text is fully synchronized and add a trailing space
        if self.loop:
            asyncio.run_coroutine_threadsafe(self._smart_inject(text + " ", is_final=True), self.loop)

    async def _smart_inject(self, text: str, is_final: bool = False):
        """Inject text using backspaces for corrections if needed."""
        if self.session_cancelled:
            return

        # De-duplicate: don't process if text hasn't changed unless it's the final signal
        if text == self.last_injected_text and not is_final:
            return

        async with self.injection_lock:
            if not self.loop:
                return

            self.is_injecting = True
            try:
                # Find common prefix length
                common_len = 0
                for i in range(min(len(self.last_injected_text), len(text))):
                    if self.last_injected_text[i] == text[i]:
                        common_len += 1
                    else:
                        break

                # Case 1: Pure Append (most common for OpenAI or stable AssemblyAI partials)
                # If everything we already typed is at the start of the new text, just type the delta.
                if common_len == len(self.last_injected_text):
                    new_text = text[common_len:]
                    if new_text:
                        logger.debug(f"Smart Inject (Append): Injecting '{new_text}'")
                        await self.loop.run_in_executor(None, inject_text, new_text)

                    if is_final:
                        if not text.endswith(" "):
                            await self.loop.run_in_executor(None, inject_text, " ")
                        self.last_injected_text = ""
                    else:
                        self.last_injected_text = text
                    return

                # Case 2: Correction (Common for AssemblyAI "Turn" updates)
                # Number of backspaces needed
                backspaces = len(self.last_injected_text) - common_len
                new_text = text[common_len:]

                if backspaces > 0:
                    # Limit backspaces to 100 to avoid runaway deletions
                    backspaces = min(backspaces, 100)
                    logger.debug(f"Smart Inject (Correct): Backspacing {backspaces} chars ('{self.last_injected_text[common_len:]}')")
                    await self.loop.run_in_executor(None, inject_backspaces, backspaces)

                if new_text:
                    logger.debug(f"Smart Inject (Correct): Injecting '{new_text}'")
                    await self.loop.run_in_executor(None, inject_text, new_text)

                # If final, we add a space to the buffer so the NEXT turn knows it's there
                if is_final:
                    if not text.endswith(" "):
                        await self.loop.run_in_executor(None, inject_text, " ")
                    self.last_injected_text = "" # Start fresh for next Turn
                else:
                    self.last_injected_text = text

            finally:
                self.last_injection_time = time.time()
                self.is_injecting = False

    async def _inject_direct(self, text: str):
        if self.session_cancelled:
            return

        async with self.injection_lock:
            if self.loop:
                self.is_injecting = True
                try:
                    # Log timing for latency debugging
                    t0 = time.perf_counter()
                    await self.loop.run_in_executor(None, inject_text, text)
                    t1 = time.perf_counter()
                    logger.debug(f"Direct injection of '{text}' took {(t1 - t0) * 1000:.2f}ms")
                finally:
                    self.last_injection_time = time.time()
                    self.is_injecting = False

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

        if not self.config.interaction.cancel_on_click_outside_anchor:
            return

        if self.anchor and not self.anchor.is_match(x, y):
            logger.info(f"Click away detected at ({x}, {y}) outside anchor. Cancelling session.")
            # Trigger manual stop logic
            if self.loop:
                asyncio.run_coroutine_threadsafe(self.stop_listening(), self.loop)

    async def start_listening(self):
        if self.is_listening or self.is_connecting:
            return

        # Credential check
        availability = self.get_provider_availability()
        if not availability.get(self.config.default_provider, False):
            logger.error(f"Missing API Key for {self.config.default_provider}")
            if self.ui:
                self.ui.notify(
                    f"Please set your {self.config.default_provider.title()} API Key in the Credentials menu.",
                    "Missing API Key",
                )
                self.ui.set_state(AppState.ERROR)
            return

        logger.info(f"Starting listening with {self.config.default_provider}...")
        self.is_connecting = True
        self.session_cancelled = False
        self.start_time = time.time()
        self.last_injected_text = ""

        # Capture Anchor
        if self.config.interaction.cancel_on_click_outside_anchor:
            self.anchor = Anchor.capture_current(self.config.interaction.anchor_scope)
            self.mouse_monitor.start()

        self.provider = TranscriptionFactory.create(
            self.config, on_partial=self.on_partial, on_final=self.on_final
        )

        try:
            await self.provider.start()

            # Play start sound AFTER successful connection
            self._play_feedback_sound("start")

            self.streamer.start()
            self.interaction_monitor.start()
            self.is_listening = True
            
            if self.indicator:
                self.indicator.set_recording(True)

            if self.ui:
                self.ui.set_state(AppState.LISTENING)
            self._audio_task = asyncio.create_task(self._audio_pipe())
        except Exception as e:
            logger.exception(f"Error starting transcription: {e}")
            self.is_listening = False
            if self.ui:
                self.ui.set_state(AppState.ERROR)
                if "401" in str(e) or "unauthorized" in str(e).lower():
                    self.ui.notify(
                        f"Invalid API Key for {self.config.default_provider.title()}. Please check your credentials.",
                        "Authentication Failed",
                    )
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
        
        if self.indicator:
            self.indicator.set_recording(False)

        if self.ui:
            self.ui.set_state(AppState.IDLE)

        # 1. Stop the streamer first
        self.streamer.stop()

        # 2. Cancel the pipe task
        if self._audio_task:
            self._audio_task.cancel()
            try:
                await self._audio_task
            except asyncio.CancelledError:
                pass
            self._audio_task = None

        # 3. Stop provider
        if self.provider:
            await self.provider.stop()
            self.provider = None

        # Play stop sound after everything is closed
        self._play_feedback_sound("stop")

        # 4. Clean up injection state
        async with self.injection_lock:
            self.last_injected_text = ""
            self.is_injecting = False

    async def _audio_pipe(self):
        # Finally the delay issue resolved by using an async generator to avoid blocking the event loop.
        async for chunk, capture_time in self.streamer.async_generator():
            if not self.is_listening or not self.provider:
                break
            await self.provider.send_audio(chunk, capture_time)

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
        description="Voice2Text: A real-time voice-to-text system tray application.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py              # Start the application tray icon
  python main.py set-key openai    # Set the OpenAI API key securely
  python main.py set-key assemblyai # Set the AssemblyAI API key securely
""",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: set-key
    set_key_parser = subparsers.add_parser(
        "set-key", help="Set an API key securely in the Windows Credential Manager"
    )
    set_key_parser.add_argument(
        "provider",
        choices=["openai", "assemblyai"],
        help="The transcription provider (openai or assemblyai)",
    )

    # Global options for logging
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increase verbosity (Level 1 or 2)"
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress console output")
    parser.add_argument("--log-file", type=str, help="Override default log file path")

    args = parser.parse_args()

    if args.command == "set-key":
        account_map = {
            "openai": ("openai_api_key", "OpenAI"),
            "assemblyai": ("assemblyai_api_key", "AssemblyAI"),
        }
        account_id, provider_name = account_map[args.provider]

        print(f"Setting credential for {provider_name}...")
        key = ask_key(provider_name)

        if key:
            SecurityManager.set_key(account_id, key)
            print(f"Successfully saved API key for {provider_name}.")
        else:
            print("Operation cancelled.")
        sys.exit(0)

    return args


async def main_async(cli_args):
    try:
        config = load_config()
    except ConfigError as e:
        print(f"\n[CONFIGURATION ERROR] {e}", file=sys.stderr)
        return

    # CLI overrides config for file path if provided
    if cli_args.log_file:
        config.logging.file_path = cli_args.log_file
        config.logging.file_enabled = True

    configure_logging(config, verbose_count=cli_args.verbose, quiet=cli_args.quiet)

    handler = ShutdownHandler()
    signal.signal(signal.SIGINT, handler.handle)

    coordinator = AppCoordinator(config)
    coordinator.loop = asyncio.get_running_loop()

    def on_quit():
        # Log indicator position if enabled for persistence awareness
        if coordinator.indicator and coordinator.indicator.root:
            try:
                x = coordinator.indicator.root.winfo_x()
                y = coordinator.indicator.root.winfo_y()
                logger.info(f"Indicator last position: ({x}, {y})")
                # In a future version, we would save this to config.toml here.
            except Exception:
                pass
        handler.should_exit = True

    def on_provider_change(provider_name):
        if coordinator.is_listening or coordinator.is_connecting:
            logger.info(f"Stopping active session before changing provider to {provider_name}")
            asyncio.run_coroutine_threadsafe(coordinator.stop_listening(), coordinator.loop)

        config.default_provider = provider_name
        logger.info(f"Provider changed to: {provider_name}")

    def on_set_key(account_id, key):
        SecurityManager.set_key(account_id, key)
        logger.info(f"API Key updated for: {account_id}")
        if coordinator.ui:
            coordinator.ui.update_availability(coordinator.get_provider_availability())
            coordinator.ui.notify(
                f"API Key for {account_id.replace('_api_key', '').title()} has been saved securely.",
                "Key Saved",
            )

    def on_toggle_sounds(enabled):
        config.interaction.sounds.enabled = enabled
        logger.info(f"Audio feedback {'enabled' if enabled else 'disabled'}")

    app = TrayApp(
        on_quit_callback=on_quit,
        on_provider_change=on_provider_change,
        on_set_key=on_set_key,
        on_toggle_sounds=on_toggle_sounds,
        initial_provider=config.default_provider,
        initial_sounds_enabled=config.interaction.sounds.enabled,
        availability=coordinator.get_provider_availability(),
    )
    coordinator.ui = app

    ui_thread = threading.Thread(target=app.run, daemon=True)
    ui_thread.start()

    listener = keyboard.Listener(on_press=coordinator.on_press, on_release=coordinator.on_release)
    listener.start()
    logger.info(
        f"Hotkey listener started: {config.hotkeys.hotkey} (hold_mode={config.hotkeys.hold_mode})"
    )

    logger.info("Application running. Press Ctrl+C twice within 3s to exit.")

    try:
        while not handler.should_exit:
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("Shutting down...")
        await coordinator.stop_listening()
        app.stop()
        await asyncio.sleep(0.5)


class ShutdownHandler:
    def __init__(self):
        self.should_exit = False
        self.last_ctrl_c = 0

    def handle(self, sig, frame):
        now = time.time()
        if now - self.last_ctrl_c < 3:
            print("\nForce Shutting down...")
            sys.exit(1)
        self.last_ctrl_c = now
        print("\nCtrl+C received. Press Ctrl+C again within 3 seconds to force exit.")
        self.should_exit = True


if __name__ == "__main__":
    from engine.config import migrate_config_file

    migrate_config_file("config.toml")

    cli_args = handle_cli()
    try:
        asyncio.run(main_async(cli_args))
    except KeyboardInterrupt:
        pass
