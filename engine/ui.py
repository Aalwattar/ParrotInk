from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Callable, Dict, Optional

import pystray
from PIL import Image, ImageDraw

from engine.app_types import AppState
from engine.indicator_ui import IndicatorWindow
from engine.logging import get_logger
from engine.ui_utils import get_resource_path

logger = get_logger("UI")


class TrayApp:
    """
    Manages the system tray icon and its menu.
    """

    def __init__(
        self,
        config,
        bridge=None,
        on_quit_callback: Optional[Callable[[], None]] = None,
        on_provider_change: Optional[Callable[[str], None]] = None,
        on_set_key: Optional[Callable[[str, str], None]] = None,
        on_toggle_sounds: Optional[Callable[[bool], None]] = None,
        on_hotkey_change: Optional[Callable[[str], None]] = None,
        on_before_hotkey_change: Optional[Callable[[], None]] = None,
        on_toggle_hud: Optional[Callable[[bool], None]] = None,
        on_toggle_click_through: Optional[Callable[[bool], None]] = None,
        on_toggle_startup: Optional[Callable[[bool], None]] = None,
        on_toggle_hold_mode: Optional[Callable[[bool], None]] = None,
        on_open_config: Optional[Callable[[], None]] = None,
        initial_provider: str = "openai",
        initial_sounds_enabled: bool = True,
        availability: Optional[Dict[str, bool]] = None,
    ):
        self.config = config
        self.bridge = bridge
        self.on_quit = on_quit_callback
        self.on_provider_change = on_provider_change
        self.on_set_key = on_set_key
        self.on_toggle_sounds = on_toggle_sounds
        self.on_hotkey_change = on_hotkey_change
        self.on_before_hotkey_change = on_before_hotkey_change
        self.on_toggle_hud = on_toggle_hud
        self.on_toggle_click_through = on_toggle_click_through
        self.on_toggle_startup = on_toggle_startup
        self.on_toggle_hold_mode = on_toggle_hold_mode
        self.on_open_config = on_open_config

        self._state = AppState.IDLE
        self._provider_availability = availability or {}
        self._sounds_enabled = initial_sounds_enabled
        self.current_provider = initial_provider

        # Initialize the icon early for tests
        image = self._create_image(self._get_icon_color(self._state))
        self.icon = pystray.Icon("voice2text", image, "Voice2Text", self._create_menu())

        # HUD Indicator
        self.indicator: Optional[IndicatorWindow] = None
        if config.ui.floating_indicator.enabled:
            self.indicator = IndicatorWindow(config=config)

        self._stop_event = threading.Event()

    @property
    def state(self) -> AppState:
        return self._state

    @property
    def availability(self) -> dict[str, bool]:
        return self._provider_availability

    @property
    def sounds_enabled(self) -> bool:
        return self._sounds_enabled

    def _get_icon_color(self, state: AppState) -> str:
        if state == AppState.LISTENING:
            return "#0078D4"  # Fluent Blue
        elif state == AppState.ERROR:
            return "#EF4444"  # Fluent Red
        return "#475569"  # Slate Gray

    def _create_image(self, color: Optional[str] = None) -> Image.Image:
        """Loads the tray icon image or creates a rounded rectangle."""
        if color:
            width, height = 64, 64
            image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.rounded_rectangle([4, 4, 60, 60], radius=12, fill=color)
            return image

        icon_path = get_resource_path("assets/icon.png")
        try:
            return Image.open(icon_path)
        except Exception:
            return self._create_image(self._get_icon_color(self._state))

    def _create_menu(self):
        from engine.ui_utils import get_app_version

        version = get_app_version()

        def get_provider_label(provider_id: str, display_name: str):
            return display_name

        return pystray.Menu(
            pystray.MenuItem(f"Voice2Text v{version}", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                get_provider_label("openai", "OpenAI"),
                lambda: self.on_set_key("openai", None) if self.on_set_key else None,
            ),
            pystray.MenuItem(
                get_provider_label("assemblyai", "AssemblyAI"),
                lambda: self.on_set_key("assemblyai", None) if self.on_set_key else None,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Set Hotkey", self.on_before_hotkey_change or self.on_hotkey_change),
            pystray.MenuItem(
                "Settings",
                pystray.Menu(
                    pystray.MenuItem(
                        "Hold to Talk",
                        self._on_toggle_hold_mode_clicked,
                        checked=lambda _: self.config.hotkeys.hold_mode,
                    ),
                    pystray.MenuItem(
                        "Enable Audio Feedback",
                        self._on_toggle_sounds_clicked,
                        checked=lambda _: self._sounds_enabled,
                    ),
                    pystray.MenuItem("Open Config File", self._open_config),
                ),
            ),
            pystray.MenuItem(
                "Select Provider",
                pystray.Menu(
                    pystray.MenuItem(
                        "OpenAI",
                        lambda icon, item: self._on_provider_selection(icon, "openai"),
                        checked=lambda _: self.current_provider == "openai",
                    ),
                    pystray.MenuItem(
                        "AssemblyAI",
                        lambda icon, item: self._on_provider_selection(icon, "assemblyai"),
                        checked=lambda _: self.current_provider == "assemblyai",
                    ),
                ),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.on_quit),
        )

    def _on_provider_selection(self, icon, provider_id: str):
        self.current_provider = provider_id
        if self.on_provider_change:
            self.on_provider_change(provider_id)

    def _on_toggle_sounds_clicked(self, icon, item):
        self._sounds_enabled = not self._sounds_enabled
        if self.on_toggle_sounds:
            self.on_toggle_sounds(self._sounds_enabled)

    def _on_toggle_hold_mode_clicked(self, icon, item):
        if self.on_toggle_hold_mode:
            self.on_toggle_hold_mode(not self.config.hotkeys.hold_mode)

    def _on_toggle_hud_clicked(self, icon, item):
        if self.on_toggle_hud:
            self.on_toggle_hud(not self.config.ui.floating_indicator.enabled)

    def _on_toggle_click_through_clicked(self, icon, item):
        if self.on_toggle_click_through:
            self.on_toggle_click_through(not self.config.ui.floating_indicator.click_through)

    def _on_toggle_startup_clicked(self, icon, item):
        if self.on_toggle_startup:
            self.on_toggle_startup(not self.config.interaction.run_at_startup)

    def _open_config(self, icon, item):
        config_path = Path("config.toml")
        if config_path.exists():
            os.startfile(str(config_path.absolute()))
        if self.on_open_config:
            self.on_open_config()

    def set_state(self, state: AppState):
        self._state = state
        if self.indicator:
            self.indicator.update_status(state == AppState.LISTENING)
        if self.icon:
            self.icon.icon = self._create_image(self._get_icon_color(state))
            self.icon.menu = self._create_menu()

    def update_availability(self, availability: Dict[str, bool]):
        self._provider_availability = availability
        if self.icon:
            self.icon.menu = self._create_menu()

    def update_status(self, message: str):
        pass

    def notify(self, message: str, title: str = "Voice2Text"):
        if self.icon:
            self.icon.notify(message, title)

    def _poll_bridge(self):
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
            elif msg_type == UIEvent.UPDATE_PARTIAL_TEXT:
                if self.indicator:
                    self.indicator.on_partial(data)
            elif msg_type == UIEvent.UPDATE_VOICE_ACTIVITY:
                if self.indicator:
                    self.indicator.update_voice_active(data)
            elif msg_type == UIEvent.UPDATE_FINAL_TEXT:
                if self.indicator:
                    self.indicator.on_final(data)
            elif msg_type == UIEvent.UPDATE_STATUS_MESSAGE:
                if self.icon:
                    self.icon.title = f"Voice2Text: {data}"
                if self.indicator:
                    self.indicator.update_status_icon(data)
            elif msg_type == UIEvent.REFRESH_HUD:
                if self.indicator:
                    self.indicator.refresh_settings()
            elif msg_type == UIEvent.QUIT:
                logger.info("UI received QUIT signal via bridge.")
                self.stop()

    def run(self) -> None:
        if self.bridge:
            threading.Thread(target=self._poll_bridge, daemon=True).start()
        if self.indicator:
            self.indicator.start()
        if self.icon:
            self.icon.run()

    def stop(self) -> None:
        self._stop_event.set()
        if self.icon:
            self.icon.stop()
        if self.indicator:
            self.indicator.stop()
