import ctypes
import threading
import time
from ctypes import wintypes

from typing import Any

from engine.logging import get_logger

# Import the new HUD
try:
    from .hud_renderer import HUD_AVAILABLE, HudOverlay
except ImportError:
    HUD_AVAILABLE = False
    HudOverlay = Any  # type: ignore

logger = get_logger("IndicatorUI")

# --- Win32 Constants ---
WS_EX_LAYERED = 0x00080000
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_POPUP = 0x80000000
WM_DESTROY = 0x0002
WM_NCHITTEST = 0x0084
HTCAPTION = 2
ULW_ALPHA = 0x00000002
AC_SRC_ALPHA = 0x01
AC_SRC_OVER = 0x00


# --- Win32 Structs ---
class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", ctypes.c_byte),
        ("BlendFlags", ctypes.c_byte),
        ("SourceConstantAlpha", ctypes.c_byte),
        ("AlphaFormat", ctypes.c_byte),
    ]


class GdiplusStartupInput(ctypes.Structure):
    _fields_ = [
        ("GdiplusVersion", ctypes.c_uint32),
        ("DebugEventCallback", ctypes.c_void_p),
        ("SuppressBackgroundThread", ctypes.c_bool),
        ("SuppressExternalCodecs", ctypes.c_bool),
    ]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", ctypes.c_uint),
        ("wParam", ctypes.c_uint64),
        ("lParam", ctypes.c_uint64),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_int64, wintypes.HWND, ctypes.c_uint, ctypes.c_uint64, ctypes.c_uint64
)


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("style", ctypes.c_uint),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HICON),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HICON),
    ]


# --- API Access ---
_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32
_gdi32 = ctypes.windll.gdi32


