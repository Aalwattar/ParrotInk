import os
import threading
import wave

import numpy as np
import sounddevice as sd

from engine.logging import get_logger

logger = get_logger("AudioFeedback")


def play_sound(path: str, volume: float = 0.5):
    """
    Play a WAV sound file asynchronously with volume control.
    """
    try:
        resolved_path = path
        if not os.path.exists(resolved_path):
            # Fallback to assets/sounds if it's a relative path or filename
            filename = os.path.basename(path)
            # Try project root assets
            bundled_path = os.path.join("assets", "sounds", filename)
            if os.path.exists(bundled_path):
                resolved_path = bundled_path
            else:
                logger.warning(f"Sound file not found: {path} (bundled: {bundled_path})")
                return

        def _play():
            try:
                with wave.open(resolved_path, "rb") as wf:
                    sample_rate = wf.getframerate()
                    n_channels = wf.getnchannels()
                    sampwidth = wf.getsampwidth()

                    # Read all frames
                    frames = wf.readframes(wf.getnframes())

                    # Convert to numpy array
                    if sampwidth == 2:
                        dtype = np.int16
                    elif sampwidth == 1:
                        dtype = np.uint8
                    else:
                        logger.warning(f"Unsupported sample width: {sampwidth}")
                        return

                    data = np.frombuffer(frames, dtype=dtype)

                    # Normalize to float32 [-1.0, 1.0]
                    if dtype == np.int16:
                        audio = data.astype(np.float32) / 32768.0
                    else:  # uint8
                        audio = (data.astype(np.float32) - 128.0) / 128.0

                    # Reshape if multi-channel
                    if n_channels > 1:
                        audio = audio.reshape(-1, n_channels)

                    # Apply volume using a quadratic taper for natural loudness control
                    # A 0-100 scale is used for simplicity. (volume / 100)**2
                    # provides a good balance between sensitivity and audibility.
                    tapered_volume = (volume / 100.0) ** 2
                    audio *= tapered_volume

                    # Play
                    sd.play(audio, sample_rate)
                    sd.wait()  # Wait for playback to finish in this background thread
            except Exception as inner_e:
                logger.error(f"Error during audio playback thread: {inner_e}")

        # Run in background thread to avoid blocking
        threading.Thread(target=_play, daemon=True).start()

    except Exception as e:
        logger.error(f"Error preparing sound {path}: {e}")
