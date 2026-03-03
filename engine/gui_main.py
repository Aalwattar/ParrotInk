from __future__ import annotations

import asyncio
import signal
import sys
import threading

from engine.config import ConfigError, load_config
from engine.constants import (
    STATUS_CONFIG_UPDATED,
    STATUS_RELOAD_FAILED,
    STATUS_RELOADING,
)
from engine.logging import configure_logging, get_logger
from engine.security import SecurityManager
from engine.ui_bridge import UIBridge

# Import coordinator from main to keep logic central
from main import AppCoordinator

logger = get_logger("GUI")


async def main_gui(cli_args):
    try:
        config = load_config()
    except ConfigError as e:
        print(f"\n[CONFIGURATION ERROR] {e}", file=sys.stderr)
        return

    # CLI overrides config for file path if provided
    if cli_args.log_file:
        config.logging.file_path = cli_args.log_file
        config.logging.file_enabled = True

    configure_logging(config, verbose_count=cli_args.verbose, quiet=cli_args.quiet)

    ui_bridge = UIBridge()
    coordinator = AppCoordinator(config, ui_bridge)
    coordinator.loop = asyncio.get_running_loop()

    # Shared event to signal main loop exit
    exit_event = asyncio.Event()

    async def trigger_shutdown(reason: str):
        await coordinator.shutdown(reason)
        exit_event.set()

    def on_quit():
        if coordinator.loop:
            coordinator.loop.call_soon_threadsafe(
                lambda: asyncio.create_task(trigger_shutdown("Tray Exit"))
            )

    def on_sigint(sig, frame):
        logger.info("SIGINT (Ctrl+C) received.")
        if coordinator.loop:
            coordinator.loop.call_soon_threadsafe(
                lambda: asyncio.create_task(trigger_shutdown("SIGINT"))
            )

    signal.signal(signal.SIGINT, on_sigint)
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, on_sigint)

    def on_provider_change(provider_name):
        def apply():
            # Senior Architecture: The AppCoordinator._on_config_changed
            # will detect the provider name change and trigger a silent stop
            # of any active recording sessions.
            # Notify UI of switching immediately
            ui_bridge.update_status_message(f"Switching to {provider_name}...")

            config.update_and_save({"transcription": {"provider": provider_name}})
            logger.info(f"Provider changed to: {provider_name}")
            ui_bridge.update_provider(provider_name)
            ui_bridge.refresh_hud()

        if coordinator.loop:
            coordinator.loop.call_soon_threadsafe(apply)

    def on_set_key(account_id, key):
        def apply():
            SecurityManager.set_key(account_id, key)
            logger.info(f"API Key updated for: {account_id}")
            ui_bridge.update_availability(coordinator.get_provider_availability())
            ui_bridge.notify(
                f"API Key for {account_id.replace('_api_key', '').title()} "
                "has been saved securely.",
                "Key Saved",
            )

        if coordinator.loop:
            coordinator.loop.call_soon_threadsafe(apply)

    def on_toggle_sounds(enabled):
        def apply():
            config.update_and_save({"interaction": {"sounds": {"enabled": enabled}}})
            logger.info(f"Audio feedback {'enabled' if enabled else 'disabled'}")

        if coordinator.loop:
            coordinator.loop.call_soon_threadsafe(apply)

    def on_toggle_hud(enabled):
        def apply():
            config.update_and_save({"ui": {"floating_indicator": {"enabled": enabled}}})
            logger.info(f"HUD {'enabled' if enabled else 'disabled'}")
            ui_bridge.refresh_hud()

        if coordinator.loop:
            coordinator.loop.call_soon_threadsafe(apply)

    def on_toggle_click_through(enabled):
        def apply():
            config.update_and_save({"ui": {"floating_indicator": {"click_through": enabled}}})
            logger.info(f"HUD click-through {'enabled' if enabled else 'disabled'}")
            ui_bridge.update_settings({"click_through": enabled})

        if coordinator.loop:
            coordinator.loop.call_soon_threadsafe(apply)

    def on_toggle_startup(enabled):
        def apply():
            from engine.platform_win.startup import set_run_at_startup

            config.update_and_save({"interaction": {"run_at_startup": enabled}})
            set_run_at_startup(enabled)
            logger.info(f"Run at Startup {'enabled' if enabled else 'disabled'}")

        if coordinator.loop:
            coordinator.loop.call_soon_threadsafe(apply)

    def on_toggle_hold_mode(enabled):
        def apply():
            config.update_and_save({"hotkeys": {"hold_mode": enabled}})
            logger.info(f"Hold to Talk {'enabled' if enabled else 'disabled'}")
            # Update and Restart the listener to apply mode change
            coordinator.input_monitor.set_hotkey(config.hotkeys.hotkey, enabled)
            coordinator.input_monitor.start()

        if coordinator.loop:
            coordinator.loop.call_soon_threadsafe(apply)

    def on_mic_profile_change(profile):
        def apply():
            config.update_and_save({"transcription": {"mic_profile": profile}})
            logger.info(f"Microphone Profile changed to: {profile}")

        if coordinator.loop:
            coordinator.loop.call_soon_threadsafe(apply)

    def on_before_hotkey_change():
        logger.info("Pausing hooks for hotkey recording...")
        # 1. Stop dictation immediately
        asyncio.run_coroutine_threadsafe(coordinator.stop_listening(), coordinator.loop)
        # 2. Stop the global pynput listener
        coordinator.input_monitor.stop()

    def on_hotkey_change(new_hotkey):
        def apply():
            logger.info(f"Applying new hotkey: {new_hotkey}")
            config.update_and_save({"hotkeys": {"hotkey": new_hotkey}})
            # Update and Restart the listener
            coordinator.input_monitor.set_hotkey(new_hotkey, config.hotkeys.hold_mode)
            coordinator.input_monitor.start()

        if coordinator.loop:
            coordinator.loop.call_soon_threadsafe(apply)

    def on_reload_config():
        def apply():
            try:
                logger.info("Manual configuration reload triggered.")
                ui_bridge.update_status_message(STATUS_RELOADING)
                config.reload()
                ui_bridge.update_status_message(STATUS_CONFIG_UPDATED)
                # Clear status after a short delay
                if coordinator.loop:
                    coordinator.loop.call_later(
                        3.0,
                        lambda: ui_bridge.update_status_message(
                            coordinator.state.name.capitalize()
                        ),
                    )
            except ConfigError as e:
                logger.error(f"Failed to reload config: {e}")
                ui_bridge.update_status_message(STATUS_RELOAD_FAILED)
                # Clear status after a short delay
                if coordinator.loop:
                    coordinator.loop.call_later(
                        5.0,
                        lambda: ui_bridge.update_status_message(
                            coordinator.state.name.capitalize()
                        ),
                    )
                import ctypes

                msg = f"Failed to reload configuration:\n\n{e}"
                # MB_OK (0) | MB_ICONERROR (0x10) | MB_TOPMOST (0x40000)
                ctypes.windll.user32.MessageBoxW(0, msg, "Configuration Error", 0x10 | 0x40000)

        if coordinator.loop:
            coordinator.loop.call_soon_threadsafe(apply)

    def on_check_updates():
        def apply():
            logger.info("Manual update check triggered.")
            ui_bridge.update_status_message("Checking for updates...")
            threading.Thread(target=coordinator.update_manager.check_now, daemon=True).start()
            # If no update found, status will eventually clear by normal transitions
            # but we can force it after a delay if still idle
            if coordinator.loop:
                coordinator.loop.call_later(
                    3.0,
                    lambda: (
                        ui_bridge.update_status_message(coordinator.state.name.capitalize())
                        if ui_bridge.queue.empty()
                        else None
                    ),
                )

        if coordinator.loop:
            coordinator.loop.call_soon_threadsafe(apply)

    from engine.ui import TrayApp

    app = TrayApp(
        config=config,
        bridge=ui_bridge,
        on_quit_callback=on_quit,
        on_provider_change=on_provider_change,
        on_set_key=on_set_key,
        on_toggle_sounds=on_toggle_sounds,
        on_hotkey_change=on_hotkey_change,
        on_before_hotkey_change=on_before_hotkey_change,
        on_toggle_hud=on_toggle_hud,
        on_toggle_click_through=on_toggle_click_through,
        on_toggle_startup=on_toggle_startup,
        on_toggle_hold_mode=on_toggle_hold_mode,
        on_mic_profile_change=on_mic_profile_change,
        on_reload_config=on_reload_config,
        on_check_updates=on_check_updates,
        initial_provider=config.transcription.provider,
        initial_sounds_enabled=config.interaction.sounds.enabled,
        availability=coordinator.get_provider_availability(),
    )

    ui_thread = threading.Thread(target=app.run, name="UIThread", daemon=False)
    ui_thread.start()

    # The monitor is configured during coordinator init, but we start it here
    # to begin capturing global events before the main loop blocks.
    coordinator.input_monitor.start()
    logger.info(
        f"Hotkey listener started: {config.hotkeys.hotkey} (hold_mode={config.hotkeys.hold_mode})"
    )

    logger.info("Application running. Use Ctrl+C or Tray Exit to quit.")

    try:
        await exit_event.wait()
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("Main loop exited. Starting cleanup...")
        coordinator.input_monitor.stop()

        # Explicitly stop the UI app to break its internal loops
        # Senior Architecture: Check if it's already stopping to avoid double-call races
        app.stop()

        # Wait for UI thread to finish
        if ui_thread.is_alive():
            logger.info("Waiting for UI thread to finalize...")
            ui_thread.join(timeout=5.0)

        await coordinator.shutdown("Finalizing")

        # CRITICAL: Close logging to prevent 'buffered busy' crash
        from engine.logging import close_logging

        close_logging()
