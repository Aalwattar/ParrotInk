import os
import threading
import webbrowser
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
from win11toast import toast

from .app_types import AppState, ProviderType
from .logging import get_logger
from .services.updates import UpdateState
from .stats import StatsManager
from .ui_menu import build_tray_menu
from .ui_utils import get_resource_path

if TYPE_CHECKING:
    from .config import Config
    from .indicator_ui import IndicatorWindow
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
        on_latency_profile_change: Callable[[str], None] | None = None,
        on_toggle_realtime_punctuation: Callable[[bool], None] | None = None,
        on_reload_config: Callable[[], None] | None = None,
        on_check_updates: Callable[[], None] | None = None,
        on_install_update: Callable[[], None] | None = None,
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
        self.on_latency_profile_change = on_latency_profile_change
        self.on_toggle_realtime_punctuation = on_toggle_realtime_punctuation
        self.on_reload_config = on_reload_config
        self.on_check_updates = on_check_updates
        self.on_install_update = on_install_update
        self.availability = availability or {"openai": True, "assemblyai": True}

        # Update info
        self.latest_version: Optional[str] = None
        self.release_url: Optional[str] = None
        self.update_state = UpdateState.IDLE
        self.download_percent = 0

        # Senior Architecture: Thread-safe UI state
        self.ui_root = None
        self._ui_ready = threading.Event()
        self.audio_error_type: Optional[str] = None  # Track specific audio errors
        self._popup_active = False  # Guard for concurrent popups

        # Senior Architecture: Prevent Tcl_AsyncDelete cross-thread panics by keeping
        # a strong reference to all generated PIL Images. If PIL.ImageTk is loaded,
        # destroying an Image on a non-Tcl thread crashes the app.
        self._icon_cache: dict[AppState, Image.Image] = {}

        self.icon = self._create_icon()
        self._stop_event = threading.Event()
        self.stats_manager = StatsManager()

        # Lazy-load indicator
        self.indicator: Optional["IndicatorWindow"] = None
        self._indicator_lock = threading.Lock()
        self._hud_failure_count = 0
        self._is_stopped = False
        self._ensure_indicator()

    def _ensure_indicator(self) -> bool:
        """
        Safely creates or verifies the floating indicator.
        Returns True if indicator exists and is ready, False otherwise.
        """
        with self._indicator_lock:
            # If disabled in config, ensure we don't have one
            if not self.config.ui.floating_indicator.enabled:
                if self.indicator:
                    try:
                        self.indicator.stop()
                    except Exception:
                        pass
                    self.indicator = None
                return False

            # Circuit Breaker: If the HUD failed too many times, permanently disable recovery
            # to prevent CPU pegging loops, and use the mock.
            if self._hud_failure_count >= 3:
                # If we don't have a mock indicator yet, create one
                if not self.indicator or getattr(self.indicator, "is_alive", lambda: False)():
                    from .indicator_ui import IndicatorWindow

                    # Force disable real HUD for this instance by patching the config temporarily
                    # Actually, IndicatorWindow falls back to GdiFallbackWindow internally
                    # if it crashes, but to stop the health loop, we just treat whatever is there
                    # as healthy, or recreate it once and never check health again.
                    pass  # We handle this by not checking health below if count >= 3

            # If we have an indicator, check if it's still alive/healthy
            if self.indicator and self._hud_failure_count < 3:
                # Senior Architecture: Use robust Win32 health probe
                if self.indicator.is_healthy():
                    return True
                else:
                    self._hud_failure_count += 1
                    logger.warning(
                        "HUD Indicator detected as unhealthy or dead "
                        f"(Failures: {self._hud_failure_count}/3). Re-initializing."
                    )
                    try:
                        self.indicator.stop()
                    except Exception:
                        pass
                    self.indicator = None

            # If enabled but not created (or just died), try to create it
            if not self.indicator:
                try:
                    from .indicator_ui import IndicatorWindow

                    logger.info("Lazily initializing IndicatorWindow.")

                    # If circuit breaker tripped, force fallback by overriding HUD_AVAILABLE locally
                    if self._hud_failure_count >= 3:
                        import engine.hud_renderer

                        engine.hud_renderer.HUD_AVAILABLE = False
                        logger.error(
                            "HUD Circuit Breaker tripped. Permanently falling back to mock."
                        )

                    self.indicator = IndicatorWindow(config=self.config)
                    # Start its thread
                    if not self._is_stopped:
                        self.indicator.start()

                        # Senior Architecture: State Sync
                        # If we recreated the HUD during an active session, it will spawn hidden.
                        # We must sync its state to match the current application state.
                        is_rec = self.state == AppState.LISTENING
                        self.indicator.update_status(is_rec)
                        if is_rec:
                            self.indicator.show()

                    return True
                except (ImportError, RuntimeError) as e:
                    # Catching specific setup/dependency failures
                    logger.error(f"Failed to initialize indicator (dependency issue): {e}")
                    self._hud_failure_count += 1
                    return False
                except Exception as e:
                    # Catch-all for unexpected HUD creation failures
                    logger.error(f"Unexpected HUD creation failure: {e}", exc_info=True)
                    self._hud_failure_count += 1
                    return False

        return True

    def _run_ui_loop(self):
        """Dedicated background thread for the Tcl/Tk interpreter."""
        global _master_root
        try:
            if _master_root is None:
                # Senior Architecture: Use 'darkly' for a luxury, monochromatic feel.
                _master_root = tb.Window(themename="darkly")
                _master_root.withdraw()

            self.ui_root = _master_root
            self._ui_ready.set()

            # Enter the hidden Master mainloop
            self.ui_root.mainloop()
        except Exception as e:
            logger.error(f"FATAL: UI Master Loop crashed: {e}", exc_info=True)

    def _get_icon_asset(self, state: AppState) -> Optional[Image.Image]:
        """
        Attempts to load a custom .ico asset for the given state.
        Returns the Image object if successful, None otherwise.
        """
        mapping = {
            AppState.IDLE: "tray_idle.ico",
            AppState.LISTENING: "tray_listening.ico",
            AppState.CONNECTING: "tray_connecting.ico",
            AppState.ERROR: "tray_error.ico",
            AppState.STOPPING: "tray_transition.ico",
            AppState.SHUTTING_DOWN: "tray_transition.ico",
        }

        filename = mapping.get(state)
        if not filename:
            return None

        icon_path = Path(get_resource_path(os.path.join("assets", "icons", filename)))
        if icon_path.exists():
            try:
                # Return the image object. pystray handles resizing if needed.
                return Image.open(icon_path)
            except Exception as e:
                logger.warning(f"Failed to load icon asset {icon_path}: {e}")

        return None

    def _get_icon_image(self, state: AppState) -> Image.Image:
        """
        Returns the best available icon for the state:
        1. Custom .ico asset from assets/icons/
        2. Dynamically generated colored square (Fallback)
        """
        # Senior Architecture: Check cache first to avoid GC cross-thread Tkinter panics
        if state in self._icon_cache:
            return self._icon_cache[state]

        asset = self._get_icon_asset(state)
        if asset:
            self._icon_cache[state] = asset
            return asset

        # Fallback to dynamic generation
        generated = self._create_image(self._get_icon_color(state))
        self._icon_cache[state] = generated
        return generated

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

    def _on_latency_profile_selection(self, icon: pystray.Icon, profile: str) -> None:
        if self.on_latency_profile_change:
            self.on_latency_profile_change(profile)

    def _on_toggle_realtime_punctuation_clicked(
        self, icon: pystray.Icon, item: pystray.MenuItem
    ) -> None:
        if self.on_toggle_realtime_punctuation:
            # We toggle based on current config state
            current = self.config.providers.assemblyai.advanced.format_text
            self.on_toggle_realtime_punctuation(not current)

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

    def _open_log_folder(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        from .logging import get_current_log_dir

        log_dir = get_current_log_dir(self.config)
        if log_dir.exists():
            os.startfile(log_dir)

    def _on_show_stats_clicked(self):
        """Launches the statistics dashboard instantly on the UI thread."""
        report = self.stats_manager.get_report()

        def launch():
            from .stats_ui import show_stats_dialog

            if self.ui_root:
                show_stats_dialog(self.ui_root, report)

        if self.ui_root:
            self.ui_root.after(0, launch)

    def _on_update_clicked(self, icon: pystray.Icon, item: pystray.MenuItem):
        """Handles clicks on the version/update menu item."""
        state_name = getattr(self.update_state, "name", "")
        if state_name == "READY_TO_INSTALL":
            # User confirmed installation via menu click
            if self.on_install_update:
                self.on_install_update()
        elif self.release_url:
            logger.info(f"Opening update URL: {self.release_url}")
            webbrowser.open(self.release_url)

    def _on_fix_mic_clicked(self, icon: pystray.Icon, item: pystray.MenuItem):
        """Deep-links to Windows Settings based on the error type."""
        import sys

        if sys.platform != "win32":
            return

        from .platform_win.audio_diag import open_settings

        if self.audio_error_type == "privacy":
            open_settings("microphone")
        else:
            open_settings("sound")

    def _create_menu(self) -> pystray.Menu:
        return build_tray_menu(self)

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
            self._get_icon_image(self.state),
            "ParrotInk",
            self._create_menu(),
        )

    def set_state(self, state: AppState) -> None:
        self.state = state
        self.icon.icon = self._get_icon_image(state)
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
                if self._ensure_indicator():
                    self.indicator.update_partial_text(data)
            elif msg_type == UIEvent.UPDATE_VOICE_ACTIVITY:
                if self._ensure_indicator():
                    self.indicator.update_voice_activity(data)
            elif msg_type == UIEvent.UPDATE_FINAL_TEXT:
                if self._ensure_indicator():
                    self.indicator.on_final(data)
            elif msg_type == UIEvent.UPDATE_STATUS_MESSAGE:
                # Update Tray Tooltip
                self.icon.title = f"ParrotInk: {data}"
                # Forward to HUD
                if self._ensure_indicator():
                    self.indicator.update_status_icon(data)
            elif msg_type == UIEvent.UPDATE_PROVIDER:
                if self._ensure_indicator():
                    self.indicator.update_provider(data)
                # Refresh tooltip with new provider
                self.set_state(self.state)
            elif msg_type == UIEvent.UPDATE_SETTINGS:
                if self._ensure_indicator():
                    self.indicator.update_settings(data)
                self._refresh_menu()
            elif msg_type == UIEvent.REFRESH_HUD:
                # If it was enabled/disabled, we attempt re-initialization
                if self._ensure_indicator():
                    self.indicator.refresh_settings()
            elif msg_type == UIEvent.CLEAR_HUD:
                if self._ensure_indicator():
                    self.indicator.clear()
            elif msg_type == UIEvent.RECORD_STATS:
                self.stats_manager.record_session(
                    data["duration"], data["words"], data["provider"], data["error"]
                )
            elif msg_type == UIEvent.UPDATE_VERSION_NOTIFICATION:
                version_tag, release_url, update_state, percent = data
                self.latest_version = version_tag
                self.release_url = release_url

                # If we just reached READY_TO_INSTALL, show a toast
                if (
                    getattr(update_state, "name", "") == "READY_TO_INSTALL"
                    and getattr(self.update_state, "name", "") != "READY_TO_INSTALL"
                ):
                    try:
                        toast(
                            title="ParrotInk Update Ready",
                            body=f"Version {version_tag} is ready to install.",
                            app_id="ParrotInk",
                        )
                    except Exception as e:
                        logger.warning(f"Failed to show update toast: {e}")

                self.update_state = update_state
                self.download_percent = percent
                self._refresh_menu()
            elif msg_type == UIEvent.UPDATE_AUDIO_ERROR:
                self.audio_error_type = data
                self._refresh_menu()
            elif msg_type == UIEvent.SHOW_HARDWARE_ERROR_POPUP:
                self._show_hardware_error_dialog()
            elif msg_type == UIEvent.QUIT:
                self.stop()

    def _show_hardware_error_dialog(self):
        """Shows a native OS popup for microphone hardware/privacy issues."""
        import sys

        # Senior Architecture: Never show blocking modal dialogs during automated tests.
        if "pytest" in sys.modules or os.getenv("GITHUB_ACTIONS"):
            logger.info("Skipping hardware error popup (Test Environment detected).")
            return

        if self._popup_active:
            return
        self._popup_active = True

        def show():
            import ctypes

            # MB_YESNO | MB_ICONWARNING | MB_SETFOREGROUND
            # 4 (Yes/No) | 48 (Warning Icon) | 65536 (SetForeground) = 65588
            # Yes = 6, No = 7
            msg = (
                "MICROPHONE ACCESS DENIED\n\n"
                "ParrotInk cannot access your microphone. "
                "This is likely blocked by Windows Privacy settings.\n\n"
                "IMPORTANT: In the settings page that opens, scroll down and "
                "ensure the following toggle is turned ON:\n\n"
                "   'Let desktop apps access your microphone'\n\n"
                "Would you like to open the Windows Microphone Privacy settings now?"
            )
            title = "Microphone Access Required"

            try:
                result = ctypes.windll.user32.MessageBoxW(0, msg, title, 65588)
                if result == 6:  # Yes clicked
                    from .platform_win.audio_diag import open_settings

                    open_settings("microphone")
            finally:
                self._popup_active = False

        # Run on a detached thread so it doesn't block the UI event loop
        threading.Thread(target=show, daemon=True).start()

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

        # Ensure stats are flushed before we kill the process
        if hasattr(self, "stats_manager"):
            self.stats_manager.stop()

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
