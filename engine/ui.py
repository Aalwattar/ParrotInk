import os
import threading
from enum import Enum
from pathlib import Path
from typing import Callable, Literal, Optional

import pystray
from PIL import Image, ImageDraw
from .security import CredentialDialog


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
        initial_provider: ProviderType = "openai",
    ):
        self.state = AppState.IDLE
        self.active_provider: ProviderType = initial_provider
        self.on_quit_callback = on_quit_callback
        self.on_provider_change = on_provider_change
        self.on_set_key = on_set_key

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
        self.active_provider = provider
        if self.on_provider_change:
            self.on_provider_change(provider)

    def _on_set_key_clicked(self, provider_id: str, provider_name: str):
        key = CredentialDialog.ask_key(provider_name)
        if key and self.on_set_key:
            self.on_set_key(provider_id, key)

    def _open_config(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        # Check current dir first
        config_path = Path("config.toml").absolute()
        if config_path.exists():
            os.startfile(config_path)
        else:
            print(f"Config file not found at: {config_path}")

    def _create_icon(self) -> pystray.Icon:
        menu = pystray.Menu(
            pystray.MenuItem("Status: Ready", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "OpenAI",
                lambda icon, item: self._on_provider_selection(icon, "openai"),
                checked=lambda item: self.active_provider == "openai",
                radio=True,
            ),
            pystray.MenuItem(
                "AssemblyAI",
                lambda icon, item: self._on_provider_selection(icon, "assemblyai"),
                checked=lambda item: self.active_provider == "assemblyai",
                radio=True,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Credentials", pystray.Menu(
                pystray.MenuItem("Set OpenAI Key...", lambda: self._on_set_key_clicked("openai_api_key", "OpenAI")),
                pystray.MenuItem("Set AssemblyAI Key...", lambda: self._on_set_key_clicked("assemblyai_api_key", "AssemblyAI")),
            )),
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