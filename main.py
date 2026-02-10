import signal
import threading
import time

from engine.signals import ShutdownHandler
from engine.ui import TrayApp


def main():
    print("Starting Voice2Text...", flush=True)

    handler = ShutdownHandler(window=3.0)
    app = TrayApp(on_quit_callback=lambda: setattr(handler, "should_exit", True))

    # Register the signal handler
    signal.signal(signal.SIGINT, handler.handle)

    # Start the UI in a background thread
    print("Starting UI thread...", flush=True)
    ui_thread = threading.Thread(target=app.run, daemon=True)
    ui_thread.start()

    print("System Tray is active. Press Ctrl+C to exit.", flush=True)

    # Wait for the shutdown signal
    try:
        while not handler.should_exit:
            time.sleep(0.1)
    except KeyboardInterrupt:
        # This handles cases where the handler might not be triggered correctly
        print("\nShutdown forced.", flush=True)

    print("Shutting down...", flush=True)
    app.stop()

    # Wait for UI thread to finish with a timeout
    ui_thread.join(timeout=2.0)
    if ui_thread.is_alive():
        print("Warning: UI thread did not terminate within 2 seconds.", flush=True)
        print("Forcing exit.", flush=True)
    else:
        print("Exited cleanly.", flush=True)


if __name__ == "__main__":
    main()
