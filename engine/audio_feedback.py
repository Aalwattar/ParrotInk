import os
import winsound
import threading
from pathlib import Path
from engine.logging import get_logger

logger = get_logger("AudioFeedback")

def _play_sync(path: str):
    """Internal synchronous playback."""
    try:
        if not os.path.exists(path):
            logger.warning(f"Sound file not found: {path}")
            return
        
        # SND_FILENAME: path is a filename
        # SND_NODEFAULT: don't play default sound if file missing
        # SND_ASYNC: return immediately
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_NODEFAULT)
    except Exception as e:
        logger.error(f"Error playing sound {path}: {e}")

def play_sound(path: str, volume: float = 0.5):
    """
    Play a WAV sound file asynchronously.
    Note: winsound.PlaySound does not natively support volume levels per-call.
    It uses the system volume.
    """
    # We launch in a thread to ensure it's non-blocking to the main logic
    threading.Thread(target=_play_sync, args=(path,), daemon=True).start()
