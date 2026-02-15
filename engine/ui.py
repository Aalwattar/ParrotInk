import os
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

import pystray
from PIL import Image, ImageDraw

from .app_types import AppState, ProviderType
from .credential_ui import ask_key
from .logging import get_logger
from .ui_utils import get_app_version

if TYPE_CHECKING:
    from .config import Config
    from .ui_bridge import UIBridge

logger = get_logger("UI")


class TrayApp:
    def __init__(
        self,
        config: "Config",
        bridge: Optional["UIBridge"] = None,
        on_quit_callback: Callable | None = None,
        on_provider_change: Callable[[ProviderType], None] | None = None,
        on_set_key: Callable[[str, str], None] | None = None,
        on_toggle_sounds: Callable[[bool], None] | None = None,
        on_hotkey_change: Callable[[str], None] | None = None,
        on_before_hotkey_change: Callable[[], None] | None = None,
        on_toggle_hud: Callable[[bool], None] | None = None,
        on_toggle_click_through: Callable[[bool], None] | None = None,
        on_toggle_startup: Callable[[bool], None] | None = None,
        on_toggle_hold_mode: Callable[[bool], None] | None = None,
        initial_provider: ProviderType = "openai",
        initial_sounds_enabled: bool = True,
        availability: Optional[dict[str, bool]] = None,
    ):
        self.config = config
        self.bridge = bridge
        self.state = AppState.IDLE
        self.current_provider: ProviderType = initial_provider
        self.sounds_enabled = initial_sounds_enabled
        self.on_quit_callback = on_quit_callback
        self.on_provider_change = on_provider_change
        self.on_set_key = on_set_key
        self.on_toggle_sounds = on_toggle_sounds
        self.on_hotkey_change = on_hotkey_change
        self.on_before_hotkey_change = on_before_hotkey_change
        self.on_toggle_hud = on_toggle_hud
        self.on_toggle_click_through = on_toggle_click_through
        self.on_toggle_startup = on_toggle_startup
        self.on_toggle_hold_mode = on_toggle_hold_mode
        self.availability = availability or {"openai": True, "assemblyai": True}

        self.icon = self._create_icon()
        self._stop_event = threading.Event()

        # Lazy-load indicator (I5)
        self.indicator = None
        if self.config.ui.floating_indicator.enabled:
            logger.info("Initializing Floating Indicator...")
            try:
                from .indicator_ui import IndicatorWindow

                self.indicator = IndicatorWindow(config=self.config)
            except Exception as e:
                logger.error(f"Failed to initialize indicator: {e}")
        else:
            logger.info("Floating Indicator is disabled.")

    def _create_image(self, color: str) -> Image.Image:
        width, height = 64, 64
        # Use RGBA for transparency support (rounded corners)
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        # Modern rounded square design - Increased size and adjusted radius for clarity
        dc.rounded_rectangle((2, 2, 62, 62), radius=12, fill=color)
        return image

    def _get_icon_color(self, state: AppState) -> str:
        if state == AppState.LISTENING:
            return "#0078D4"  # Microsoft Blue (Vibrant)
        if state == AppState.CONNECTING:
            return "#FACC15"  # Yellow-400
        if state == AppState.ERROR:
            return "#EF4444"  # Red-500
        if state in (AppState.STOPPING, AppState.SHUTTING_DOWN):
            return "#94A3B8"  # Slate-400
        return "#475569"  # Slate-600 (Better visibility than Slate-700)

    def _on_provider_selection(self, icon: pystray.Icon, provider: ProviderType) -> None:
        self.current_provider = provider
        if self.on_provider_change:
            self.on_provider_change(provider)

    def _on_toggle_sounds_clicked(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.sounds_enabled = not self.sounds_enabled
        if self.on_toggle_sounds:
            self.on_toggle_sounds(self.sounds_enabled)

    def _on_toggle_hud_clicked(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        if self.on_toggle_hud:
            self.on_toggle_hud(not self.config.ui.floating_indicator.enabled)

    def _on_toggle_click_through_clicked(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        if self.on_toggle_click_through:
            self.on_toggle_click_through(not self.config.ui.floating_indicator.click_through)

    def _on_toggle_startup_clicked(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        if self.on_toggle_startup:
            self.on_toggle_startup(not self.config.interaction.run_at_startup)

    def _on_toggle_hold_mode_clicked(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        if self.on_toggle_hold_mode:
            self.on_toggle_hold_mode(not self.config.hotkeys.hold_mode)

    def _on_change_hotkey_clicked(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        logger.info("Hotkey Change requested (Feature Under Development)")
        if self.indicator:
            # Show the message on the HUD
            self.indicator.show()
            self.indicator.on_final("Hotkey Configuration: Under Development")
        else:
            # Fallback to notification if HUD is disabled
            self.notify(
                "Hotkey UI is under development. Please edit config.toml manually.",
                "Under Development",
            )

    def _on_set_key_clicked(self, provider_id: str, provider_name: str):
        # We launch this in a thread because showing a dialog (console or GUI)
        # from the pystray callback might block the tray icon loop or not work well.
        def prompt():
            key = ask_key(provider_name)
            if key and self.on_set_key:
                self.on_set_key(provider_id, key)

        threading.Thread(target=prompt, daemon=True).start()

    def _open_config(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        from .platform_win.paths import get_config_path

        config_path = Path(get_config_path())
        if config_path.exists():
            os.startfile(config_path)
        else:
            logger.warning(f"Config file not found at: {config_path}")
            # Fallback to current directory for development convenience if APPDATA is missing
            local_path = Path("config.toml").absolute()
            if local_path.exists():
                os.startfile(local_path)
            else:
                self.notify("Configuration file not found.", "Error")

    def _create_icon(self) -> pystray.Icon:
        version = get_app_version()
        menu = pystray.Menu(
            pystray.MenuItem(
                f"Voice2Text v{version}",
                lambda: None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "OpenAI",
                lambda icon, item: self._on_provider_selection(icon, "openai"),
                checked=lambda item: self.current_provider == "openai",
                enabled=lambda item: self.availability.get("openai", True),
                radio=True,
            ),
            pystray.MenuItem(
                "AssemblyAI",
                lambda icon, item: self._on_provider_selection(icon, "assemblyai"),
                checked=lambda item: self.current_provider == "assemblyai",
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
                        lambda item: f"Change Hotkey... ({self.config.hotkeys.hotkey.upper()})",
                        self._on_change_hotkey_clicked,
                    ),
                    pystray.MenuItem(
                        "Hold to Talk",
                        self._on_toggle_hold_mode_clicked,
                        checked=lambda item: self.config.hotkeys.hold_mode,
                    ),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem(
                        "Enable Audio Feedback",
                        self._on_toggle_sounds_clicked,
                        checked=lambda item: self.sounds_enabled,
                    ),
                    pystray.MenuItem(
                        "Run at Startup",
                        self._on_toggle_startup_clicked,
                        checked=lambda item: self.config.interaction.run_at_startup,
                    ),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem(
                        "Show HUD",
                        self._on_toggle_hud_clicked,
                        checked=lambda item: self.config.ui.floating_indicator.enabled,
                    ),
                    pystray.MenuItem(
                        "HUD Click-Through",
                        self._on_toggle_click_through_clicked,
                        checked=lambda item: self.config.ui.floating_indicator.click_through,
                        enabled=lambda item: self.config.ui.floating_indicator.enabled,
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

        # Update Tooltip
        state_map = {
            AppState.IDLE: "Idle",
            AppState.LISTENING: "Listening",
            AppState.CONNECTING: "Connecting...",
            AppState.ERROR: "Error",
            AppState.STOPPING: "Stopping...",
            AppState.SHUTTING_DOWN: "Shutting down...",
        }
        self.icon.title = f"Voice2Text: {state_map.get(state, 'Unknown')}"

        # Sync indicator visibility and status
        if self.indicator:
            if state == AppState.LISTENING:
                logger.debug("TrayApp: Showing indicator (LISTENING)")
                self.indicator.update_status(True)
                self.indicator.show()
            elif state == AppState.CONNECTING:
                self.indicator.update_status(True)
                if hasattr(self.indicator.impl, "update_status_icon"):
                    self.indicator.impl.update_status_icon("CONNECTING")
                self.indicator.show()
            elif state == AppState.IDLE:
                logger.debug("TrayApp: Updating status to idle (IDLE)")
                self.indicator.update_status(False)
                # Removed self.indicator.hide() here to allow on_final to handle lingering text
            elif state == AppState.ERROR:
                self.indicator.update_status(False)
            # We might want to keep it visible to show the error,
            # but for now let's hide it or just update color
            pass

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
            elif msg_type == UIEvent.UPDATE_PARTIAL_TEXT:
                if self.indicator:
                    self.indicator.update_partial_text(data)
            elif msg_type == UIEvent.UPDATE_VOICE_ACTIVITY:
                if self.indicator:
                    self.indicator.update_voice_active(data)
            elif msg_type == UIEvent.UPDATE_FINAL_TEXT:
                if self.indicator:
                    self.indicator.on_final(data)
            elif msg_type == UIEvent.UPDATE_STATUS_MESSAGE:
                # Update Tray Tooltip
                self.icon.title = f"Voice2Text: {data}"
                # Forward to HUD
                if self.indicator:
                    self.indicator.update_status_icon(data)
            elif msg_type == UIEvent.QUIT:
                logger.info("UI received QUIT signal via bridge.")
                self.stop()

    def run(self) -> None:
        if self.bridge:
            threading.Thread(target=self._poll_bridge, daemon=True).start()
        if self.indicator:
            self.indicator.start()
        self.icon.run()

    def stop(self) -> None:
        print("\nShutting down UI...", flush=True)
        self._stop_event.set()
        self.icon.stop()

        callback = self.on_quit_callback
        self.on_quit_callback = None  # Prevent recursion
        if callback:
            callback()
