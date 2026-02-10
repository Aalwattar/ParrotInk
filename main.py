import asyncio
import signal
import sys
import argparse
import threading
import time
from typing import Optional, Set

from pynput import keyboard

from engine.audio import AudioStreamer
from engine.config import Config, ConfigError, load_config
from engine.injector import inject_text
from engine.interaction import InteractionMonitor
from engine.signals import ShutdownHandler
from engine.transcription import BaseProvider, TranscriptionFactory
from engine.ui import AppState, TrayApp
from engine.security import SecurityManager
from engine.credential_ui import ask_key
from engine.logging import get_logger, configure_logging

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
        self.ui: Optional[TrayApp] = None

        # Hotkey state
        self.hotkey_pressed = False
        self.target_hotkey = self._parse_hotkey(config.hotkeys.hotkey)
        self.current_keys: Set[str] = set()

        # Interaction monitoring
        self.interaction_monitor = InteractionMonitor()
        self.interaction_monitor.set_any_key_callback(self._on_manual_stop)
        self.session_cancelled = False
        self.start_time = 0

        # Injection safety
        self.injection_lock = asyncio.Lock()
        self.last_partial = ""

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
        if time.time() - self.start_time < 0.2: # Reduced cooldown, more responsive
            return

        if key:
            name = self._get_canonical_name(key)
            # If the key is part of our hotkey, ignore it.
            # We also check if it's currently in current_keys which is managed by the hotkey listener
            if name in self.target_hotkey:
                return

        # Ignore keyboard events if they are coming from our own injection
        # Also ensure we are actually listening and not just in the process of starting
        if self.is_listening and not self.is_connecting and not self.injection_lock.locked():
            logger.info(f"Manual key press detected ({key}). Stopping and cancelling injection...")
            self.session_cancelled = True
            if self.loop:
                asyncio.run_coroutine_threadsafe(self.stop_listening(), self.loop)

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
                return key.char.lower()
            if key.vk:
                # 65-90 are A-Z
                if 65 <= key.vk <= 90:
                    return chr(key.vk).lower()
                # 160-165 are shift/ctrl/alt
                vk_map = {
                    160: "shift", 161: "shift",
                    162: "ctrl", 163: "ctrl",
                    164: "alt", 165: "alt",
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

        # In this new mode, providers send DELTAS, so we inject them directly
        if text:
            if self.loop:
                asyncio.run_coroutine_threadsafe(self._inject_direct(text), self.loop)

    def on_final(self, text: str):
        if self.session_cancelled:
            logger.debug(f"Session cancelled. Discarding final text: {text}")
            return

        # Since we are injecting deltas, we need to be careful with on_final.
        # Most providers send 'completed' which might contain the FULL text.
        # But if we already injected parts of it, we don't want to re-inject.
        
        # For now, let's just add the final space.
        if self.loop:
            asyncio.run_coroutine_threadsafe(self._inject_direct(" "), self.loop)

    async def _inject_direct(self, text: str):
        """Immediate injection without delay."""
        if self.session_cancelled:
            return
        
        async with self.injection_lock:
            if self.loop:
                await self.loop.run_in_executor(None, inject_text, text)

    async def _delayed_inject(self, text: str):
        # We removed the sleep here to achieve real-time speed.
        # Check if session was cancelled
        if self.session_cancelled:
            return

        # Use a lock to prevent overlapping injections
        if self.injection_lock.locked():
            logger.warning(f"Injection busy. Queuing text: {text}")
            # Even if busy, we want the lock to handle it rather than dropping it
            # but for partials, dropping older ones is often fine.
            # For simplicity, we'll keep the lock check but make it fast.

        async with self.injection_lock:
            if self.loop:
                t0 = time.perf_counter()
                await self.loop.run_in_executor(None, inject_text, text)
                t1 = time.perf_counter()
                logger.debug(f"Coordinator handoff to injector took {(t1-t0)*1000:.2f}ms")

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

        self.provider = TranscriptionFactory.create(
            self.config, on_partial=self.on_partial, on_final=self.on_final
        )

        try:
            await self.provider.start()
            self.streamer.start()
            self.interaction_monitor.start()
            self.is_listening = True
            if self.ui:
                self.ui.set_state(AppState.LISTENING)
            asyncio.create_task(self._audio_pipe())
        except Exception as e:
            logger.exception(f"Error starting transcription: {e}")
            self.is_listening = False
            if self.ui:
                self.ui.set_state(AppState.ERROR)
                if "401" in str(e) or "unauthorized" in str(e).lower():
                     self.ui.notify(f"Invalid API Key for {self.config.default_provider.title()}. Please check your credentials.", "Authentication Failed")
        finally:
            self.is_connecting = False

    async def stop_listening(self):
        if not self.is_listening:
            return

        logger.info("Stopping listening...")
        self.is_listening = False
        self.interaction_monitor.stop()

        if self.ui:
            self.ui.set_state(AppState.IDLE)

        self.streamer.stop()
        if self.provider:
            await self.provider.stop()
            self.provider = None

    async def _audio_pipe(self):
        for chunk in self.streamer.generator():
            if not self.is_listening or not self.provider:
                break
            await self.provider.send_audio(chunk)

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
            "assemblyai": ("assemblyai_api_key", "AssemblyAI")
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
        handler.should_exit = True

    def on_provider_change(provider_name):
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

    app = TrayApp(
        on_quit_callback=on_quit,
        on_provider_change=on_provider_change,
        on_set_key=on_set_key,
        initial_provider=config.default_provider,
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


if __name__ == "__main__":


    from engine.config import migrate_config_file


    migrate_config_file("config.toml")





    cli_args = handle_cli()


    try:


        asyncio.run(main_async(cli_args))


    except KeyboardInterrupt:


        pass

