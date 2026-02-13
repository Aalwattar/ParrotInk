import ctypes
import queue
import threading
from ctypes import wintypes

from engine.logging import get_logger

logger = get_logger("HudRenderer")

try:
    import skia
    import win32con
    import win32gui
    from win32api import GetModuleHandle

    from .hud_styles import GlassStyle

    HUD_AVAILABLE = True
except ImportError:
    HUD_AVAILABLE = False

# --- Win32 Constants ---
WS_EX_LAYERED = 0x00080000
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_POPUP = 0x80000000
ULW_ALPHA = 0x00000002
AC_SRC_ALPHA = 0x01
AC_SRC_OVER = 0x00
WM_NCHITTEST = 0x0084
HTCAPTION = 2
WM_TIMER = 0x0113


# --- Win32 Structs ---
class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", ctypes.c_byte),
        ("BlendFlags", ctypes.c_byte),
        ("SourceConstantAlpha", ctypes.c_byte),
        ("AlphaFormat", ctypes.c_byte),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


_user32 = ctypes.windll.user32
_gdi32 = ctypes.windll.gdi32

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


class HudOverlay:
    def __init__(self, style_name: str = "glass"):
        if not HUD_AVAILABLE:
            return

        self.text_queue: queue.Queue[str | tuple[str, str]] = queue.Queue()
        self.last_text = ""
        self.is_recording = False
        self.visible = False
        self._hwnd = None
        self._ready_event = threading.Event()
        self._partial_words = 5

        # Select style
        if style_name == "glass":
            self.style = GlassStyle()
        else:
            self.style = GlassStyle()  # Fallback

        # UI Specs
        self.win_width = 1000
        self.win_height = 80

        # GDI Resources
        self._hdc_mem = None
        self._hbmp = None
        self._pixel_ptr = None

    def _update_window(self):
        if not self._hwnd:
            return
        hdc_screen = _user32.GetDC(0)
        size = wintypes.SIZE(self.win_width, self.win_height)
        zero_pt = wintypes.POINT(0, 0)
        blend = BLENDFUNCTION(AC_SRC_OVER, 0, 255, AC_SRC_ALPHA)

        _user32.UpdateLayeredWindow(
            self._hwnd,
            hdc_screen,
            None,
            ctypes.byref(size),
            self._hdc_mem,
            ctypes.byref(zero_pt),
            0,
            ctypes.pointer(blend),
            ULW_ALPHA,
        )
        _user32.ReleaseDC(0, hdc_screen)

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_TIMER:
            changed = False
            status_override = None

            # Process Queue - Drain COMPLETELY to ensure we show the latest state
            # If we limit count < 5, we might lag behind if the provider sends burst updates.
            qsize = self.text_queue.qsize()
            if qsize > 0:
                latest_text = None
                latest_status = None

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
                        else:
                            # Legacy string support
                            latest_text = item
                    except queue.Empty:
                        break

                # Apply only the latest state from the batch
                if latest_text is not None:
                    self.last_text = latest_text
                if latest_status is not None:
                    status_override = latest_status

            if (changed or self.visible) and hasattr(self, "_canvas"):
                self.style.draw(
                    self._canvas,
                    self.win_width,
                    self.win_height,
                    self.last_text if self.last_text else "Listening...",
                    self.is_recording,
                    status_override,
                )
                self._update_window()
            return 0
        if msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
        if msg == WM_NCHITTEST:
            return HTCAPTION
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def run(self):
        if not HUD_AVAILABLE:
            return

        hinst = GetModuleHandle(None)
        class_name = "Voice2TextSkiaHUD"
        wcex = win32gui.WNDCLASS()
        wcex.lpfnWndProc = self._wnd_proc
        wcex.lpszClassName = class_name
        wcex.hInstance = hinst
        wcex.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        try:
            win32gui.RegisterClass(wcex)
        except Exception:
            pass

        # Robust Bottom-Center Position
        screen_w = _user32.GetSystemMetrics(0)
        screen_h = _user32.GetSystemMetrics(1)

        x_pos = (screen_w - self.win_width) // 2
        y_pos = screen_h - self.win_height - 60

        self._hwnd = win32gui.CreateWindowEx(
            win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW,
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
            logger.info(f"HUD Window Created: {self._hwnd} at ({x_pos}, {y_pos})")
        else:
            logger.error(f"Failed to create HUD window: {win32gui.GetLastError()}")

        # Setup GDI DIB Section
        hdc_screen = _user32.GetDC(0)
        self._hdc_mem = _gdi32.CreateCompatibleDC(hdc_screen)
        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = self.win_width
        bmi.bmiHeader.biHeight = -self.win_height
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = 0
        self._pixel_ptr = ctypes.c_void_p()
        self._hbmp = _gdi32.CreateDIBSection(
            self._hdc_mem, ctypes.byref(bmi), 0, ctypes.byref(self._pixel_ptr), None, 0
        )
        _gdi32.SelectObject(self._hdc_mem, self._hbmp)
        _user32.ReleaseDC(0, hdc_screen)

        # Skia surface wrapping the DIB section directly
        info = skia.ImageInfo.Make(
            self.win_width, self.win_height, skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType
        )

        # Create a buffer that points to the DIB section memory
        size_in_bytes = self.win_width * self.win_height * 4
        pixel_data = (ctypes.c_byte * size_in_bytes).from_address(self._pixel_ptr.value)

        self._surface = skia.Surface.MakeRasterDirect(info, pixel_data, self.win_width * 4)
        self._canvas = self._surface.getCanvas()

        _user32.SetTimer(self._hwnd, 1, 50, None)
        self._ready_event.set()
        win32gui.PumpMessages()

    def show(self):
        if self._hwnd:
            win32gui.ShowWindow(self._hwnd, win32con.SW_SHOWNOACTIVATE)
            self.visible = True

    def hide(self):
        if self._hwnd:
            win32gui.ShowWindow(self._hwnd, win32con.SW_HIDE)
            self.visible = False

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

    def update_text(self, text: str):
        if HUD_AVAILABLE:
            self.text_queue.put(("TEXT", text))

    def update_partial_text(self, text: str):
        self.update_text(text)
