import queue
import time
from typing import Dict, Optional

from engine.app_types import AppState
from engine.logging import get_logger

logger = get_logger("UIBridge")


class UIEvent:
    SET_STATE = "set_state"
    NOTIFY = "notify"
    UPDATE_AVAILABILITY = "update_availability"
    UPDATE_PARTIAL_TEXT = "update_partial_text"
    UPDATE_FINAL_TEXT = "update_final_text"
    QUIT = "quit"


class UIBridge:
    """
    A thread-safe bridge that decouples the AppCoordinator from the UI.
    The Coordinator pushes events into a queue, and the UI polls the queue.
    """

    def __init__(self):
        self.queue = queue.Queue()
        self._last_final_time = 0.0

    def set_state(self, state: AppState):
        self.queue.put((UIEvent.SET_STATE, state))

    def update_partial_text(self, text: str):
        # OPTIMIZATION: If a final result was just received (e.g. within 300ms),
        # ignore partials that might be racing it from the same phrase.
        if time.time() - self._last_final_time < 0.3:
            return
        self.queue.put((UIEvent.UPDATE_PARTIAL_TEXT, text))

    def update_final_text(self, text: str):
        self._last_final_time = time.time()
        self.queue.put((UIEvent.UPDATE_FINAL_TEXT, text))

    def notify(self, message: str, title: str = "Voice2Text"):
        self.queue.put((UIEvent.NOTIFY, (message, title)))

    def update_availability(self, availability: Dict[str, bool]):
        self.queue.put((UIEvent.UPDATE_AVAILABILITY, availability))

    def stop(self):
        """Signal the UI to stop."""
        self.queue.put((UIEvent.QUIT, None))

    def get_event(self, block: bool = False, timeout: Optional[float] = None):
        try:
            return self.queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None
