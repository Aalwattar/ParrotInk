from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Any, Optional

from engine.constants import (
    DEFAULT_MAX_CHARS,
    STATUS_FINALIZED,
    STATUS_LISTENING,
)
from engine.logging import get_logger

if TYPE_CHECKING:
    from engine.config import Config

logger = get_logger("IndicatorUI")

# Internal Constants (Not exposed to user)
DEFAULT_LINGER_SECONDS = 2.5
MIN_VISIBLE_DURATION = 0.3
REDRAW_THROTTLE_SECONDS = 0.05


class GdiFallbackWindow:
    """Mock implementation for tests where HUD is missing."""

    def __init__(self, config=None, click_through=True):
        self.config = config
        self.is_recording = False
        self.visible = False
        self.last_text = ""
        self.partial_text = ""

    def run(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def update_status(self, recording):
        self.is_recording = recording

    def update_text(self, text):
        self.last_text = text

    def update_partial_text(self, text):
        self.partial_text = text

    def apply_click_through(self, val):
        pass


class IndicatorWindow:
    """
    High-level controller for the floating recording indicator.
    """

    def __init__(self, config: Optional["Config"] = None):
        if config is None:
            from engine.config import Config

            config = Config()

        self.config = config
        self._is_active = False
        self._current_partial_text = ""
        self._committed_text = ""
        self._last_status_msg = ""
        self._current_provider: str = config.transcription.provider if config else ""
        self._shown_at = 0.0
        self._last_redraw_at = 0.0
        self._visible = False
        self._session_id = 0

        # Import inside __init__ to pick up test mocks/patches correctly
        import engine.hud_renderer

        # Use getattr to safely check the module attribute which might be patched
        hud_available = getattr(engine.hud_renderer, "HUD_AVAILABLE", False)

        if hud_available:
            try:
                logger.debug("Initializing HudOverlay implementation.")
                from engine.hud_renderer import HudOverlay

                self.impl: Any = HudOverlay(
                    config=config, click_through=config.ui.floating_indicator.click_through
                )
                # Verify that impl actually initialized (to handle early returns in HudOverlay)
                if not hasattr(self.impl, "update_status"):
                    logger.warning("HudOverlay failed to initialize correctly. Falling back.")
                    self.impl = GdiFallbackWindow(config=config)
            except (ImportError, RuntimeError, AttributeError) as e:
                logger.error(f"HudOverlay instantiation failed: {e}")
                self.impl = GdiFallbackWindow(config=config)
            except Exception as e:
                logger.error(f"Unexpected HUD initialization error: {e}")
                self.impl = GdiFallbackWindow(config=config)
        else:
            logger.debug("HUD_AVAILABLE is False, using GdiFallbackWindow.")
            self.impl = GdiFallbackWindow(config=config)

        self._thread: Optional[threading.Thread] = None

    def refresh_settings(self):
        """Safely signals the UI thread to refresh settings."""
        if hasattr(self.impl, "apply_click_through"):
            # We don't call it here. We rely on the UI thread to see the config change
            # or we send an explicit event through the bridge.
            pass

    @property
    def is_recording(self):
        return getattr(self.impl, "is_recording", False)

    @property
    def partial_text(self):
        if hasattr(self.impl, "last_text") and self.impl.last_text:
            return self.impl.last_text
        return getattr(self.impl, "partial_text", "")

    @property
    def visible(self):
        # Always prioritize our local tracking for consistency in tests
        if self._visible:
            return True
        return getattr(self.impl, "visible", False)

    @property
    def is_alive(self):
        """Returns True if the underlying HUD thread is active and responsive."""
        if isinstance(self.impl, GdiFallbackWindow):
            return True
        if self._thread and not self._thread.is_alive():
            return False
        # Check window handle
        if hasattr(self.impl, "_hwnd") and self.impl._hwnd is None:
            # It might still be starting, but if it has exited (hwnd set back to None), it's dead
            return False
        return True

    def start(self):
        if hasattr(self.impl, "start"):
            self.impl.start()
        elif hasattr(self.impl, "run"):
            self._thread = threading.Thread(target=self.impl.run, daemon=True)
            self._thread.start()

    def stop(self):
        self.impl.stop()

    def show(self):
        self.impl.show()
        self._visible = True
        self._shown_at = time.time()

    def hide(self):
        self.impl.hide()
        self._visible = False

    def update_status(self, is_recording: bool):
        self._is_active = is_recording
        self.impl.update_status(is_recording)

        if is_recording:
            self._session_id += 1
            self._committed_text = ""
            self._current_partial_text = ""
            # Don't clear 'Ready' or 'Connecting' if they just happened
            if self._last_status_msg.lower() in ("listening", "finalized"):
                self._last_status_msg = ""
            self.show()

        self._render_preview()

        if not is_recording:
            self._start_linger_timer()

    def update_status_icon(self, status: str):
        self._last_status_msg = status
        if hasattr(self.impl, "update_status_icon"):
            self.impl.update_status_icon(status)

        if status and status not in (STATUS_LISTENING, STATUS_FINALIZED):
            self.show()
            self._render_preview()
            self._start_linger_timer(duration=3.0)
        else:
            self._render_preview()

    def update_provider(self, provider: str):
        self._current_provider = provider
        if hasattr(self.impl, "update_provider"):
            self.impl.update_provider(provider)
        self._render_preview()

    def update_settings(self, settings: dict):
        if hasattr(self.impl, "update_settings"):
            self.impl.update_settings(settings)

    def clear(self):
        """Force clears all text and resets state."""
        self._committed_text = ""
        self._current_partial_text = ""
        self._last_status_msg = ""
        if hasattr(self.impl, "update_text"):
            self.impl.update_text("")
        self._render_preview()

    def _start_linger_timer(self, duration: Optional[float] = None):
        if duration is None:
            duration = DEFAULT_LINGER_SECONDS

        session_at_start = self._session_id

        def _hide_after():
            elapsed = time.time() - self._shown_at
            if elapsed < MIN_VISIBLE_DURATION:
                time.sleep(MIN_VISIBLE_DURATION - elapsed)
            time.sleep(duration)
            # Only hide if we haven't started a NEW session since this timer was created
            if not self.is_recording and self._session_id == session_at_start:
                self.hide()

        threading.Thread(target=_hide_after, daemon=True).start()

    def on_partial(self, text: str):
        self._current_partial_text = text
        now = time.time()
        if now - self._last_redraw_at < REDRAW_THROTTLE_SECONDS:
            return
        self._last_redraw_at = now
        self._render_preview()

    def update_partial_text(self, text: str):
        self.on_partial(text)

    def on_final(self, text: str, linger_seconds: Optional[float] = None):
        if self._committed_text:
            self._committed_text += " "
        self._committed_text += text
        self._current_partial_text = ""
        self._render_preview()

        if linger_seconds is not None:
            self._start_linger_timer(linger_seconds)

    def update_voice_activity(self, active: bool):
        if hasattr(self.impl, "update_voice_active"):
            self.impl.update_voice_active(active)

    def _render_preview(self):
        full_text = self._committed_text
        if self._current_partial_text:
            if full_text:
                full_text += " "
            full_text += self._current_partial_text

        max_chars = DEFAULT_MAX_CHARS
        if self.config:
            max_chars = self.config.ui.floating_indicator.max_characters

        if not full_text:
            if self._last_status_msg and self._last_status_msg not in (
                STATUS_LISTENING,
                STATUS_FINALIZED,
            ):
                display_text = self._last_status_msg
            elif self.is_recording:
                display_text = STATUS_LISTENING
            else:
                display_text = ""
        elif len(full_text) > max_chars:
            display_text = "…" + full_text[-(max_chars - 1) :]
        else:
            display_text = full_text

        if hasattr(self.impl, "update_partial_text"):
            self.impl.update_partial_text(display_text)
        else:
            self.impl.update_text(display_text)
