import threading
import time

import pytest

from engine.config import Config
from engine.hud_renderer import HUD_AVAILABLE, HudOverlay


@pytest.mark.skipif(not HUD_AVAILABLE, reason="HUD not available in this environment")
def test_hud_is_responsive_real_window():
    """
    Verification that the WM_NULL ping actually works against a live HUD window.
    """
    config = Config()
    hud = HudOverlay(config=config)

    # HUD needs to be running in a thread to pump messages
    hud_thread = threading.Thread(target=hud.run, daemon=True)
    hud_thread.start()

    # Give it a second to create the window
    time.sleep(2.0)

    try:
        assert hud._hwnd is not None, "HUD window was not created"
        assert hud.is_responsive() is True, "HUD should be responsive initially"

        # We can't easily "hang" it without killing the thread,
        # but we can verify that after stopping it, it is NOT responsive.
        hud.stop()
        time.sleep(1.0)

        assert hud.is_responsive() is False, "HUD should not be responsive after stop"
    finally:
        hud.stop()


@pytest.mark.skipif(not HUD_AVAILABLE, reason="HUD not available in this environment")
def test_hud_is_responsive_no_window():
    hud = HudOverlay()
    assert hud.is_responsive() is False, "HUD without window should not be responsive"


if __name__ == "__main__":
    # Manual run
    test_hud_is_responsive_real_window()
    test_hud_is_responsive_no_window()
