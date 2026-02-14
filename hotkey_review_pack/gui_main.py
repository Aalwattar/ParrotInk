import asyncio
import sys

from engine.logging import get_logger
from engine.ui_bridge import UIBridge

logger = get_logger("GUI")


async def main_gui(cli_args):
    # Late import to ensure logging is configured
    from engine.config import ConfigError, load_config
    from main import AppCoordinator

    try:
        config = load_config()
    except ConfigError as e:
        print(f"\n[CONFIGURATION ERROR] {e}", file=sys.stderr)
        return

    ui_bridge = UIBridge()
    coordinator = AppCoordinator(config, ui_bridge)
    loop = asyncio.get_running_loop()
    coordinator.loop = loop

    def on_quit():
        logger.info("Initiating shutdown (reason: tray quit)...")
        asyncio.run_coroutine_threadsafe(coordinator.shutdown(), loop)

    def on_provider_change(provider):
        config.update_and_save({"transcription": {"provider": provider}})
        logger.info(f"Switched provider to {provider}")

    def on_set_key(account_id, key):
        from engine.security import SecurityManager

        SecurityManager.set_key(account_id, key)
        logger.info(f"Updated key for {account_id}")
        ui_bridge.update_availability(coordinator.get_provider_availability())

    def on_toggle_sounds(enabled):
        config.interaction.sounds.enabled = enabled
        logger.info(f"Audio feedback {'enabled' if enabled else 'disabled'}")

    def on_toggle_hud(enabled):
        config.update_and_save({"ui": {"floating_indicator": {"enabled": enabled}}})
        logger.info(f"HUD {'enabled' if enabled else 'disabled'}")
        if enabled and not app.indicator:
            try:
                from .indicator_ui import IndicatorWindow

                app.indicator = IndicatorWindow(config=config)
                app.indicator.start()
            except Exception as e:
                logger.error(f"Failed to initialize HUD: {e}")

    def on_toggle_click_through(enabled):
        config.update_and_save({"ui": {"floating_indicator": {"click_through": enabled}}})
        logger.info(f"HUD click-through {'enabled' if enabled else 'disabled'}")

    def on_before_hotkey_change():
        """Pauses systems before the recording dialog blocks the UI thread."""
        logger.info("Pausing global inputs for hotkey recording...")
        # Clean up any active session and stop global hooks immediately
        asyncio.run_coroutine_threadsafe(coordinator.stop_listening(), loop)
        coordinator.input_monitor.stop()

    def on_hotkey_change(new_hotkey):
        """Called when a new hotkey is captured."""

        def apply_change():
            logger.info(f"Applying new hotkey: {new_hotkey}")
            # 1. Update config (this will notify coordinator variable internally)
            config.update_and_save({"hotkeys": {"hotkey": new_hotkey}})
            # 2. Restart the global hotkey listener
            coordinator.input_monitor.start()

        # Ensure all app state changes happen on the Main loop thread
        loop.call_soon_threadsafe(apply_change)

    # Import TrayApp here to keep gui_main decoupled
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

    # Allow app to access coordinator for state management
    # Note: TrayApp handles on_hotkey_change which triggers stop_listening
    app.coordinator = coordinator  # type: ignore

    logger.info(
        f"Hotkey listener started: {config.hotkeys.hotkey} (hold_mode={config.hotkeys.hold_mode})"
    )

    # Initialize Floating Indicator if enabled
    if config.ui.floating_indicator.enabled:
        logger.info("Initializing Floating Indicator...")
        try:
            from .indicator_ui import IndicatorWindow

            app.indicator = IndicatorWindow(config=config)
            app.indicator.start()
        except Exception as e:
            logger.error(f"Failed to initialize HUD: {e}")

    # Start services
    coordinator.input_monitor.start()
    coordinator.mouse_monitor.start()

    logger.info("Application running. Use Ctrl+C or Tray Exit to quit.")

    # Run the TrayApp (non-blocking now)
    await app.run()
