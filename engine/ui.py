import os
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

# Senior Architectural Fix: Set DPI Unaware BEFORE ANY OTHER IMPORTS
# This is the only way to ensure Skia HUD and pystray remain at their original, preferred scaling.
try:
    import ctypes

    ctypes.windll.shcore.SetProcessDpiAwareness(0)
except Exception:
    pass

import pystray
import ttkbootstrap as tb
from PIL import Image, ImageDraw

from .app_types import AppState, ProviderType
from .logging import get_logger
from .stats import StatsManager
from .ui_utils import get_app_version

if TYPE_CHECKING:
    from .config import Config
    from .ui_bridge import UIBridge

logger = get_logger("UI")

# Master Root (Stored globally for the UI Thread)
_master_root: Optional[tb.Window] = None

# Internal Constants (Not exposed to user)
ICON_SIZE = 64
ICON_RADIUS = 12

COLOR_LISTENING = "#0078D4"
COLOR_CONNECTING = "#FACC15"
COLOR_ERROR = "#EF4444"
COLOR_TRANSITION = "#94A3B8"
COLOR_IDLE = "#475569"


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
        on_mic_profile_change: Callable[[str], None] | None = None,
        on_reload_config: Callable[[], None] | None = None,
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
        self.on_mic_profile_change = on_mic_profile_change
        self.on_reload_config = on_reload_config
        self.availability = availability or {"openai": True, "assemblyai": True}

        # Senior Architecture: Thread-safe UI state
        self.ui_root = None
        self._ui_ready = threading.Event()
        self.icon = self._create_icon()
        self._stop_event = threading.Event()
        self.stats_manager = StatsManager()

        # Lazy-load indicator
        self.indicator = None
        self._is_stopped = False
        if self.config.ui.floating_indicator.enabled:
            try:
                from .indicator_ui import IndicatorWindow

                self.indicator = IndicatorWindow(config=self.config)
            except Exception as e:
                logger.error(f"Failed to initialize indicator: {e}")

    def _run_ui_loop(self):
        """Dedicated background thread for the Tcl/Tk interpreter."""
        global _master_root
        if _master_root is None:
            # Senior Architecture: Use 'darkly' for a luxury, monochromatic feel.
            _master_root = tb.Window(themename="darkly")
            _master_root.withdraw()

        self.ui_root = _master_root
        self._ui_ready.set()

        # Enter the hidden Master mainloop
        self.ui_root.mainloop()

    def _create_image(self, color: str) -> Image.Image:
        image = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        dc.rounded_rectangle((2, 2, ICON_SIZE - 2, ICON_SIZE - 2), radius=ICON_RADIUS, fill=color)
        return image

    def _get_icon_color(self, state: AppState) -> str:
        colors = {
            AppState.LISTENING: COLOR_LISTENING,
            AppState.CONNECTING: COLOR_CONNECTING,
            AppState.ERROR: COLOR_ERROR,
            AppState.STOPPING: COLOR_TRANSITION,
            AppState.SHUTTING_DOWN: COLOR_TRANSITION,
        }
        return colors.get(state, COLOR_IDLE)

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

    def _on_mic_profile_selection(self, icon: pystray.Icon, profile: str) -> None:
        if self.on_mic_profile_change:
            self.on_mic_profile_change(profile)

    def _on_change_hotkey_clicked(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        if self.on_before_hotkey_change:
            self.on_before_hotkey_change()

        def record():
            from .hotkey_ui import HotkeyRecorder

            recorder = HotkeyRecorder(on_captured=self.on_hotkey_change)
            recorder.run()

        threading.Thread(target=record, daemon=True).start()

    def _on_set_key_clicked(self, provider_id: str, provider_name: str):
        # We launch the dialog on the UI Thread via after(0, ...)
        def prompt():
            from .credential_ui import ask_key

            if self.ui_root:
                key = ask_key(self.ui_root, provider_name)
                if key and self.on_set_key:
                    self.on_set_key(provider_id, key)

        if self.ui_root:
            self.ui_root.after(0, prompt)

    def _open_config(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        from .platform_win.paths import get_config_path

        config_path = Path(get_config_path())
        if config_path.exists():
            os.startfile(config_path)
        else:
            local_path = Path("config.toml").absolute()
            if local_path.exists():
                os.startfile(local_path)

    def _on_show_stats_clicked(self):
        """Launches the statistics dashboard instantly on the UI thread."""
        report = self.stats_manager.get_report()

        def launch():
            from .stats_ui import show_stats_dialog

            if self.ui_root:
                show_stats_dialog(self.ui_root, report)

        if self.ui_root:
            self.ui_root.after(0, launch)

    def _create_menu(self) -> pystray.Menu:
        version = get_app_version()
        return pystray.Menu(
            pystray.MenuItem(f"ParrotInk v{version}", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "OpenAI",
                lambda i, it: self._on_provider_selection(i, "openai"),
                checked=lambda i: self.current_provider == "openai",
                radio=True,
            ),
            pystray.MenuItem(
                "AssemblyAI",
                lambda i, it: self._on_provider_selection(i, "assemblyai"),
                checked=lambda i: self.current_provider == "assemblyai",
                radio=True,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Statistics...", self._on_show_stats_clicked),
            pystray.MenuItem(
                "Settings",
                pystray.Menu(
                    pystray.MenuItem(
                        "Setup API Keys",
                        pystray.Menu(
                            pystray.MenuItem(
                                "Set OpenAI Key...",
                                lambda: self._on_set_key_clicked("openai_api_key", "OpenAI"),
                            ),
                            pystray.MenuItem(
                                "Set AssemblyAI Key...",
                                lambda: self._on_set_key_clicked(
                                    "assemblyai_api_key", "AssemblyAI"
                                ),
                            ),
                        ),
                    ),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem(
                        lambda it: f"Change Hotkey... ({self.config.hotkeys.hotkey.upper()})",
                        self._on_change_hotkey_clicked,
                    ),
                    pystray.MenuItem(
                        "Hold to Talk",
                        self._on_toggle_hold_mode_clicked,
                        checked=lambda it: self.config.hotkeys.hold_mode,
                    ),
                    pystray.MenuItem(
                        "Enable Audio Feedback",
                        self._on_toggle_sounds_clicked,
                        checked=lambda it: self.sounds_enabled,
                    ),
                    pystray.MenuItem(
                        "Run at Startup",
                        self._on_toggle_startup_clicked,
                        checked=lambda it: self.config.interaction.run_at_startup,
                    ),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem(
                        "Show HUD",
                        self._on_toggle_hud_clicked,
                        checked=lambda it: self.config.ui.floating_indicator.enabled,
                    ),
                    pystray.MenuItem(
                        "HUD Click-Through",
                        self._on_toggle_click_through_clicked,
                        checked=lambda it: self.config.ui.floating_indicator.click_through,
                        enabled=lambda it: self.config.ui.floating_indicator.enabled,
                    ),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("Open Configuration File", self._open_config),
                    pystray.MenuItem(
                        "Reload Configuration",
                        self._on_reload_config_clicked,
                        enabled=lambda it: self.state in (AppState.IDLE, AppState.ERROR),
                    ),
                ),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_tray_quit),
        )

    def _on_tray_quit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Triggered only when the user explicitly clicks 'Quit' in the menu."""
        logger.info("Tray 'Quit' selected.")
        if self.on_quit_callback:
            self.on_quit_callback()
        else:
            self.stop()

    def _on_reload_config_clicked(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        if self.on_reload_config:
            self.on_reload_config()

    def _create_icon(self) -> pystray.Icon:
        return pystray.Icon(
            "parrotink",
            self._create_image(self._get_icon_color(self.state)),
            "ParrotInk",
            self._create_menu(),
        )

    def set_state(self, state: AppState) -> None:
        self.state = state
        self.icon.icon = self._create_image(self._get_icon_color(state))
        if self.indicator:
            is_rec = state == AppState.LISTENING
            self.indicator.update_status(is_rec)
            if is_rec:
                self.indicator.show()

    def update_availability(self, availability: dict[str, bool]):
        self.availability = availability

    def notify(self, message: str, title: str = "ParrotInk"):
        self.icon.notify(message, title)

    def _refresh_menu(self):
        self.icon.menu = self._create_menu()

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
                    self.indicator.update_partial_text(data)
            elif msg_type == UIEvent.UPDATE_VOICE_ACTIVITY:
                if self.indicator:
                    self.indicator.update_voice_activity(data)
            elif msg_type == UIEvent.UPDATE_FINAL_TEXT:
                if self.indicator:
                    self.indicator.on_final(data)
            elif msg_type == UIEvent.UPDATE_STATUS_MESSAGE:
                # Update Tray Tooltip
                self.icon.title = f"ParrotInk: {data}"
                # Forward to HUD
                if self.indicator:
                    self.indicator.update_status_icon(data)
            elif msg_type == UIEvent.UPDATE_PROVIDER:
                if self.indicator:
                    self.indicator.update_provider(data)
                # Refresh tooltip with new provider
                self.set_state(self.state)
            elif msg_type == UIEvent.UPDATE_SETTINGS:
                if self.indicator:
                    self.indicator.update_settings(data)
                self._refresh_menu()
            elif msg_type == UIEvent.REFRESH_HUD:
                if self.indicator:
                    self.indicator.refresh_settings()
            elif msg_type == UIEvent.CLEAR_HUD:
                if self.indicator:
                    self.indicator.clear()
            elif msg_type == UIEvent.RECORD_STATS:
                self.stats_manager.record_session(
                    data["duration"], data["words"], data["provider"], data["error"]
                )
                self.stats_manager.save()
            elif msg_type == UIEvent.QUIT:
                self.stop()

    def run(self) -> None:
        # 1. Launch the hidden Master on its own sidecar thread
        threading.Thread(target=self._run_ui_loop, daemon=True).start()

        # 2. Wait for the UI Master to be initialized before continuing
        self._ui_ready.wait(timeout=5.0)

        # 3. Launch the Tray Icon in another thread to avoid blocking the main thread
        threading.Thread(target=self.icon.run, daemon=True).start()

        # 4. Start polling the bridge (also in its own thread)
        if self.bridge:
            threading.Thread(target=self._poll_bridge, daemon=True).start()

        if self.indicator:
            threading.Thread(target=self.indicator.start, daemon=True).start()

        logger.info("UI System fully initialized. Entering wait state.")
        # Block this thread until stop() is called.
        # Since gui_main now runs this in a non-daemon thread, this keeps the process alive
        # while the sidecar threads (icon, bridge, indicator) do the work.
        while not self._stop_event.is_set():
            self._stop_event.wait(timeout=1.0)

        logger.info("TrayApp run loop exited.")

    def _shutdown_ui(self):
        """Runs on the UI thread to stop the mainloop and cleanup."""
        global _master_root
        if self.ui_root:
            try:
                # Stop the mainloop first
                self.ui_root.quit()
                # Destroy the window
                self.ui_root.destroy()
                self.ui_root = None
                _master_root = None
            except Exception as e:
                logger.debug(f"Error during Tcl shutdown: {e}")

    def stop(self, *args) -> None:
        """
        Thread-safe stop signal.
        Can be called from any thread (Tray, Main, or Bridge).
        """
        if self._is_stopped:
            return
        self._is_stopped = True

        logger.info("Stopping UI systems...")
        self._stop_event.set()

        # Cleanly destroy the hidden master on its OWN (UI) thread
        # This prevents "async handler deleted by the wrong thread"
        if self.ui_root:
            try:
                self.ui_root.after(0, self._shutdown_ui)
            except Exception:
                # If the loop is already dead, _shutdown_ui isn't needed
                pass

        # Pystray stop is idempotent
        try:
            self.icon.stop()
        except Exception:
            pass

        if self.indicator:
            self.indicator.stop()

