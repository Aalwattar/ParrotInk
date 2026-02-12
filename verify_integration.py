import asyncio
import threading
import time

from engine.app_types import AppState
from engine.ui import TrayApp
from engine.ui_bridge import UIBridge


async def simulate_coordinator(bridge):
    print("Coordinators: Setting state to LISTENING...")
    bridge.set_state(AppState.LISTENING)

    time.sleep(2)
    print("Coordinators: Sending partial text...")
    bridge.update_partial_text("Hello world testing indicator")

    time.sleep(3)
    print("Coordinators: Sending more text...")
    bridge.update_partial_text("this is a long sentence that should overflow the buffer")

    time.sleep(5)
    print("Coordinators: Setting state to IDLE...")
    bridge.set_state(AppState.IDLE)

    time.sleep(2)
    print("Coordinators: Stopping UI...")
    bridge.stop()


if __name__ == "__main__":
    from engine.config import Config

    config = Config()
    bridge = UIBridge()
    app = TrayApp(config=config, bridge=bridge)

    # Run UI in thread
    ui_thread = threading.Thread(target=app.run, daemon=True)
    ui_thread.start()

    # Run simulation
    asyncio.run(simulate_coordinator(bridge))

    print("Integration test complete.")
