import sys

from engine.ui import TrayApp


def main():
    print("Starting Voice2Text...")
    print("Press Ctrl+C in this terminal or select 'Quit' from the tray icon to exit.")

    app = TrayApp()

    try:
        app.run()
    except KeyboardInterrupt:
        app.stop()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
