import os
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

import pystray
from PIL import Image, ImageDraw

from .credential_ui import ask_key
from .logging import get_logger
from .types import AppState, ProviderType

if TYPE_CHECKING:
    from .ui_bridge import UIBridge

logger = get_logger("UI")


class TrayApp:
    def __init__(
        self,
        bridge: Optional["UIBridge"] = None,
        on_quit_callback: Callable | None = None,
        on_provider_change: Callable[[ProviderType], None] | None = None,
        on_set_key: Callable[[str, str], None] | None = None,
        on_toggle_sounds: Callable[[bool], None] | None = None,
        initial_provider: ProviderType = "openai",
        initial_sounds_enabled: bool = True,
        availability: Optional[dict[str, bool]] = None,
    ):
        self.bridge = bridge
        self.state = AppState.IDLE
        self.default_provider: ProviderType = initial_provider
        self.sounds_enabled = initial_sounds_enabled
        self.on_quit_callback = on_quit_callback
        self.on_provider_change = on_provider_change
        self.on_set_key = on_set_key
        self.on_toggle_sounds = on_toggle_sounds
        self.availability = availability or {"openai": True, "assemblyai": True}

        self.icon = self._create_icon()
        self._stop_event = threading.Event()

    def _create_image(self, color: str) -> Image.Image:
        width, height = 64, 64
        image = Image.new("RGB", (width, height), "white")
        dc = ImageDraw.Draw(image)
        dc.ellipse((8, 8, 56, 56), fill=color)
        return image

    def _get_icon_color(self, state: AppState) -> str:
        if state == AppState.LISTENING:
            return "red"
        if state == AppState.ERROR:
            return "orange"
        return "black"

    def _on_provider_selection(self, icon: pystray.Icon, provider: ProviderType) -> None:
        self.default_provider = provider
        if self.on_provider_change:
            self.on_provider_change(provider)

    def _on_toggle_sounds_clicked(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.sounds_enabled = not self.sounds_enabled
        if self.on_toggle_sounds:
            self.on_toggle_sounds(self.sounds_enabled)

    def _on_set_key_clicked(self, provider_id: str, provider_name: str):
        # We launch this in a thread because showing a dialog (console or GUI)
        # from the pystray callback might block the tray icon loop or not work well.
        def prompt():
            key = ask_key(provider_name)
            if key and self.on_set_key:
                self.on_set_key(provider_id, key)

        threading.Thread(target=prompt, daemon=True).start()

    def _open_config(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        # Check current dir first
        config_path = Path("config.toml").absolute()
        if config_path.exists():
            os.startfile(config_path)
        else:
            print(f"Config file not found at: {config_path}")

    def _create_icon(self) -> pystray.Icon:
        menu = pystray.Menu(
            pystray.MenuItem(
                "OpenAI",
                lambda icon, item: self._on_provider_selection(icon, "openai"),
                checked=lambda item: self.default_provider == "openai",
                enabled=lambda item: self.availability.get("openai", True),
                radio=True,
            ),
            pystray.MenuItem(
                "AssemblyAI",
                lambda icon, item: self._on_provider_selection(icon, "assemblyai"),
                checked=lambda item: self.default_provider == "assemblyai",
                enabled=lambda item: self.availability.get("assemblyai", True),
                radio=True,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Credentials",
                pystray.Menu(
                    pystray.MenuItem(
                        "Set OpenAI Key...",
                        lambda: self._on_set_key_clicked("openai_api_key", "OpenAI"),
                    ),
                    pystray.MenuItem(
                        "Set AssemblyAI Key...",
                        lambda: self._on_set_key_clicked("assemblyai_api_key", "AssemblyAI"),
                    ),
                ),
            ),
            pystray.MenuItem(
                "Settings",
                pystray.Menu(
                    pystray.MenuItem(
                        "Enable Audio Feedback",
                        self._on_toggle_sounds_clicked,
                        checked=lambda item: self.sounds_enabled,
                    ),
                ),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open Config", self._open_config),
            pystray.MenuItem("Quit", self.stop),
        )

        return pystray.Icon(
            "voice2text", self._create_image(self._get_icon_color(self.state)), "Voice2Text", menu
        )

    def set_state(self, state: AppState) -> None:
        self.state = state
        self.icon.icon = self._create_image(self._get_icon_color(state))

    def update_availability(self, availability: dict[str, bool]):
        """Updates the availability status of providers."""
        self.availability = availability

    def notify(self, message: str, title: str = "Voice2Text"):
        """Show a system tray notification."""
        self.icon.notify(message, title)

    def _poll_bridge(self):
        """Polls the UI bridge for events and updates the icon."""
        if not self.bridge:
            return

        from .ui_bridge import UIEvent

        while not self._stop_event.is_set():
            event = self.bridge.get_event(block=True, timeout=0.5)
            if not event:
                continue

            msg_type, data = event
            if msg_type == UIEvent.SET_STATE:
                self.set_state(data)
            elif msg_type == UIEvent.NOTIFY:
                message, title = data
                self.notify(message, title)
            elif msg_type == UIEvent.UPDATE_AVAILABILITY:
                self.update_availability(data)
            elif msg_type == UIEvent.QUIT:
                logger.info("UI received QUIT signal via bridge.")
                self.stop()

    def run(self) -> None:
        if self.bridge:
            threading.Thread(target=self._poll_bridge, daemon=True).start()
        self.icon.run()

    def stop(self) -> None:
        print("\nShutting down UI...", flush=True)
        self._stop_event.set()
        self.icon.stop()

        callback = self.on_quit_callback
        self.on_quit_callback = None  # Prevent recursion
        if callback:
            callback()
