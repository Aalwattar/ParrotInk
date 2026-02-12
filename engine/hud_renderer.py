import ctypes
import queue
import threading
import time

from engine.logging import get_logger

logger = get_logger("HudRenderer")

# --- Robust Import Handling ---
HUD_AVAILABLE = False
try:
    from ctypes import wintypes

    import skia
    import win32api
    import win32con
    import win32gui

    HUD_AVAILABLE = True
except ImportError:
    pass


# --- Win32 Structs & Ctypes Setup ---
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
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
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

_gdi32.CreateDIBSection.argtypes = [
    wintypes.HDC,
    ctypes.POINTER(BITMAPINFO),
    wintypes.UINT,
    ctypes.POINTER(ctypes.c_void_p),
    wintypes.HANDLE,
    wintypes.DWORD,
]


# --- Main HUD Class ---
class HudOverlay:
    def __init__(self):
        if not HUD_AVAILABLE:
            return

        self.text_queue = queue.Queue()
        self.last_text = ""
        self.is_recording = False
        self.visible = False
        self._hwnd = None
        self._ready_event = threading.Event()

        # UI Specs
        self.HEIGHT = 48
        self.MAX_WIDTH = 600
        self.MIN_WIDTH = 140
        self.RADIUS = 24

        # Design Palette
        self.BG_COLOR = 0xEB1E1E1E
        self.BORDER_COLOR = 0x44FFFFFF
        self.TEXT_COLOR = 0xFFFFFFFF
        self.ACCENT_IDLE = 0xFF00BCD4  # Cyan
        self.ACCENT_REC = 0xFFFF0000  # Red
        self.SHADOW_COLOR = 0x80000000

    def _register_window_class(self):
        self.class_name = "StealthHUD_v1"
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self._wnd_proc
        wc.lpszClassName = self.class_name
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hInstance = win32api.GetModuleHandle(None)
        try:
            win32gui.RegisterClass(wc)
        except Exception:
            pass

    def _create_window(self):
        hinst = win32api.GetModuleHandle(None)
        screen_w = win32api.GetSystemMetrics(0)
        self._hwnd = win32gui.CreateWindowEx(
            win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW,
            self.class_name,
            "Voice2Text HUD",
            win32con.WS_POPUP,
            (screen_w - 300) // 2,
            50,
            300,
            100,
            None,
            None,
            hinst,
            None,
        )
        _user32.SetTimer(self._hwnd, 1, 50, None)
        self._update_content("Standby")
        self._ready_event.set()

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_TIMER:
            self._check_queue()
            return 0
        elif msg == win32con.WM_NCHITTEST:
            return win32con.HTCAPTION
        elif msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _check_queue(self):
        text = None
        try:
            while True:
                text = self.text_queue.get_nowait()
        except queue.Empty:
            pass

        if text is not None and text != self.last_text:
            self.last_text = text
            self._update_content(text)

    def update_text(self, text: str):
        if HUD_AVAILABLE:
            self.last_text = text  # For sync visibility in tests
            self.text_queue.put(text)

    def update_status(self, is_recording: bool):
        self.is_recording = is_recording
        if self._hwnd:
            self._update_content(self.last_text or ("Listening..." if is_recording else "Standby"))

    def update_partial_text(self, text: str):
        words = text.split()
        buffer = " ".join(words[-5:]) if len(words) > 5 else text
        self.update_text(buffer)

    def show(self):
        self.visible = True
        if self._hwnd:
            # Must be called from the same thread if we want immediate result,
            # but win32gui.ShowWindow is generally thread-safe for simple show/hide.
            win32gui.ShowWindow(self._hwnd, win32con.SW_SHOWNOACTIVATE)

    def hide(self):
        self.visible = False
        if self._hwnd:
            win32gui.ShowWindow(self._hwnd, win32con.SW_HIDE)

    def stop(self):
        if self._hwnd:
            win32gui.PostMessage(self._hwnd, win32con.WM_CLOSE, 0, 0)

    def _update_content(self, text: str):
        if not HUD_AVAILABLE or not self._hwnd:
            return
        font = skia.Font(skia.Typeface("Segoe UI"), 16)
        text_width = font.measureText(text)

        win_width = max(self.MIN_WIDTH, min(int(text_width + 80), self.MAX_WIDTH))
        win_height = self.HEIGHT + 24

        info = skia.ImageInfo.Make(
            win_width, win_height, skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType
        )
        surface = skia.Surface.MakeRaster(info)

        with surface as canvas:
            canvas.clear(skia.ColorTRANSPARENT)
            rect = skia.Rect.MakeXYWH(8, 8, win_width - 16, self.HEIGHT)

            # Shadow
            canvas.drawRoundRect(
                rect,
                self.RADIUS,
                self.RADIUS,
                skia.Paint(
                    Color=self.SHADOW_COLOR,
                    ImageFilter=skia.ImageFilters.Blur(6.0, 6.0),
                    AntiAlias=True,
                ),
            )

            # Capsule
            canvas.drawRoundRect(
                rect, self.RADIUS, self.RADIUS, skia.Paint(Color=self.BG_COLOR, AntiAlias=True)
            )

            # Border
            canvas.drawRoundRect(
                rect,
                self.RADIUS,
                self.RADIUS,
                skia.Paint(
                    Color=self.BORDER_COLOR,
                    Style=skia.Paint.kStroke_Style,
                    StrokeWidth=1.2,
                    AntiAlias=True,
                ),
            )

            # Accent (Cyan if idle, Red if recording)
            accent_color = self.ACCENT_REC if self.is_recording else self.ACCENT_IDLE
            canvas.drawCircle(
                rect.left() + 20, rect.centerY(), 4, skia.Paint(Color=accent_color, AntiAlias=True)
            )

            # Text
            metrics = font.getMetrics()
            canvas.drawString(
                text,
                rect.left() + 38,
                rect.centerY() - (metrics.fAscent + metrics.fDescent) / 2,
                font,
                skia.Paint(Color=self.TEXT_COLOR, AntiAlias=True),
            )

        self._blit(surface, win_width, win_height)

    def _blit(self, surface, w, h):
        if not self._hwnd:
            return
        pixels = surface.makeImageSnapshot().tobytes()
        hdc_screen = _user32.GetDC(0)
        hdc_mem = _gdi32.CreateCompatibleDC(hdc_screen)
        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = w
        bmi.bmiHeader.biHeight = -h
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = 0
        bits_ptr = ctypes.c_void_p()
        hbitmap = _gdi32.CreateDIBSection(
            hdc_mem, ctypes.byref(bmi), 0, ctypes.byref(bits_ptr), None, 0
        )
        ctypes.memmove(bits_ptr, pixels, len(pixels))
        old_bmp = _gdi32.SelectObject(hdc_mem, hbitmap)
        rect = win32gui.GetWindowRect(self._hwnd)
        pos = wintypes.POINT(rect[0], rect[1])
        size = wintypes.SIZE(w, h)
        src_pos = wintypes.POINT(0, 0)
        blend = BLENDFUNCTION(0x00, 0, 255, 0x01)
        _user32.UpdateLayeredWindow(
            self._hwnd,
            hdc_screen,
            ctypes.byref(pos),
            ctypes.byref(size),
            hdc_mem,
            ctypes.byref(src_pos),
            0,
            ctypes.byref(blend),
            2,
        )
        _gdi32.SelectObject(hdc_mem, old_bmp)
        _gdi32.DeleteObject(hbitmap)
        _gdi32.DeleteDC(hdc_mem)
        _user32.ReleaseDC(0, hdc_screen)

    def run(self):
        """Starts the Win32 message pump and ensures window creation in this thread."""
        self._register_window_class()
        self._create_window()
        win32gui.PumpMessages()


def _delayed_stop(hud):
    time.sleep(4)
    hud.hide()
    hud.stop()


if __name__ == "__main__":
    if HUD_AVAILABLE:
        overlay = HudOverlay()
        threading.Thread(target=_delayed_stop, args=(overlay,), daemon=True).start()
        # Initial state simulation
        overlay.is_recording = True
        overlay.last_text = "This is a live test of the Stealth HUD renderer."
        overlay.visible = True
        
        # Start pump (will create window and show it if visible=True)
        # Note: In production we use show() later, but for test:
        def _force_show(hud):
            hud._ready_event.wait()
            hud.show()
        threading.Thread(target=_force_show, args=(overlay,), daemon=True).start()
        
        overlay.run()
