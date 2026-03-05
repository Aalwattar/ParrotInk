import webbrowser
from typing import TYPE_CHECKING

import pystray

from engine.app_types import AppState
from engine.constants import URL_HOMEPAGE, URL_ISSUES
from engine.ui_utils import get_app_version

if TYPE_CHECKING:
    from engine.ui import TrayApp


def build_tray_menu(app: "TrayApp") -> pystray.Menu:
    """
    Constructs the system tray menu using a structured hierarchy.
    Redesigned for Phase 3 UI/UX improvements.
    """
    version = get_app_version()

    def no_op(*args, **kwargs):
        pass

    menu_items = []

    # 1. Hardware Fix Links (Top Priority)
    if app.audio_error_type:
        fix_label = (
            "🚨 FIX: Check Privacy & security > Microphone"
            if app.audio_error_type == "privacy"
            else "🚨 FIX: Audio Device Unavailable"
        )
        menu_items.append(pystray.MenuItem(fix_label, app._on_fix_mic_clicked, default=True))
        menu_items.append(pystray.Menu.SEPARATOR)

    # 2. Version / Updates (Informational)
    version_label = f"ParrotInk v{version}"
    on_version_click = no_op
    is_version_enabled = False
    is_version_default = False

    if app.latest_version:
        version_label = f"✨ UPDATE AVAILABLE: {app.latest_version}"
        on_version_click = app._on_update_clicked
        is_version_enabled = True
        is_version_default = True

    menu_items.append(
        pystray.MenuItem(
            version_label,
            on_version_click,
            enabled=is_version_enabled,
            default=is_version_default,
        )
    )
    menu_items.append(pystray.Menu.SEPARATOR)

    # 3. Transcription Sub-menu (Provider & Profile)
    menu_items.append(
        pystray.MenuItem(
            "Transcription",
            pystray.Menu(
                pystray.MenuItem(
                    "Provider",
                    pystray.Menu(
                        pystray.MenuItem(
                            "OpenAI",
                            lambda i, it: app._on_provider_selection(i, "openai"),
                            checked=lambda i: app.current_provider == "openai",
                            radio=True,
                        ),
                        pystray.MenuItem(
                            "AssemblyAI",
                            lambda i, it: app._on_provider_selection(i, "assemblyai"),
                            checked=lambda i: app.current_provider == "assemblyai",
                            radio=True,
                        ),
                    ),
                ),
                pystray.MenuItem(
                    "Microphone Profile",
                    pystray.Menu(
                        pystray.MenuItem(
                            "Headset (Near-field)",
                            lambda i, it: app._on_mic_profile_selection(i, "headset"),
                            checked=lambda i: app.config.transcription.mic_profile == "headset",
                            radio=True,
                        ),
                        pystray.MenuItem(
                            "Laptop (Far-field)",
                            lambda i, it: app._on_mic_profile_selection(i, "laptop"),
                            checked=lambda i: app.config.transcription.mic_profile == "laptop",
                            radio=True,
                        ),
                        pystray.MenuItem(
                            "None (Raw)",
                            lambda i, it: app._on_mic_profile_selection(i, "none"),
                            checked=lambda i: app.config.transcription.mic_profile == "none",
                            radio=True,
                        ),
                    ),
                ),
            ),
        )
    )

    # 4. Settings Sub-menu
    menu_items.append(
        pystray.MenuItem(
            "Settings",
            pystray.Menu(
                pystray.MenuItem(
                    "API Credentials",
                    pystray.Menu(
                        pystray.MenuItem(
                            "Set OpenAI Key...",
                            lambda: app._on_set_key_clicked("openai_api_key", "OpenAI"),
                        ),
                        pystray.MenuItem(
                            "Set AssemblyAI Key...",
                            lambda: app._on_set_key_clicked("assemblyai_api_key", "AssemblyAI"),
                        ),
                    ),
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    lambda it: f"Change Hotkey... ({app.config.hotkeys.hotkey.upper()})",
                    app._on_change_hotkey_clicked,
                    enabled=lambda it: app.state in (AppState.IDLE, AppState.ERROR),
                ),
                pystray.MenuItem(
                    "Hold to Talk",
                    app._on_toggle_hold_mode_clicked,
                    checked=lambda it: app.config.hotkeys.hold_mode,
                ),
                pystray.MenuItem(
                    "Enable Audio Feedback",
                    app._on_toggle_sounds_clicked,
                    checked=lambda it: app.sounds_enabled,
                ),
                pystray.MenuItem(
                    "Run at Startup",
                    app._on_toggle_startup_clicked,
                    checked=lambda it: app.config.interaction.run_at_startup,
                ),
            ),
        )
    )

    # 5. Tools Sub-menu
    menu_items.append(
        pystray.MenuItem(
            "Tools",
            pystray.Menu(
                pystray.MenuItem("Statistics...", app._on_show_stats_clicked),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "Floating HUD",
                    pystray.Menu(
                        pystray.MenuItem(
                            "Enabled",
                            app._on_toggle_hud_clicked,
                            checked=lambda it: app.config.ui.floating_indicator.enabled,
                        ),
                        pystray.MenuItem(
                            "Click-Through",
                            app._on_toggle_click_through_clicked,
                            checked=lambda it: app.config.ui.floating_indicator.click_through,
                            enabled=lambda it: app.config.ui.floating_indicator.enabled,
                        ),
                    ),
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Open Configuration File", app._open_config),
                pystray.MenuItem("Open Log Folder", app._open_log_folder),
                pystray.MenuItem(
                    "Reload Configuration",
                    app._on_reload_config_clicked,
                    enabled=lambda it: app.state in (AppState.IDLE, AppState.ERROR),
                ),
            ),
        )
    )

    # 6. Help & Exit
    menu_items.append(pystray.Menu.SEPARATOR)
    menu_items.append(
        pystray.MenuItem(
            "Help",
            pystray.Menu(
                pystray.MenuItem("View Documentation", lambda: webbrowser.open(URL_HOMEPAGE)),
                pystray.MenuItem("Report an Issue", lambda: webbrowser.open(URL_ISSUES)),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "Check for Updates...",
                    lambda: app.on_check_updates() if app.on_check_updates else None,
                ),
            ),
        )
    )

    menu_items.append(pystray.MenuItem("Quit", app._on_tray_quit))

    return pystray.Menu(*menu_items)
