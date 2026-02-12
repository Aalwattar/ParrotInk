import sys
import time

from engine.indicator_ui import IndicatorWindow


def run_test(style):
    print(f"\n--- Testing Style: {style.upper()} ---")
    win = IndicatorWindow(design_style=style)
    win.start()
    time.sleep(1)
    win.show()
    win.update_status(True)
    win.update_partial_text(f"Testing the {style} design style...")
    time.sleep(4)
    win.update_status(False)
    win.update_partial_text("Design standby mode.")
    time.sleep(2)
    win.hide()
    win.stop()
    time.sleep(1)


if __name__ == "__main__":
    styles = ["glass", "vibrant", "minimal"]
    for s in styles:
        run_test(s)

    print("\nAll tests complete. Which one did you prefer?")
    sys.exit(0)
