from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import Callable, List, Optional, Set

from engine.logging import get_logger
from engine.platform_win.api import (
    AC_SRC_ALPHA,
    AC_SRC_OVER,
    BLENDFUNCTION,
    ULW_ALPHA,
    WM_CLOSE,
    WM_DESTROY,
    WM_KEYDOWN,
    WM_KEYUP,
    WM_LBUTTONDOWN,
    WM_SYSKEYDOWN,
    WM_SYSKEYUP,
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

logger = get_logger("HotkeyUI")


class HotkeyRecorder:
    """
    A Win32 modal-like window that captures a hotkey combination.
    Uses native message handling to avoid global hooks.
    """

    def __init__(self, on_captured: Callable[[str], None]):
        self.on_captured = on_captured
        self.current_keys: Set[str] = set()
        self.final_hotkey: Optional[str] = None
        self._hwnd = None
        self._width, self._height = 400, 100
        self._class_name = f"V2THotkeyRecorder_{id(self)}"

        from engine.platform_win.api import WNDPROC

        self._wnd_proc_ptr = WNDPROC(self._wnd_proc)

        self._token = ctypes.c_ulonglong()
        gdiplus.GdiplusStartup(
            ctypes.byref(self._token),
            ctypes.byref(GdiplusStartupInput(1, None, False, False)),
            None,
        )

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        elif msg == WM_CLOSE:
            user32.DestroyWindow(hwnd)
            return 0
        elif msg == WM_LBUTTONDOWN:
            # Cancel on click
            self._cancel()
            return 0
        elif msg in (WM_KEYDOWN, WM_SYSKEYDOWN):
            self._handle_key_down(wparam, lparam)
            return 0
        elif msg in (WM_KEYUP, WM_SYSKEYUP):
            self._handle_key_up(wparam)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _cancel(self):
        """Aborts recording without saving anything."""
        self.final_hotkey = None
        user32.PostMessageW(self._hwnd, WM_CLOSE, 0, 0)

    def _handle_key_down(self, vk: int, lparam: int):
        # Escape key (0x1B) cancels recording
        if vk == 0x1B:
            self._cancel()
            return

        scan_code = (lparam >> 16) & 0xFF
        key_name = self._vk_to_text(vk, scan_code)
        if key_name and key_name not in self.current_keys:
            self.current_keys.add(key_name)
            self._draw()

    def _handle_key_up(self, vk: int):
        if self.current_keys:
            keys_list = sorted(list(self.current_keys))
            if self._is_valid(keys_list):
                self.final_hotkey = "+".join(keys_list)
                user32.PostMessageW(self._hwnd, WM_CLOSE, 0, 0)
            else:
                # If invalid (like just holding Ctrl), we allow clearing on release
                # but we usually wait for a full combo.
                scan_code = user32.MapVirtualKeyW(vk, 0)
                key_name = self._vk_to_text(vk, scan_code)
                if key_name and key_name in self.current_keys:
                    self.current_keys.remove(key_name)
                    self._draw()

    def _is_valid(self, keys: List[str]) -> bool:
        """Minimum requirement: one non-modifier key or a function key."""
        modifiers = {"ctrl", "alt", "shift", "cmd"}
        non_mods = [k for k in keys if k not in modifiers]
        # Allow combos like Ctrl+Alt+V or single keys like F12
        return len(non_mods) > 0

    def _vk_to_text(self, vk: int, scan_code: int) -> Optional[str]:
        # Modifiers
        if vk in (0x10, 0xA0, 0xA1):
            return "shift"
        if vk in (0x11, 0xA2, 0xA3):
            return "ctrl"
        if vk in (0x12, 0xA4, 0xA5):
            return "alt"
        if vk in (0x5B, 0x5C):
            return "cmd"

        # F-keys
        if 112 <= vk <= 123:
            return f"f{vk - 111}"

        # GetKeyNameText handles most other keys
        lparam = scan_code << 16
        # Check if extended bit is needed (e.g. for arrow keys, etc.)
        # For simplicity, we just use the name from Windows
        buffer = ctypes.create_unicode_buffer(32)
        if user32.GetKeyNameTextW(lparam, buffer, 32) > 0:
            return buffer.value.lower()
        return None

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

        dib_ref = (ctypes.c_char * 40).from_buffer(bmi)
        hbmp = gdi32.CreateDIBSection(hdc_mem, ctypes.byref(dib_ref), 0, ctypes.c_void_p(), None, 0)
        gdi32.SelectObject(hdc_mem, hbmp)

        graphics = ctypes.c_void_p()
        gdiplus.GdipCreateFromHDC(hdc_mem, ctypes.byref(graphics))
        gdiplus.GdipSetSmoothingMode(graphics, 4)

        # Draw Backdrop (Capsule)
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

        # Draw Text
        font_family = ctypes.c_void_p()
        gdiplus.GdipCreateFontFamilyFromName("Segoe UI", None, ctypes.byref(font_family))
        font = ctypes.c_void_p()
        gdiplus.GdipCreateFont(font_family, 12.0, 1, 3, ctypes.byref(font))
        text_brush = ctypes.c_void_p()
        gdiplus.GdipCreateSolidFill(0xFFFFFFFF, ctypes.byref(text_brush))

        # Primary Text
        display_text = "Press keys for new hotkey..."
        if self.current_keys:
            display_text = " + ".join(sorted(list(self.current_keys))).upper()

        rect = (ctypes.c_float * 4)(20.0, 30.0, float(self._width - 40), 30.0)
        fmt = ctypes.c_void_p()
        gdiplus.GdipCreateStringFormat(0, 0, ctypes.byref(fmt))
        gdiplus.GdipSetStringFormatAlign(fmt, 1)  # Center

        gdiplus.GdipDrawString(
            graphics, display_text, -1, font, ctypes.byref(rect), fmt, text_brush
        )

        # Secondary Text (Hint)
        hint_brush = ctypes.c_void_p()
        gdiplus.GdipCreateSolidFill(0xFF888888, ctypes.byref(hint_brush))
        hint_font = ctypes.c_void_p()
        gdiplus.GdipCreateFont(font_family, 8.0, 0, 3, ctypes.byref(hint_font))
        hint_rect = (ctypes.c_float * 4)(20.0, 60.0, float(self._width - 40), 20.0)

        gdiplus.GdipDrawString(
            graphics,
            "(ESC or Click to cancel)",
            -1,
            hint_font,
            ctypes.byref(hint_rect),
            fmt,
            hint_brush,
        )

        # Update Window
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
        gdiplus.GdipDeleteGraphics(graphics)
        gdiplus.GdipDeletePath(path)
        gdiplus.GdipDeleteBrush(brush)
        gdiplus.GdipDeleteFont(font)
        gdiplus.GdipDeleteFont(hint_font)
        gdiplus.GdipDeleteFontFamily(font_family)
        gdiplus.GdipDeleteBrush(text_brush)
        gdiplus.GdipDeleteBrush(hint_brush)
        gdiplus.GdipDeleteStringFormat(fmt)
        gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(0, hdc_screen)

    def run(self):
        hinst = kernel32.GetModuleHandleW(None)
        hcursor = user32.LoadCursorW(None, 32512)
        wcex = WNDCLASSEXW(
            ctypes.sizeof(WNDCLASSEXW),
            0,
            self._wnd_proc_ptr,
            0,
            0,
            hinst,
            0,
            hcursor,
            0,
            None,
            self._class_name,
            0,
        )
        user32.RegisterClassExW(ctypes.byref(wcex))

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
        user32.ShowWindow(self._hwnd, 5)
        user32.SetForegroundWindow(self._hwnd)
        user32.SetFocus(self._hwnd)
        self._draw()

        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        if self.final_hotkey:
            self.on_captured(self.final_hotkey)

        gdiplus.GdiplusShutdown(self._token)
        user32.UnregisterClassW(self._class_name, hinst)
