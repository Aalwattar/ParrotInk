import signal
import sys

from engine.ui import TrayApp


def main():
    print("Starting Voice2Text...")

    app = TrayApp()

    # Define a clean shutdown function
    def shutdown(sig, frame):
        print("\nInterrupt received! Shutting down immediately...")
        app.stop()
        sys.exit(0)

    # Register the signal handler for immediate response
    signal.signal(signal.SIGINT, shutdown)

    print("System Tray is active. Select 'Quit' or press Ctrl+C to exit.")

    # Run the tray icon in the main thread's loop
    # (pystray's run() method is usually the one that needs to own the main thread on some OSs)
    # To keep the main thread responsive to signals, we can use run_detached()
    # if supported, or just let it run and trust the signal handler.
    try:
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
