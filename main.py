import asyncio
import signal
import sys
import threading
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


class AppCoordinator:
    def __init__(self, config: Config):
        self.config = config
        self.streamer = AudioStreamer(sample_rate=config.transcription.sample_rate)
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

        # Injection safety
        self.injection_lock = asyncio.Lock()

        print(f"DEBUG: Target hotkey set to: {self.target_hotkey}")

    def _on_manual_stop(self):
        """Callback for when a manual key press is detected during listening."""
        # Ignore keyboard events if they are coming from our own injection
        if self.is_listening and not self.injection_lock.locked():
            print("\n[EVENT] Manual key press detected. Stopping and cancelling injection...")
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
                if 65 <= key.vk <= 90:
                    return chr(key.vk).lower()
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
        pass

    def on_final(self, text: str):
        if self.session_cancelled:
            print(f"[DEBUG] Session cancelled. Discarding final text: {text}")
            return

        if self.loop:
            asyncio.run_coroutine_threadsafe(self._delayed_inject(text), self.loop)

    async def _delayed_inject(self, text: str):
        # Wait a bit for the user to release keys (Ctrl/Alt) to avoid shortcut interference
        await asyncio.sleep(0.3)

        # Check again after sleep in case session was cancelled during delay
        if self.session_cancelled:
            return

        # Use a lock to prevent overlapping injections
        if self.injection_lock.locked():
            print("[WARN] Injection skipped: Previous injection still in progress.")
            return

        async with self.injection_lock:
            # Run injection in executor because it blocks (calls sleep)
            if self.loop:
                await self.loop.run_in_executor(None, inject_text, text)

    async def start_listening(self):
        if self.is_listening or self.is_connecting:
            return

        # Credential check
        key = None
        if self.config.active_provider == "openai":
            key = self.config.get_openai_key()
        elif self.config.active_provider == "assemblyai":
            key = self.config.get_assemblyai_key()
            
        if not key and not self.config.test.enabled:
            print(f"\n[ERROR] Missing API Key for {self.config.active_provider}")
            if self.ui:
                self.ui.notify(f"Please set your {self.config.active_provider.title()} API Key in the Credentials menu.", "Missing API Key")
                self.ui.set_state(AppState.ERROR)
            return

        print(f"\n[EVENT] Starting listening with {self.config.active_provider}...")
        self.is_connecting = True
        self.session_cancelled = False

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
            print(f"Error starting transcription: {e}")
            self.is_listening = False
            if self.ui:
                self.ui.set_state(AppState.ERROR)
                if "401" in str(e) or "unauthorized" in str(e).lower():
                     self.ui.notify(f"Invalid API Key for {self.config.active_provider.title()}. Please check your credentials.", "Authentication Failed")
        finally:
            self.is_connecting = False

    async def stop_listening(self):
        if not self.is_listening:
            return

        print("\n[EVENT] Stopping listening...")
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


async def main_async():
    try:
        config = load_config()
    except ConfigError as e:
        print(f"\n[CONFIGURATION ERROR] {e}", file=sys.stderr)
        return

    handler = ShutdownHandler()
    signal.signal(signal.SIGINT, handler.handle)

    coordinator = AppCoordinator(config)
    coordinator.loop = asyncio.get_running_loop()

    def on_quit():
        handler.should_exit = True

    def on_provider_change(provider_name):
        config.active_provider = provider_name
        print(f"\nProvider changed to: {provider_name}")

    def on_set_key(account_id, key):
        SecurityManager.set_key(account_id, key)
        print(f"\nAPI Key updated for: {account_id}")
        if coordinator.ui:
            coordinator.ui.notify(f"API Key for {account_id.replace('_api_key', '').title()} has been saved securely.", "Key Saved")

    app = TrayApp(
        on_quit_callback=on_quit,
        on_provider_change=on_provider_change,
        on_set_key=on_set_key,
        initial_provider=config.active_provider,
    )
    coordinator.ui = app

    ui_thread = threading.Thread(target=app.run, daemon=True)
    ui_thread.start()

    listener = keyboard.Listener(on_press=coordinator.on_press, on_release=coordinator.on_release)
    listener.start()
    print(
        f"Hotkey listener started: {config.hotkeys.hotkey} (hold_mode={config.hotkeys.hold_mode})"
    )

    print("Application running. Press Ctrl+C twice within 3s to exit.")

    try:
        while not handler.should_exit:
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        pass
    finally:
        print("\nShutting down...")
        await coordinator.stop_listening()
        app.stop()
        await asyncio.sleep(0.5)


if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        pass