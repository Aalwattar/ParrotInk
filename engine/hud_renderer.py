import ctypes
import queue
import threading
from ctypes import wintypes
from typing import Optional

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
        ("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG), ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD),
    ]

class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]

_user32 = ctypes.windll.user32
_gdi32 = ctypes.windll.gdi32

_user32.UpdateLayeredWindow.argtypes = [
    wintypes.HWND, wintypes.HDC, ctypes.POINTER(wintypes.POINT),
    ctypes.POINTER(wintypes.SIZE), wintypes.HDC, ctypes.POINTER(wintypes.POINT),
    wintypes.COLORREF, ctypes.POINTER(BLENDFUNCTION), wintypes.DWORD,
]

class HudOverlay:
    def __init__(self, style_name: str = "glass"):
        if not HUD_AVAILABLE:
            return

        self.text_queue = queue.Queue()
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
            self.style = GlassStyle() # Fallback

        # UI Specs
        self.win_width = 650
        self.win_height = 150

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
            self._hwnd, hdc_screen, None, ctypes.byref(size), self._hdc_mem,
            ctypes.byref(zero_pt), 0, ctypes.byref(blend), ULW_ALPHA
        )
        _user32.ReleaseDC(0, hdc_screen)

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_TIMER:
            changed = False
            while not self.text_queue.empty():
                self.last_text = self.text_queue.get()
                changed = True
            
            if (changed or self.visible) and hasattr(self, "_canvas"):
                self.style.draw(
                    self._canvas, self.win_width, self.win_height, 
                    self.last_text if self.last_text else "Standby", 
                    self.is_recording
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
        try: win32gui.RegisterClass(wcex)
        except: pass

        self._hwnd = win32gui.CreateWindowEx(
            WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW, class_name, 
            "V2T HUD", WS_POPUP, 100, 100, self.win_width, self.win_height, 
            0, 0, hinst, None
        )

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
        self._hbmp = _gdi32.CreateDIBSection(self._hdc_mem, ctypes.byref(bmi), 0, ctypes.byref(self._pixel_ptr), None, 0)
        _gdi32.SelectObject(self._hdc_mem, self._hbmp)
        _user32.ReleaseDC(0, hdc_screen)

        # Skia surface wrapping the DIB section directly
        info = skia.ImageInfo.Make(
            self.win_width, self.win_height,
            skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType
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
        if self._hwnd: win32gui.ShowWindow(self._hwnd, win32con.SW_SHOWNOACTIVATE); self.visible = True

    def hide(self):
        if self._hwnd: win32gui.ShowWindow(self._hwnd, win32con.SW_HIDE); self.visible = False

    def stop(self):
        if self._hwnd: win32gui.PostMessage(self._hwnd, win32con.WM_CLOSE, 0, 0)

    def update_status(self, is_recording: bool): self.is_recording = is_recording

    def update_text(self, text: str):
        if HUD_AVAILABLE: self.text_queue.put(text)

    def update_partial_text(self, text: str):
        words = text.split()
        limit = self._partial_words
        buffer = " ".join(words[-limit:]) if len(words) > limit else text
        self.update_text(buffer)