def _setup_api():
    try:
        _gdiplus = ctypes.windll.gdiplus
        _gdiplus.GdipAddPathArc.argtypes = [
            ctypes.c_void_p,
            ctypes.c_float,
            ctypes.c_float,
            ctypes.c_float,
            ctypes.c_float,
            ctypes.c_float,
            ctypes.c_float,
        ]
        _gdiplus.GdipFillEllipse.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_float,
            ctypes.c_float,
            ctypes.c_float,
            ctypes.c_float,
        ]
        _gdiplus.GdipDrawPath.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        _gdiplus.GdipCreatePen1.argtypes = [
            ctypes.c_uint32,
            ctypes.c_float,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        _gdiplus.GdipCreateFont.argtypes = [
            ctypes.c_void_p,
            ctypes.c_float,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        _gdiplus.GdipDrawString.argtypes = [
            ctypes.c_void_p,
            ctypes.c_wchar_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
        ]
    except Exception:
        pass

    _user32.UpdateLayeredWindow.argtypes = [
        wintypes.HWND,
        wintypes.HDC,
        ctypes.POINTER(wintypes.POINT),
        ctypes.POINTER(wintypes.SIZE),
        wintypes.HDC,
        ctypes.POINTER(wintypes.POINT),
        wintypes.COLORREF,
        ctypes.POINTER(BLENDFUNCTION),
        wintypes.DWORD,
    ]

    _user32.DefWindowProcW.argtypes = [
        wintypes.HWND,
        ctypes.c_uint,
        ctypes.c_uint64,
        ctypes.c_uint64,
    ]
    _user32.DefWindowProcW.restype = ctypes.c_int64


class GdiFallbackWindow:
    """Fallback implementation using GDI+ if Skia is unavailable."""

    def __init__(self, design_style="glass"):
        _setup_api()
        self.is_recording = False
        self.partial_text = ""
        self.visible = False
        self.design_style = design_style
        self._hwnd = None
        self._width, self._height = 340, 42
        self._class_name = "Voice2TextGdiFallback"
        self._wnd_proc_ptr = WNDPROC(self._wnd_proc)

        try:
            self._gdiplus = ctypes.windll.gdiplus
            token = ctypes.c_ulonglong()
            self._gdiplus.GdiplusStartup(
                ctypes.byref(token), ctypes.byref(GdiplusStartupInput(1, None, False, False)), None
            )
        except Exception:
            self._gdiplus = None

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_NCHITTEST:
            return HTCAPTION
        if msg == WM_DESTROY:
            return 0
        return _user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _draw_ui(self):
        if not self._hwnd or not self._gdiplus:
            return
        hdc_screen = _user32.GetDC(0)
        hdc_mem = _gdi32.CreateCompatibleDC(hdc_screen)

        bmi = bytearray(40)
        bmi[0:4] = (40).to_bytes(4, "little")
        bmi[4:8] = (self._width).to_bytes(4, "little")
        bmi[8:12] = (self._height).to_bytes(4, "little")
        bmi[12:14] = (1).to_bytes(2, "little")
        bmi[14:16] = (32).to_bytes(2, "little")

        hbmp = _gdi32.CreateDIBSection(
            hdc_mem,
            ctypes.byref((ctypes.c_char * 40).from_buffer(bmi)),
            0,
            ctypes.c_void_p(),
            None,
            0,
        )
        _gdi32.SelectObject(hdc_mem, hbmp)

        graphics = ctypes.c_void_p()
        self._gdiplus.GdipCreateFromHDC(hdc_mem, ctypes.byref(graphics))
        self._gdiplus.GdipSetSmoothingMode(graphics, 4)
        self._gdiplus.GdipSetTextRenderingHint(graphics, 4)

        w, h = float(self._width), float(self._height)
        bg_color = 0xCC1A1A1A if not self.is_recording else 0xCC330000
        border_color = 0x44FFFFFF
        text_color = 0xCCFFFFFF
        r = h / 2.0 - 2.0

        path = ctypes.c_void_p()
        self._gdiplus.GdipCreatePath(0, ctypes.byref(path))
        self._gdiplus.GdipAddPathArc(path, 1.0, 1.0, r * 2, r * 2, 180.0, 90.0)
        self._gdiplus.GdipAddPathArc(path, w - r * 2 - 2, 1.0, r * 2, r * 2, 270.0, 90.0)
        self._gdiplus.GdipAddPathArc(path, w - r * 2 - 2, h - r * 2 - 2, r * 2, r * 2, 0.0, 90.0)
        self._gdiplus.GdipAddPathArc(path, 1.0, h - r * 2 - 2, r * 2, r * 2, 90.0, 90.0)
        self._gdiplus.GdipClosePathFigure(path)

        brush = ctypes.c_void_p()
        self._gdiplus.GdipCreateSolidFill(bg_color, ctypes.byref(brush))
        self._gdiplus.GdipFillPath(graphics, brush, path)

        pen = ctypes.c_void_p()
        self._gdiplus.GdipCreatePen1(border_color, 1.0, 2, ctypes.byref(pen))
        self._gdiplus.GdipDrawPath(graphics, pen, path)

        led_argb = 0xFFFF0000 if self.is_recording else 0x88AAAAAA
        led_brush = ctypes.c_void_p()
        self._gdiplus.GdipCreateSolidFill(led_argb, ctypes.byref(led_brush))
        self._gdiplus.GdipFillEllipse(graphics, led_brush, 18.0, h / 2.0 - 5.0, 10.0, 10.0)

        font_family = ctypes.c_void_p()
        self._gdiplus.GdipCreateFontFamilyFromName("Segoe UI", None, ctypes.byref(font_family))
        font = ctypes.c_void_p()
        self._gdiplus.GdipCreateFont(font_family, 11.0, 1, 3, ctypes.byref(font))
        text_brush = ctypes.c_void_p()
        self._gdiplus.GdipCreateSolidFill(text_color, ctypes.byref(text_brush))

        lrect = (ctypes.c_float * 4)(42.0, h / 2.0 - 9.0, w - 60.0, 22.0)
        display_text = self.partial_text if self.partial_text else "Standing by..."
        self._gdiplus.GdipDrawString(
            graphics, display_text, -1, font, ctypes.byref(lrect), None, text_brush
        )

        self._gdiplus.GdipDeleteGraphics(graphics)
        blend = BLENDFUNCTION(AC_SRC_OVER, 0, 255, AC_SRC_ALPHA)
        size = wintypes.SIZE(self._width, self._height)
        zero_pt = wintypes.POINT(0, 0)
        _user32.UpdateLayeredWindow(
            self._hwnd,
            hdc_screen,
            None,
            ctypes.byref(size),
            hdc_mem,
            ctypes.byref(zero_pt),
            0,
            ctypes.byref(blend),
            ULW_ALPHA,
        )

        self._gdiplus.GdipDeleteBrush(brush)
        self._gdiplus.GdipDeleteBrush(led_brush)
        self._gdiplus.GdipDeleteBrush(text_brush)
        self._gdiplus.GdipDeletePen(pen)
        self._gdiplus.GdipDeleteFont(font)
        self._gdiplus.GdipDeleteFontFamily(font_family)
        self._gdiplus.GdipDeletePath(path)
        _gdi32.DeleteObject(hbmp)
        _gdi32.DeleteDC(hdc_mem)
        _user32.ReleaseDC(0, hdc_screen)

    def _run_loop(self):
        hinst = _kernel32.GetModuleHandleW(None)
        wcex = WNDCLASSEXW(
            ctypes.sizeof(WNDCLASSEXW),
            0,
            self._wnd_proc_ptr,
            0,
            0,
            hinst,
            0,
            _user32.LoadCursorW(None, 32512),
            0,
            None,
            self._class_name,
            0,
        )
        _user32.RegisterClassExW(ctypes.byref(wcex))
        self._hwnd = _user32.CreateWindowExW(
            WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW,
            self._class_name,
            "V2T Fallback",
            WS_POPUP,
            500,
            50,
            self._width,
            self._height,
            None,
            None,
            hinst,
            None,
        )
        self._draw_ui()
        if self.visible:
            _user32.ShowWindow(self._hwnd, 5)
        msg = MSG()
        while _user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            _user32.TranslateMessage(ctypes.byref(msg))
            _user32.DispatchMessageW(ctypes.byref(msg))

    def start(self):
        threading.Thread(target=self._run_loop, daemon=True).start()

    def show(self):
        self.visible = True
        if self._hwnd:
            _user32.ShowWindow(self._hwnd, 5)

    def hide(self):
        self.visible = False
        if self._hwnd:
            _user32.ShowWindow(self._hwnd, 0)

    def stop(self):
        if self._hwnd:
            _user32.PostMessageW(self._hwnd, 0x0010, 0, 0)  # WM_CLOSE

    def update_status(self, is_recording: bool):
        self.is_recording = is_recording
        self._draw_ui()

    def update_partial_text(self, text: str):
        words = text.split()
        self.partial_text = " ".join(words[-5:]) if len(words) > 5 else text
        self._draw_ui()


class IndicatorWindow:
    """Universal Indicator that uses HudOverlay (Skia) if available, otherwise GdiFallbackWindow."""

    def __init__(self, design_style="glass"):
        if HUD_AVAILABLE:
            logger.info("Using Skia-based HudOverlay for recording indicator.")
            self.impl = HudOverlay()
        else:
            logger.info("Skia not available. Falling back to GDI+ indicator.")
            self.impl = GdiFallbackWindow(design_style=design_style)

    @property
    def is_recording(self):
        return self.impl.is_recording

    @property
    def partial_text(self):
        return self.impl.last_text if hasattr(self.impl, "last_text") else self.impl.partial_text

    @property
    def visible(self):
        return self.impl.visible

    def start(self):
        # HudOverlay manages its own message pump if run() is called,
        # but the current HudOverlay implementation in hud_renderer.py
        # has a blocking run(). Let's make it start in a thread for parity.
        if isinstance(self.impl, HudOverlay):
            threading.Thread(target=self.impl.run, daemon=True).start()
            # Ensure window is created before we continue
            if hasattr(self.impl, "_ready_event"):
                self.impl._ready_event.wait(timeout=2.0)
        else:
            self.impl.start()

    def show(self):
        self.impl.show()

    def hide(self):
        self.impl.hide()

    def stop(self):
        self.impl.stop()

    def update_status(self, is_recording: bool):
        # HudOverlay doesn't have an explicit update_status yet,
        # it just updates text. Let's add it or map it.
        if hasattr(self.impl, "update_status"):
            self.impl.update_status(is_recording)
        else:
            # For HUD, status might be reflected by color or just text
            if not is_recording:
                self.impl.update_text("Standby")

    def update_partial_text(self, text: str):
        if hasattr(self.impl, "update_partial_text"):
            self.impl.update_partial_text(text)
        else:
            self.impl.update_text(text)

    def on_final(self, text: str, linger_seconds: float = 2.0):
        """Show final text and stay visible for linger_seconds."""
        self.update_partial_text(text)
        self.update_status(False)

        def _hide_after():
            time.sleep(linger_seconds)
            # Only hide if we haven't started recording again
            if not getattr(self.impl, "is_recording", False):
                self.hide()

        threading.Thread(target=_hide_after, daemon=True).start()
