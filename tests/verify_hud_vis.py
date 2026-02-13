import logging
import threading
import time

from engine.hud_renderer import HudOverlay

logging.basicConfig(level=logging.INFO)


def run_hud():
    hud = HudOverlay()
    print("Starting HUD run loop...")
    # Force visible
    hud.visible = True
    # Start thread
    t = threading.Thread(target=hud.run, daemon=True)
    t.start()

    time.sleep(1)
    if not hud._hwnd:
        print("HWND is NULL after 1s!")
        return

    print(f"HWND: {hud._hwnd}")
    hud.show()
    print("Called show()")

    hud.update_status(True)
    hud.update_partial_text("DIAGNOSTIC TEST")
    print("Sent text update")

    # Keep alive for 5 seconds
    for i in range(5):
        print(f"HUD Alive... {5 - i}")
        time.sleep(1)

    hud.stop()
    print("Stopped")


if __name__ == "__main__":
    run_hud()
