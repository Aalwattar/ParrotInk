import os
import threading
from enum import Enum
from pathlib import Path
from typing import Callable, Literal, Optional

import pystray
from PIL import Image, ImageDraw

from .credential_ui import ask_key


class AppState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    ERROR = "error"


ProviderType = Literal["openai", "assemblyai"]


class TrayApp:
    def __init__(
        self,
        on_quit_callback: Callable | None = None,
        on_provider_change: Callable[[ProviderType], None] | None = None,
        on_set_key: Callable[[str, str], None] | None = None,
        on_toggle_sounds: Callable[[bool], None] | None = None,
        initial_provider: ProviderType = "openai",
        initial_sounds_enabled: bool = True,
        availability: Optional[dict[str, bool]] = None,
    ):
        self.state = AppState.IDLE
        self.default_provider: ProviderType = initial_provider
        self.sounds_enabled = initial_sounds_enabled
        self.on_quit_callback = on_quit_callback
        self.on_provider_change = on_provider_change
        self.on_set_key = on_set_key
        self.on_toggle_sounds = on_toggle_sounds
        self.availability = availability or {"openai": True, "assemblyai": True}

        self.icon = self._create_icon()

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

    def run(self) -> None:
        self.icon.run()

    def stop(self) -> None:
        print("\nShutting down UI...", flush=True)
        self.icon.stop()

        callback = self.on_quit_callback
        self.on_quit_callback = None  # Prevent recursion
        if callback:
            callback()
