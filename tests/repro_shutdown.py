import threading
import time

from engine.ui import TrayApp


def reproduce_shutdown():
    print("Starting TrayApp in thread...", flush=True)
    app = TrayApp()

    # Use a dummy icon run to avoid blocking if possible,
    # but TrayApp.run() is blocking.
    ui_thread = threading.Thread(target=app.run, daemon=True)
    ui_thread.start()

    time.sleep(2)

    print("Calling app.stop() from main thread...", flush=True)
    app.stop()

    ui_thread.join(timeout=2)
    if ui_thread.is_alive():
        print("UI thread still alive after timeout.")
    else:
        print("UI thread exited cleanly.")


if __name__ == "__main__":
    reproduce_shutdown()
