import ctypes
import queue
import threading
import time
from ctypes import wintypes
from typing import Any, Optional

from engine.logging import get_logger

from .platform_win.api import (
    AC_SRC_ALPHA,
    AC_SRC_OVER,
    BITMAPINFO,
    BITMAPINFOHEADER,
    BLENDFUNCTION,
    HTCAPTION,
    HTTRANSPARENT,
    ULW_ALPHA,
    WM_NCHITTEST,
    WS_EX_TRANSPARENT,
    gdi32,
    user32,
)

logger = get_logger("HudRenderer")

# Internal Constants (Not exposed to user)
WIN_WIDTH = 1000
WIN_HEIGHT = 52
DEFAULT_Y_OFFSET = 60
DEFAULT_REFRESH_RATE_MS = 50


try:
    import skia
    import win32con
    import win32gui
    from win32api import GetModuleHandle

    from .hud_styles import GlassStyle

    HUD_AVAILABLE = True
except ImportError:
    HUD_AVAILABLE = False


class HudOverlay:
    def __init__(self, config: Optional[Any] = None, style_name: str = "glass", click_through=True):
        if not HUD_AVAILABLE:
            return

        self.config = config
        self._click_through = click_through
        self.text_queue: queue.Queue[str | tuple[str, Any]] = queue.Queue()
        self.last_text = ""
        self.last_status = None
        self.last_provider = config.transcription.provider if config else None
        self.voice_active = False
        self.is_recording = False
        self.visible = False
        self._hwnd = None
        self._ready_event = threading.Event()

        # UI Specs
        self.win_width = WIN_WIDTH
        self.win_height = WIN_HEIGHT

        # GDI Resources
        self._hdc_mem = None
        self._hbmp = None
        self._pixel_ptr = None

        # Select style
        if style_name == "glass":
            self.style = GlassStyle()
        else:
            self.style = GlassStyle()  # Fallback

    def _update_window(self):
        if not self._hwnd:
            return
        hdc_screen = user32.GetDC(0)
        size = wintypes.SIZE(self.win_width, self.win_height)
        zero_pt = wintypes.POINT(0, 0)
        blend = BLENDFUNCTION(AC_SRC_OVER, 0, 255, AC_SRC_ALPHA)

        user32.UpdateLayeredWindow(
            self._hwnd,
            hdc_screen,
            None,
            ctypes.byref(size),
            self._hdc_mem,
            ctypes.byref(zero_pt),
            0,
            ctypes.byref(blend),
            ULW_ALPHA,
        )
        user32.ReleaseDC(0, hdc_screen)

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_TIMER:
            changed = False

            # Process Queue - Drain COMPLETELY
            qsize = self.text_queue.qsize()
            if qsize > 0:
                latest_text = None
                latest_status = None
                latest_voice = None
                latest_provider = None
                latest_settings = None

                while True:
                    try:
                        item = self.text_queue.get_nowait()
                        changed = True
                        if isinstance(item, tuple):
                            kind, payload = item
                            if kind == "TEXT":
                                latest_text = payload
                            elif kind == "STATUS":
                                latest_status = payload
                            elif kind == "VOICE":
                                latest_voice = payload
                            elif kind == "PROVIDER":
                                latest_provider = payload
                            elif kind == "SETTINGS":
                                latest_settings = payload
                        else:
                            latest_text = item
                    except queue.Empty:
                        break

                if latest_text is not None:
                    self.last_text = latest_text
                if latest_status is not None:
                    self.last_status = latest_status
                if latest_voice is not None:
                    self.voice_active = latest_voice
                if latest_provider is not None:
                    self.last_provider = latest_provider
                if latest_settings is not None:
                    if "click_through" in latest_settings:
                        self.apply_click_through(latest_settings["click_through"])

            if changed and hasattr(self, "_canvas"):
                self.style.draw(
                    self._canvas,
                    self.win_width,
                    self.win_height,
                    self.last_text if self.last_text is not None else "",
                    self.is_recording,
                    getattr(self, "last_status", None),
                    getattr(self, "voice_active", False),
                    getattr(self, "last_provider", None),
                )
                self._update_window()
            return 0
        if msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
        if msg == WM_NCHITTEST:
            return HTTRANSPARENT if self._click_through else HTCAPTION
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def run(self):
        """
        Main window thread logic. Includes retry logic for startup robustness.
        """
        if not HUD_AVAILABLE:
            logger.error("HUD not available (import failure)")
            return

        try:
            hinst = GetModuleHandle(None)
            class_name = "ParrotInkSkiaHUD"
            wcex = win32gui.WNDCLASS()
            wcex.lpfnWndProc = self._wnd_proc
            wcex.lpszClassName = class_name
            wcex.hInstance = hinst
            wcex.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
            try:
                win32gui.RegisterClass(wcex)
            except Exception as e:
                # Registration might fail if already registered, which is fine
                logger.debug(f"HUD Window class registration skipped: {e}")

            # Robust Bottom-Center Position
            screen_w = user32.GetSystemMetrics(0)
            screen_h = user32.GetSystemMetrics(1)

            if screen_w == 0 or screen_h == 0:
                logger.error("Screen metrics returned 0. Display might not be ready.")

            y_offset = DEFAULT_Y_OFFSET
            refresh_rate = DEFAULT_REFRESH_RATE_MS
            if self.config:
                y_offset = getattr(self.config.ui.floating_indicator, "y_offset", DEFAULT_Y_OFFSET)
                refresh_rate = getattr(
                    self.config.ui.floating_indicator, "refresh_rate_ms", DEFAULT_REFRESH_RATE_MS
                )

            x_pos = (screen_w - self.win_width) // 2
            y_pos = screen_h - self.win_height - y_offset

            # Extended styles
            ex_style = win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW
            if self._click_through:
                ex_style |= WS_EX_TRANSPARENT

            # Senior Architecture: Startup Robustness Retry Loop
            # Windows may not be "ready" to create a topmost layered window
            # immediately after a system restart or crash recovery.
            max_retries = 5
            retry_delay = 1.0

            for attempt in range(max_retries):
                self._hwnd = win32gui.CreateWindowEx(
                    ex_style,
                    class_name,
                    "V2T HUD",
                    win32con.WS_POPUP,
                    x_pos,
                    y_pos,
                    self.win_width,
                    self.win_height,
                    0,
                    0,
                    hinst,
                    None,
                )
                if self._hwnd:
                    logger.info(
                        f"HUD Window Created: {self._hwnd} at ({x_pos}, {y_pos}) "
                        f"(Attempt {attempt + 1})"
                    )
                    break

                error_code = win32gui.GetLastError()
                logger.warning(
                    f"HUD window creation failed (Attempt {attempt + 1}/{max_retries}): "
                    f"{error_code}"
                )
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

            if not self._hwnd:
                logger.error(f"Failed to create HUD window after {max_retries} attempts.")
                return

            # Setup GDI DIB Section
            hdc_screen = user32.GetDC(0)
            self._hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
            bmi = BITMAPINFO()
            bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmi.bmiHeader.biWidth = self.win_width
            bmi.bmiHeader.biHeight = -self.win_height
            bmi.bmiHeader.biPlanes = 1
            bmi.bmiHeader.biBitCount = 32
            bmi.bmiHeader.biCompression = 0
            self._pixel_ptr = ctypes.c_void_p()
            self._hbmp = gdi32.CreateDIBSection(
                self._hdc_mem, ctypes.byref(bmi), 0, ctypes.byref(self._pixel_ptr), None, 0
            )
            if not self._hbmp:
                logger.error(f"Failed to create DIB section: {win32gui.GetLastError()}")
                user32.ReleaseDC(0, hdc_screen)
                return

            gdi32.SelectObject(self._hdc_mem, self._hbmp)
            user32.ReleaseDC(0, hdc_screen)

            # Skia surface wrapping the DIB section directly
            info = skia.ImageInfo.Make(
                self.win_width, self.win_height, skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType
            )

            # Create a buffer that points to the DIB section memory
            size_in_bytes = self.win_width * self.win_height * 4
            pixel_data = (ctypes.c_byte * size_in_bytes).from_address(self._pixel_ptr.value)

            self._surface = skia.Surface.MakeRasterDirect(info, pixel_data, self.win_width * 4)
            if not self._surface:
                logger.error("Failed to create Skia surface.")
                return

            self._canvas = self._surface.getCanvas()

            user32.SetTimer(self._hwnd, 1, refresh_rate, None)
            self._ready_event.set()

            win32gui.PumpMessages()
        except Exception as e:
            logger.error(f"HUD Run loop failed with exception: {e}", exc_info=True)
        finally:
            self._hwnd = None
            self._ready_event.clear()
            logger.info("HUD Run loop exited.")

    def show(self):
        if self._hwnd:
            win32gui.ShowWindow(self._hwnd, win32con.SW_SHOWNOACTIVATE)
            self.visible = True
            # Force redraw
            self.text_queue.put(("VISIBILITY", True))

    def hide(self):
        if self._hwnd:
            win32gui.ShowWindow(self._hwnd, win32con.SW_HIDE)
            self.visible = False
            # Force redraw
            self.text_queue.put(("VISIBILITY", False))

    def stop(self):
        if self._hwnd:
            win32gui.PostMessage(self._hwnd, win32con.WM_CLOSE, 0, 0)

    def update_status(self, is_recording: bool):
        self.is_recording = is_recording
        if is_recording:
            # Reset state for new session to prevent flicker of old text
            self.last_text = ""
            self.text_queue.put(("TEXT", ""))
            self.text_queue.put(("STATUS", "listening"))

    def update_status_icon(self, status: str):
        """Supported status: 'finalized', 'listening', 'connecting'"""
        if HUD_AVAILABLE:
            self.text_queue.put(("STATUS", status))

    def update_provider(self, provider: str):
        if HUD_AVAILABLE:
            self.text_queue.put(("PROVIDER", provider))

    def update_settings(self, settings: dict):
        if HUD_AVAILABLE:
            self.text_queue.put(("SETTINGS", settings))

    def update_text(self, text: str):
        if HUD_AVAILABLE:
            self.text_queue.put(("TEXT", text))

    def update_voice_active(self, active: bool):
        if HUD_AVAILABLE:
            self.text_queue.put(("VOICE", active))

    def update_partial_text(self, text: str):
        self.update_text(text)

    def apply_click_through(self, enabled: bool):
        """Dynamically toggles click-through style."""
        self._click_through = enabled
        if not self._hwnd:
            return
        style = win32gui.GetWindowLong(self._hwnd, win32con.GWL_EXSTYLE)
        if enabled:
            style |= win32con.WS_EX_TRANSPARENT
        else:
            style &= ~win32con.WS_EX_TRANSPARENT
        win32gui.SetWindowLong(self._hwnd, win32con.GWL_EXSTYLE, style)
