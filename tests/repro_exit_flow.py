import asyncio
import time

from engine.config import load_config
from engine.ui_bridge import UIBridge
from main import AppCoordinator


async def run_test():
    print("Testing Centralized Shutdown Flow...")
    config = load_config()
    ui_bridge = UIBridge()
    coordinator = AppCoordinator(config, ui_bridge)
    coordinator.loop = asyncio.get_running_loop()

    # Simulate a running state
    coordinator.is_listening = True

    print("Triggering shutdown...")
    # This should call stop_listening and finish
    start_time = time.time()
    await coordinator.shutdown("Test Exit")
    end_time = time.time()

    duration = end_time - start_time
    print(f"Shutdown took {duration:.2f} seconds")

    assert not coordinator.is_listening
    assert duration < 5.0
    print("Shutdown flow SUCCESS")


if __name__ == "__main__":
    asyncio.run(run_test())
