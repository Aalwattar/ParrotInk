import webbrowser
from typing import TYPE_CHECKING

import pystray

from engine.app_types import AppState
from engine.constants import URL_HOMEPAGE, URL_ISSUES
from engine.transcription.catalog import (
    PROVIDER_LABELS,
    get_model,
    get_selected_model,
    models_for_provider,
)
from engine.ui_utils import get_app_version

if TYPE_CHECKING:
    from engine.ui import TrayApp


def get_active_model_name(app: "TrayApp") -> str:
    """Helper to get the name of the active transcription model."""
    return get_selected_model(app.config, app.current_provider)


def _uses_modern_assemblyai(app: "TrayApp") -> bool:
    return (
        app.current_provider == "assemblyai"
        and get_model("assemblyai", get_active_model_name(app)).modern
    )


def _supports_mic_profile(app: "TrayApp") -> bool:
    return app.current_provider == "openai" or _uses_modern_assemblyai(app)


def _provider_menu(app: "TrayApp") -> pystray.Menu:
    def select(provider):
        return lambda icon, item: app._on_provider_selection(icon, provider)

    def checked(provider):
        return lambda item: app.current_provider == provider

    return pystray.Menu(
        *(
            pystray.MenuItem(
                label,
                select(provider),
                checked=checked(provider),
                radio=True,
                enabled=lambda item: app.state in (AppState.IDLE, AppState.ERROR),
            )
            for provider, label in PROVIDER_LABELS.items()
        )
    )


def _model_menu(app: "TrayApp") -> pystray.Menu:
    provider = app.current_provider

    def select(model):
        return lambda icon, item: app._on_model_selection(icon, provider, model)

    def checked(model):
        return lambda item: get_selected_model(app.config, provider) == model

    return pystray.Menu(
        *(
            pystray.MenuItem(
                spec.label,
                select(spec.id),
                checked=checked(spec.id),
                radio=True,
                enabled=lambda item: app.state in (AppState.IDLE, AppState.ERROR),
            )
            for spec in models_for_provider(app.current_provider)
            if spec.modern and "(legacy)" not in spec.label
        )
    )


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
        state_name = getattr(app.update_state, "name", "")
        if state_name == "DOWNLOADING":
            pct = app.download_percent
            if pct > 0:
                version_label = f"⏳ DOWNLOADING UPDATE: {pct}%"
            else:
                version_label = "⏳ DOWNLOADING UPDATE..."
            is_version_enabled = False  # Keep non-clickable during download
        elif state_name == "READY_TO_INSTALL":
            version_label = f"🚀 INSTALL UPDATE: {app.latest_version} (READY)"
            on_version_click = app._on_update_clicked
            is_version_enabled = True
            is_version_default = True
        elif state_name == "ERROR":
            version_label = "❌ UPDATE ERROR (Check Logs)"
            on_version_click = app._on_update_clicked
            is_version_enabled = True
        else:
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

    # 3. Usage Statistics (Promoted to Top Level)
    menu_items.append(pystray.MenuItem("Statistics...", app._on_show_stats_clicked))
    menu_items.append(pystray.Menu.SEPARATOR)

    # 4. Transcription Sub-menu (Provider & Profiles)
    menu_items.append(
        pystray.MenuItem(
            lambda it: f"Transcription ({get_active_model_name(app)})",
            pystray.Menu(
                pystray.MenuItem(
                    "Provider",
                    _provider_menu(app),
                ),
                pystray.MenuItem("Model", _model_menu(app)),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "Transcription Speed",
                    pystray.Menu(
                        pystray.MenuItem(
                            "Fast (Less accurate)",
                            lambda i, it: app._on_latency_profile_selection(i, "fast"),
                            checked=lambda i: app.config.transcription.latency_profile == "fast",
                            radio=True,
                        ),
                        pystray.MenuItem(
                            "Standard (Balanced) (Default)",
                            lambda i, it: app._on_latency_profile_selection(i, "balanced"),
                            checked=lambda i: (
                                app.config.transcription.latency_profile == "balanced"
                            ),
                            radio=True,
                        ),
                        pystray.MenuItem(
                            "Slower (More accurate)",
                            lambda i, it: app._on_latency_profile_selection(i, "accurate"),
                            checked=lambda i: (
                                app.config.transcription.latency_profile == "accurate"
                            ),
                            radio=True,
                        ),
                    ),
                    enabled=lambda i: app.current_provider != "cloudflare",
                ),
                pystray.MenuItem(
                    "Microphone Profile",
                    pystray.Menu(
                        pystray.MenuItem(
                            "Optimized for Headsets",
                            lambda i, it: app._on_mic_profile_selection(i, "headset"),
                            checked=lambda i: app.config.transcription.mic_profile == "headset",
                            radio=True,
                        ),
                        pystray.MenuItem(
                            "Optimized for Laptops",
                            lambda i, it: app._on_mic_profile_selection(i, "laptop"),
                            checked=lambda i: app.config.transcription.mic_profile == "laptop",
                            radio=True,
                        ),
                        pystray.MenuItem(
                            "Standard (Original Mic) (Default)",
                            lambda i, it: app._on_mic_profile_selection(i, "none"),
                            checked=lambda i: app.config.transcription.mic_profile == "none",
                            radio=True,
                        ),
                    ),
                    enabled=lambda i: _supports_mic_profile(app),
                ),
                pystray.MenuItem(
                    lambda it: (
                        "Punctuation (automatic)"
                        if _uses_modern_assemblyai(app)
                        else "Format Final Text"
                    ),
                    app._on_toggle_realtime_punctuation_clicked,
                    checked=lambda i: (
                        _uses_modern_assemblyai(app)
                        or app.config.providers.assemblyai.advanced.format_text
                    ),
                    # AssemblyAI specific feature
                    enabled=lambda i: (
                        app.current_provider == "assemblyai" and not _uses_modern_assemblyai(app)
                    ),
                ),
            ),
        )
    )

    # 5. Settings Sub-menu
    menu_items.append(
        pystray.MenuItem(
            "Settings",
            pystray.Menu(
                pystray.MenuItem(
                    "API Credentials",
                    pystray.Menu(
                        pystray.MenuItem(
                            "Set OpenAI Key...",
                            lambda i, it: app._on_set_key_clicked("openai_api_key", "OpenAI"),
                        ),
                        pystray.MenuItem(
                            "Set AssemblyAI Key...",
                            lambda i, it: app._on_set_key_clicked(
                                "assemblyai_api_key", "AssemblyAI"
                            ),
                        ),
                        pystray.MenuItem(
                            "Set Cloudflare API Token...",
                            lambda i, it: app._on_set_key_clicked(
                                "cloudflare_api_token", "Cloudflare API Token"
                            ),
                        ),
                    ),
                ),
                pystray.MenuItem(
                    "Configure Cloudflare Gateway...", app._on_cloudflare_settings_clicked
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
            ),
        )
    )

    # 6. Tools Sub-menu
    menu_items.append(
        pystray.MenuItem(
            "Tools",
            pystray.Menu(
                pystray.MenuItem("1. Open Configuration File", app._open_config),
                pystray.MenuItem(
                    "2. Load Configuration",
                    app._on_reload_config_clicked,
                    enabled=lambda it: app.state in (AppState.IDLE, AppState.ERROR),
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Open Logs Folder", app._open_log_folder),
            ),
        )
    )

    # 7. Help & Exit
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
