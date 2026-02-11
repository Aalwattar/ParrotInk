import os
import threading
import winsound

from engine.logging import get_logger

logger = get_logger("AudioFeedback")


def play_sound(path: str, volume: float = 0.5):
    """
    Play a WAV sound file asynchronously.
    """
    try:
        if not os.path.exists(path):
            logger.warning(f"Sound file not found: {path}")
            return

        # SND_FILENAME: path is a filename
        # SND_NODEFAULT: don't play default sound if file missing
        # SND_ASYNC: return immediately without needing a separate thread
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_NODEFAULT | winsound.SND_ASYNC)
    except Exception as e:
        logger.error(f"Error playing sound {path}: {e}")
