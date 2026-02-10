import os
import signal
import threading
import time

import pystray
from PIL import Image


def create_image():
    image = Image.new("RGB", (64, 64), "black")
    return image


def test_responsiveness():
    shutdown_called = False

    def handler(sig, frame):
        nonlocal shutdown_called
        print("\nCaught SIGINT!", flush=True)
        shutdown_called = True

    signal.signal(signal.SIGINT, handler)

    icon = pystray.Icon("test", create_image(), "Test")

    print("Starting icon loop in background thread...", flush=True)
    ui_thread = threading.Thread(target=icon.run, daemon=True)
    ui_thread.start()

    print("Main thread waiting. Sending SIGINT to self in 1 second...", flush=True)

    def send_sig():
        time.sleep(1)
        print("Sending SIGINT...", flush=True)
        os.kill(os.getpid(), signal.SIGINT)

    threading.Thread(target=send_sig, daemon=True).start()

    # Wait for a few seconds to see if we can catch a signal
    start_time = time.time()
    while time.time() - start_time < 5:
        if shutdown_called:
            break
        time.sleep(0.1)

    icon.stop()
    ui_thread.join(timeout=2)

    if shutdown_called:
        print("Success: Main thread caught SIGINT.")
    else:
        print("Failure: Main thread did not catch SIGINT within timeout.")


if __name__ == "__main__":
    test_responsiveness()
