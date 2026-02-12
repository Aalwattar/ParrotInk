import ctypes
import threading
from ctypes import wintypes
from typing import Optional

from engine.logging import get_logger

logger = get_logger("IndicatorUI")

# --- Win32 Constants & Types ---
WS_EX_LAYERED = 0x00080000
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_POPUP = 0x80000000
CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001
CW_USEDEFAULT = 0x80000000
WM_DESTROY = 0x0002
WM_NCHITTEST = 0x0084
HTCAPTION = 2
WM_PAINT = 0x000F
WM_ERASEBKGND = 0x0014

# Accent Policies for Blur/Acrylic
ACCENT_DISABLED = 0
ACCENT_ENABLE_BLURBEHIND = 3
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4

class ACCENT_POLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_int),
        ("AnimationId", ctypes.c_int),
    ]

class WINDOWCOMPOSITIONATTRIBUTEDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.POINTER(ACCENT_POLICY)),
        ("SizeOfData", ctypes.c_size_t),
    ]

WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM)

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

# --- Win32 API Functions ---
# We use windll instead of windll.user32 etc to allow for easier mocking in tests if needed
# and to avoid side effects during import
_user32 = None
_kernel32 = None
_gdi32 = None

def _get_win32():
    global _user32, _kernel32, _gdi32
    if _user32 is None:
        _user32 = ctypes.windll.user32
        _kernel32 = ctypes.windll.kernel32
        _gdi32 = ctypes.windll.gdi32
        
        _user32.CreateWindowExW.argtypes = [
            wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID
        ]
        _user32.CreateWindowExW.restype = wintypes.HWND
    return _user32, _kernel32, _gdi32

# --- Helper for Acrylic ---
def set_acrylic_effect(hwnd, color=0x00000000):
    user32, _, _ = _get_win32()
    accent = ACCENT_POLICY()
    accent.AccentState = ACCENT_ENABLE_ACRYLICBLURBEHIND
    accent.GradientColor = color # ABGR
    
    data = WINDOWCOMPOSITIONATTRIBUTEDATA()
    data.Attribute = 19 # WCA_ACCENT_POLICY
    data.Data = ctypes.pointer(accent)
    data.SizeOfData = ctypes.sizeof(accent)
    
    # SetWindowCompositionAttribute is in user32.dll
    user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))

class IndicatorWindow:
    """
    Floating Win32 Indicator Window with Acrylic blur.
    """
    def __init__(self):
        self.is_recording = False
        self.partial_text = ""
        self.visible = False
        self._hwnd = None
        self._thread: Optional[threading.Thread] = None
        self._class_name = u"Voice2TextIndicator"
        self._wnd_proc_ptr = WNDPROC(self._wnd_proc)
        self._initialized = False

    def _setup_class(self):
        if self._initialized:
            return
        
        user32, kernel32, gdi32 = _get_win32()
        hinst = kernel32.GetModuleHandleW(None)
        
        # Register Class
        wcex = WNDCLASSEXW()
        wcex.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wcex.style = CS_HREDRAW | CS_VREDRAW
        wcex.lpfnWndProc = self._wnd_proc_ptr
        wcex.hInstance = hinst
        wcex.hbrBackground = gdi32.GetStockObject(4) # BLACK_BRUSH
        wcex.lpszClassName = self._class_name
        wcex.hCursor = user32.LoadCursorW(None, 32512) # IDC_ARROW
        
        if not user32.RegisterClassExW(ctypes.byref(wcex)):
            # Might already be registered
            pass
        
        self._initialized = True

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        user32, _, _ = _get_win32()
        if msg == WM_NCHITTEST:
            # Allow dragging anywhere
            return HTCAPTION
        elif msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        elif msg == WM_PAINT:
            self._on_paint(hwnd)
            return 0
        elif msg == WM_ERASEBKGND:
            return 1 # We handle painting
        
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _on_paint(self, hwnd):
        user32, _, _ = _get_win32()
        ps = wintypes.PAINTSTRUCT()
        hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))
        
        # Draw text and status
        rect = wintypes.RECT()
        user32.GetClientRect(hwnd, ctypes.byref(rect))
        
        # Simple text draw for now
        display_text = f"{'REC' if self.is_recording else 'IDLE'}: {self.partial_text}"
        user32.SetTextColor(hdc, 0xFFFFFF) # White
        user32.SetBkMode(hdc, 1) # Transparent
        user32.DrawTextW(hdc, display_text, -1, ctypes.byref(rect), 0x0000 | 0x0004 | 0x0020) # CENTER | VC_CENTER | SINGLELINE
        
        user32.EndPaint(hwnd, ctypes.byref(ps))

    def _create_window(self):
        user32, kernel32, _ = _get_win32()
        hinst = kernel32.GetModuleHandleW(None)
        
        ex_style = WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW
        style = WS_POPUP
        
        self._hwnd = user32.CreateWindowExW(
            ex_style, self._class_name, u"V2T Indicator", style,
            500, 50, 300, 40,
            None, None, hinst, None
        )
        
        if not self._hwnd:
            logger.error("Failed to create indicator window.")
            return

        # Set transparency/acrylic
        self._update_visuals()

    def _update_visuals(self):
        if not self._hwnd:
            return
            
        user32, _, _ = _get_win32()
        # 0xAA0000FF = Semi-transparent Red (ABGR)
        # 0xAA222222 = Semi-transparent Dark Grey
        color = 0xAA0000CC if self.is_recording else 0xAA333333
        set_acrylic_effect(self._hwnd, color)
        user32.InvalidateRect(self._hwnd, None, True)

    def _run_loop(self):
        self._setup_class()
        self._create_window()
        
        user32, _, _ = _get_win32()
        if self.visible:
            user32.ShowWindow(self._hwnd, 5) # SW_SHOW
        
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def start(self):
        """Starts the window in a separate thread."""
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def show(self):
        self.visible = True
        if self._hwnd:
            user32, _, _ = _get_win32()
            user32.ShowWindow(self._hwnd, 5) # SW_SHOW
        logger.debug("Indicator window shown.")

    def hide(self):
        self.visible = False
        if self._hwnd:
            user32, _, _ = _get_win32()
            user32.ShowWindow(self._hwnd, 0) # SW_HIDE
        logger.debug("Indicator window hidden.")

    def update_status(self, is_recording: bool):
        self.is_recording = is_recording
        self._update_visuals()
        logger.debug(f"Indicator status updated: recording={is_recording}")

    def update_partial_text(self, text: str):
        words = text.split()
        if len(words) > 5:
            self.partial_text = " ".join(words[-5:])
        else:
            self.partial_text = text
        if self._hwnd:
            user32, _, _ = _get_win32()
            user32.InvalidateRect(self._hwnd, None, True)
        logger.debug(f"Indicator text updated: {self.partial_text}")
