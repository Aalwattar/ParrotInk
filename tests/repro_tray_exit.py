import threading
import time

from engine.ui import TrayApp


def test_tray_exit_hang():
    # Simulate the logic in main.py
    should_exit = False

    def on_quit():
        nonlocal should_exit
        # This is what currently happens when 'Quit' is clicked:
        # TrayApp calls its stop() which calls this callback.
        print("Quit callback triggered.", flush=True)
        # Note: In the bugged version, main.py might not be looking at this
        # or we might not have passed this callback correctly.
        should_exit = True

    app = TrayApp(on_quit_callback=on_quit)

    print("Starting UI thread...", flush=True)
    ui_thread = threading.Thread(target=app.run, daemon=True)
    ui_thread.start()

    time.sleep(1)

    print("Simulating 'Quit' click by calling app.stop()...", flush=True)
    # This simulates the user clicking Quit in the tray
    app.stop()

    print("Main loop waiting for should_exit flag...", flush=True)
    start_wait = time.time()
    while not should_exit and (time.time() - start_wait < 3):
        time.sleep(0.1)

    if should_exit:
        print("SUCCESS: Main loop recognized exit.")
    else:
        print("FAILURE: Main loop timed out (Hang).")


if __name__ == "__main__":
    test_tray_exit_hang()
