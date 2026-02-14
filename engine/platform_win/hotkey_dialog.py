import ctypes
from ctypes import wintypes
from typing import Callable, Optional, Set

from pynput import keyboard

from engine.logging import get_logger

from .api import (
    AC_SRC_ALPHA,
    AC_SRC_OVER,
    BLENDFUNCTION,
    ULW_ALPHA,
    WM_DESTROY,
    WNDCLASSEXW,
    WS_EX_LAYERED,
    WS_EX_TOOLWINDOW,
    WS_EX_TOPMOST,
    WS_POPUP,
    GdiplusStartupInput,
    gdi32,
    gdiplus,
    kernel32,
    user32,
)

logger = get_logger("HotkeyDialog")


class HotkeyRecordingWindow:
    """
    A HUD-styled modal window that captures a hotkey combination.
    """

    def __init__(
        self, on_captured: Callable[[str], None], is_valid_cb: Callable[[list[str]], bool]
    ):
        self.on_captured = on_captured
        self.is_valid_cb = is_valid_cb
        self.current_keys: Set[str] = set()
        self.final_hotkey: Optional[str] = None
        self._hwnd = None
        self._width, self._height = 400, 100
        self._class_name = "Voice2TextHotkeyRecorder"
        # We must keep a reference to the WNDPROC to prevent it from being garbage collected
        from .api import WNDPROC

        self._wnd_proc_ptr = WNDPROC(self._wnd_proc)

        # GDI+ Token
        self._token = ctypes.c_ulonglong()
        gdiplus.GdiplusStartup(
            ctypes.byref(self._token),
            ctypes.byref(GdiplusStartupInput(1, None, False, False)),
            None,
        )

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_DESTROY:
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _draw(self):
        if not self._hwnd:
            return
        hdc_screen = user32.GetDC(0)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)

        bmi = bytearray(40)
        bmi[0:4] = (40).to_bytes(4, "little")
        bmi[4:8] = (self._width).to_bytes(4, "little")
        bmi[8:12] = (self._height).to_bytes(4, "little")
        bmi[12:14] = (1).to_bytes(2, "little")
        bmi[14:16] = (32).to_bytes(2, "little")

        hbmp = gdi32.CreateDIBSection(
            hdc_mem,
            ctypes.byref((ctypes.c_char * 40).from_buffer(bmi)),
            0,
            ctypes.c_void_p(),
            None,
            0,
        )
        gdi32.SelectObject(hdc_mem, hbmp)

        graphics = ctypes.c_void_p()
        gdiplus.GdipCreateFromHDC(hdc_mem, ctypes.byref(graphics))
        gdiplus.GdipSetSmoothingMode(graphics, 4)

        # Background (Glassy Dark)
        path = ctypes.c_void_p()
        gdiplus.GdipCreatePath(0, ctypes.byref(path))
        r = 15.0
        gdiplus.GdipAddPathArc(path, 10.0, 10.0, r * 2, r * 2, 180.0, 90.0)
        gdiplus.GdipAddPathArc(
            path, float(self._width - 10 - r * 2), 10.0, r * 2, r * 2, 270.0, 90.0
        )
        gdiplus.GdipAddPathArc(
            path,
            float(self._width - 10 - r * 2),
            float(self._height - 10 - r * 2),
            r * 2,
            r * 2,
            0.0,
            90.0,
        )
        gdiplus.GdipAddPathArc(
            path, 10.0, float(self._height - 10 - r * 2), r * 2, r * 2, 90.0, 90.0
        )
        gdiplus.GdipClosePathFigure(path)

        brush = ctypes.c_void_p()
        gdiplus.GdipCreateSolidFill(0xE01A1A1A, ctypes.byref(brush))
        gdiplus.GdipFillPath(graphics, brush, path)

        # Border
        pen = ctypes.c_void_p()
        gdiplus.GdipCreatePen1(0xFF444444, 1.5, 2, ctypes.byref(pen))
        gdiplus.GdipDrawPath(graphics, pen, path)

        # Text
        font_family = ctypes.c_void_p()
        gdiplus.GdipCreateFontFamilyFromName("Segoe UI", None, ctypes.byref(font_family))

        font = ctypes.c_void_p()
        gdiplus.GdipCreateFont(font_family, 12.0, 1, 3, ctypes.byref(font))

        text_brush = ctypes.c_void_p()
        gdiplus.GdipCreateSolidFill(0xFFFFFFFF, ctypes.byref(text_brush))

        display_text = "Press and hold keys..."
        if self.current_keys:
            display_text = " + ".join(sorted(list(self.current_keys))).upper()

        rect = (ctypes.c_float * 4)(20.0, 30.0, float(self._width - 40), 40.0)

        # Use center alignment
        str_format = ctypes.c_void_p()
        gdiplus.GdipCreateStringFormat(0, 0, ctypes.byref(str_format))
        gdiplus.GdipSetStringFormatAlign(str_format, 1)  # Center

        gdiplus.GdipDrawString(
            graphics, display_text, -1, font, ctypes.byref(rect), str_format, text_brush
        )

        # Update
        blend = BLENDFUNCTION(AC_SRC_OVER, 0, 255, AC_SRC_ALPHA)
        size = wintypes.SIZE(self._width, self._height)
        zero_pt = wintypes.POINT(0, 0)
        user32.UpdateLayeredWindow(
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

        # Cleanup
        gdiplus.GdipDeleteBrush(brush)
        gdiplus.GdipDeleteBrush(text_brush)
        gdiplus.GdipDeleteFont(font)
        gdiplus.GdipDeleteFontFamily(font_family)
        gdiplus.GdipDeletePen(pen)
        gdiplus.GdipDeletePath(path)
        gdiplus.GdipDeleteStringFormat(str_format)
        gdiplus.GdipDeleteGraphics(graphics)
        gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(0, hdc_screen)

    def _normalize_key(self, key: keyboard.Key | keyboard.KeyCode) -> Optional[str]:
        if isinstance(key, keyboard.Key):
            mapping = {
                "ctrl_l": "ctrl",
                "ctrl_r": "ctrl",
                "alt_l": "alt",
                "alt_r": "alt",
                "shift_l": "shift",
                "shift_r": "shift",
                "cmd_l": "cmd",
                "cmd_r": "cmd",
            }
            return mapping.get(key.name, key.name)
        elif hasattr(key, "char") and key.char:
            return key.char.lower()
        return None

    def _on_press(self, key):
        k = self._normalize_key(key)
        if k and k not in self.current_keys:
            self.current_keys.add(k)
            self._draw()

    def _on_release(self, key):
        if self.current_keys:
            keys_list = sorted(list(self.current_keys))
            if self.is_valid_cb(keys_list):
                self.final_hotkey = "+".join(keys_list)
                self.on_captured(self.final_hotkey)
                user32.PostMessageW(self._hwnd, 0x0010, 0, 0)  # Close
            else:
                # If invalid (e.g. only modifiers), clear and wait
                self.current_keys.clear()
                self._draw()

    def show(self):
        hinst = kernel32.GetModuleHandleW(None)
        wcex = WNDCLASSEXW(
            ctypes.sizeof(WNDCLASSEXW),
            0,
            self._wnd_proc_ptr,
            0,
            0,
            hinst,
            0,
            user32.LoadCursorW(None, 32512),
            0,
            None,
            self._class_name,
            0,
        )
        user32.RegisterClassExW(ctypes.byref(wcex))

        # Center on screen
        sw = user32.GetSystemMetrics(0)
        sh = user32.GetSystemMetrics(1)
        x = (sw - self._width) // 2
        y = (sh - self._height) // 2

        self._hwnd = user32.CreateWindowExW(
            WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW,
            self._class_name,
            "Record Hotkey",
            WS_POPUP,
            x,
            y,
            self._width,
            self._height,
            None,
            None,
            hinst,
            None,
        )

        self._draw()
        user32.ShowWindow(self._hwnd, 5)

        # Start keyboard listener
        with keyboard.Listener(on_press=self._on_press, on_release=self._on_release) as listener:
            # Message loop
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            listener.stop()

        gdiplus.GdiplusShutdown(self._token)
