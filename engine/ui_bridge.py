import queue
import time
from typing import Any, Dict, Optional

from engine.app_types import AppState
from engine.logging import get_logger

logger = get_logger("UIBridge")


class UIEvent:
    SET_STATE = "set_state"
    NOTIFY = "notify"
    UPDATE_AVAILABILITY = "update_availability"
    UPDATE_PARTIAL_TEXT = "update_partial_text"
    UPDATE_FINAL_TEXT = "update_final_text"
    UPDATE_VOICE_ACTIVITY = "update_voice_activity"
    UPDATE_STATUS_MESSAGE = "update_status_message"
    UPDATE_PROVIDER = "update_provider"
    UPDATE_SETTINGS = "update_settings"
    REFRESH_HUD = "refresh_hud"
    CLEAR_HUD = "clear_hud"
    RECORD_STATS = "record_stats"
    UPDATE_VERSION_NOTIFICATION = "update_version_notification"
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
        self.queue.put((UIEvent.UPDATE_PARTIAL_TEXT, text))

    def update_voice_activity(self, active: bool):
        self.queue.put((UIEvent.UPDATE_VOICE_ACTIVITY, active))

    def update_final_text(self, text: str):
        self._last_final_time = time.time()
        self.queue.put((UIEvent.UPDATE_FINAL_TEXT, text))

    def notify(self, message: str, title: str = "ParrotInk"):
        self.queue.put((UIEvent.NOTIFY, (message, title)))

    def update_availability(self, availability: Dict[str, bool]):
        self.queue.put((UIEvent.UPDATE_AVAILABILITY, availability))

    def update_status_message(self, message: str):
        self.queue.put((UIEvent.UPDATE_STATUS_MESSAGE, message))

    def update_provider(self, provider_name: str):
        self.queue.put((UIEvent.UPDATE_PROVIDER, provider_name))

    def update_settings(self, settings: Dict[str, Any]):
        self.queue.put((UIEvent.UPDATE_SETTINGS, settings))

    def refresh_hud(self):
        """Signal the HUD to refresh its settings."""
        self.queue.put((UIEvent.REFRESH_HUD, None))

    def clear_hud(self):
        """Signal the HUD to clear its state."""
        self.queue.put((UIEvent.CLEAR_HUD, None))

    def record_stats(self, duration: float, words: int, provider: str, error: bool = False):
        """Signal the UI to record session statistics."""
        data = {"duration": duration, "words": words, "provider": provider, "error": error}
        self.queue.put((UIEvent.RECORD_STATS, data))

    def update_version_notification(self, version_tag: str, release_url: str):
        """Signal the UI that a new version is available."""
        self.queue.put((UIEvent.UPDATE_VERSION_NOTIFICATION, (version_tag, release_url)))

    def stop(self):
        """Signal the UI to stop."""
        self.queue.put((UIEvent.QUIT, None))

    def get_event(self, block: bool = False, timeout: Optional[float] = None):
        try:
            return self.queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None
