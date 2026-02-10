import queue
from typing import Generator

import numpy as np
import sounddevice as sd


class AudioStreamer:
    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.queue: queue.Queue[np.ndarray] = queue.Queue()
        self.is_running = False
        self._stream: sd.InputStream | None = None

    def _callback(self, indata: np.ndarray, frames: int, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(f"Audio status warning: {status}")
        self.queue.put(indata.copy())

    def start(self):
        """Starts the audio capture stream."""
        if self.is_running:
            return

        # sounddevice starts a background thread for the callback.
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=self.chunk_size,
            callback=self._callback,
        )
        self._stream.start()
        self.is_running = True
        print(f"Audio capture started at {self.sample_rate}Hz...")

    def stop(self):
        """Stops the audio capture stream."""
        if not self.is_running:
            return

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        self.is_running = False
        print("Audio capture stopped.")

    def generator(self) -> Generator[np.ndarray, None, None]:
        """Yields audio chunks from the queue."""
        while self.is_running:
            try:
                # Use a timeout to avoid blocking indefinitely so we can check is_running
                chunk = self.queue.get(timeout=0.1)
                yield chunk
            except queue.Empty:
                continue
