import asyncio
import time
from typing import Optional

from engine.injector import SmartInjector, inject_text
from engine.logging import get_logger

logger = get_logger("Injection")


class InjectionController:
    """
    Manages the safe injection of transcribed text into the focused window.
    Handles locking and suppression windows to avoid feedback loops.
    """

    def __init__(self):
        self.lock = asyncio.Lock()
        self.injector = SmartInjector()
        self._is_injecting: bool = False
        self.last_injection_time: float = 0.0
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    @property
    def is_injecting(self) -> bool:
        return self._is_injecting

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

    async def smart_inject(self, text: str, is_final: bool = False):
        """Injects text using the stateful SmartInjector."""
        if not self.loop:
            return

        async with self.lock:
            self._is_injecting = True
            try:
                # Note: SmartInjector handles its own delta calculation
                await self.loop.run_in_executor(None, self.injector.inject, text, is_final)
            finally:
                self._is_injecting = False
                self.last_injection_time = time.time()

    async def raw_inject(self, text: str):
        """Injects text directly without stateful management."""
        if not self.loop:
            return

        async with self.lock:
            logger.debug(f"Injecting raw text: {text}")
            t0 = time.perf_counter()
            await self.loop.run_in_executor(None, inject_text, text)
            t1 = time.perf_counter()
            logger.debug(f"Raw injection call completed in {(t1 - t0) * 1000:.2f}ms")
            self.last_injection_time = time.time()
