import asyncio
import threading
import time
from concurrent.futures import Future
from typing import Callable, Optional

from engine.anchor import Anchor
from engine.injector import SmartInjector
from engine.logging import get_logger

logger = get_logger("Injection")


class InjectionController:
    """
    Manages the safe injection of transcribed text into the focused window.
    Handles locking and suppression windows to avoid feedback loops.
    """

    def __init__(self, on_target_lost: Callable[[], None] | None = None):
        self.lock = asyncio.Lock()
        self.injector = SmartInjector()
        self._is_injecting: bool = False
        self.last_injection_time: float = 0.0
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._target: Anchor | None = None
        self._cancelled = False
        self._error: BaseException | None = None
        self._session: object | None = None
        self._pending: set[Future[None]] = set()
        self._pending_lock = threading.Lock()
        self._worker_lock = threading.Lock()
        self._on_target_lost = on_target_lost

    @property
    def target(self) -> Anchor | None:
        return self._target

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    @property
    def pending_count(self) -> int:
        with self._pending_lock:
            return len(self._pending)

    def begin(self, target: Anchor | None):
        """Bind new output to a target, invalidating work from the previous session."""
        self.cancel()
        self._target = target
        self._session = object()
        self._cancelled = False
        self.injector = SmartInjector()
        self._error = None

    def cancel(self):
        """Immediately reject late text, including workers already waiting to insert."""
        self._cancelled = True
        with self._pending_lock:
            pending = tuple(self._pending)
        for future in pending:
            future.cancel()

    def release(self):
        """Release the target after final output has drained or been cancelled."""
        self._session = None
        self._target = None

    def queue(self, text: str, is_final: bool = False):
        if self.loop is None or self.cancelled or self._session is None:
            return
        session, target = self._session, self.target

        def can_insert():
            if self.cancelled or self._session is not session:
                return False
            focused = target is None or target.has_focus()
            # Focus acquisition can block while cancellation or a new session arrives.
            if self.cancelled or self._session is not session:
                return False
            if not focused:
                self.cancel()
                logger.info("Discarding transcription: editor focus changed before insertion")
                if self._on_target_lost:
                    self._on_target_lost()
                return False
            return True

        future = asyncio.run_coroutine_threadsafe(
            self.smart_inject(text, is_final, can_insert), self.loop
        )
        with self._pending_lock:
            self._pending.add(future)
        future.add_done_callback(lambda completed: self._discard(completed, session))
        if self.cancelled or self._session is not session:
            future.cancel()

    def _discard(self, future: Future[None], session: object):
        with self._pending_lock:
            if not future.cancelled() and self._session is session:
                error = future.exception()
                if error is not None:
                    self._error = error
            self._pending.discard(future)

    async def drain(self):
        """Wait for queued editor writes before the recording target is released."""
        with self._pending_lock:
            pending = tuple(self._pending)
        if pending:
            await asyncio.gather(*(asyncio.wrap_future(f) for f in pending), return_exceptions=True)
        if self._error is not None:
            raise self._error

    @property
    def is_injecting(self) -> bool:
        return self._is_injecting or self._worker_lock.locked()

    async def smart_inject(
        self, text: str, is_final: bool = False, can_insert: Callable[[], bool] | None = None
    ):
        """Injects text using the stateful SmartInjector."""
        if not self.loop:
            return

        async with self.lock:
            self._is_injecting = True
            try:

                def insert():
                    # Check on the worker after waiting for the lock and executor.
                    # Cancelling an asyncio wait cannot stop an already-running worker.
                    with self._worker_lock:
                        if can_insert is None or can_insert():
                            self.injector.inject(text, is_final)

                await self.loop.run_in_executor(None, insert)
            finally:
                self._is_injecting = False
                self.last_injection_time = time.time()
