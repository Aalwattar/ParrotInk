from __future__ import annotations

import asyncio
import signal
import sys
import threading

from engine.config import ConfigError, load_config
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
        logger.info("Tray 'Quit' selected.")
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

    def on_provider_change(provider_name):
        if coordinator.is_listening or coordinator.is_connecting:
            logger.info(f"Stopping active session before changing provider to {provider_name}")
            asyncio.run_coroutine_threadsafe(coordinator.stop_listening(), coordinator.loop)
        elif coordinator.provider:
            # If we have an idle (WARM) provider, stop it so the next connect uses the new one
            logger.info(f"Stopping idle provider before changing to {provider_name}")
            asyncio.run_coroutine_threadsafe(coordinator.provider.stop(), coordinator.loop)
            coordinator.provider = None

        config.transcription.provider = provider_name
        logger.info(f"Provider changed to: {provider_name}")

    def on_set_key(account_id, key):
        SecurityManager.set_key(account_id, key)
        logger.info(f"API Key updated for: {account_id}")
        ui_bridge.update_availability(coordinator.get_provider_availability())
        ui_bridge.notify(
            f"API Key for {account_id.replace('_api_key', '').title()} has been saved securely.",
            "Key Saved",
        )

    def on_toggle_sounds(enabled):
        config.interaction.sounds.enabled = enabled
        logger.info(f"Audio feedback {'enabled' if enabled else 'disabled'}")

    def on_toggle_hud(enabled):
        config.update_and_save({"ui": {"floating_indicator": {"enabled": enabled}}})
        logger.info(f"HUD {'enabled' if enabled else 'disabled'}")
        # Initialize indicator if enabling for the first time
        if enabled and not app.indicator:
            logger.info("Lazy-initializing HUD Indicator...")
            try:
                from .indicator_ui import IndicatorWindow

                app.indicator = IndicatorWindow(config=config)
                app.indicator.start()
            except Exception as e:
                logger.error(f"Failed to initialize HUD: {e}")

    def on_toggle_click_through(enabled):
        config.update_and_save({"ui": {"floating_indicator": {"click_through": enabled}}})
        logger.info(f"HUD click-through {'enabled' if enabled else 'disabled'}")

    loop = asyncio.get_running_loop()

    def on_before_hotkey_change():
        if coordinator:
            logger.info("Pausing global inputs for hotkey recording...")
            # Stop active recording if any
            asyncio.run_coroutine_threadsafe(coordinator.stop_listening(), loop)
            # Stop the global pynput listener so it doesn't conflict with the dialog
            coordinator.input_monitor.stop()

    def on_hotkey_change(new_hotkey):
        # Update config
        config.update_and_save({"hotkeys": {"hotkey": new_hotkey}})

        # Restart the global listener with the new hotkey active
        if coordinator:
            logger.info("Resuming global inputs...")
            coordinator.input_monitor.start()

    # Import TrayApp here to keep gui_main decoupled from other modules until needed
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
        initial_provider=config.transcription.provider,
        initial_sounds_enabled=config.interaction.sounds.enabled,
        availability=coordinator.get_provider_availability(),
    )

    ui_thread = threading.Thread(target=app.run, daemon=True)
    ui_thread.start()

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
        # Ensure shutdown is called if we exited wait() for some other reason
        coordinator.input_monitor.stop()  # Stop listener first to prevent new events
        await coordinator.shutdown("Finalizing")
