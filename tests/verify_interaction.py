import time

from engine.interaction import InteractionMonitor


def main():
    monitor = InteractionMonitor()

    # Define what happens when a key is pressed
    def on_trigger():
        print("\n[SUCCESS] Key Press Detected! Trigger working correctly.")

    monitor.set_any_key_callback(on_trigger)

    print("Starting Interaction Monitor...")
    print("Press ANY key (Shift, Ctrl, A, Space, etc.) to test.")
    print("Press Ctrl+C to exit this test.")

    monitor.start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping monitor...")
    finally:
        monitor.stop()


if __name__ == "__main__":
    main()
