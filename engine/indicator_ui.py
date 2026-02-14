import ctypes
import threading
import time
from ctypes import wintypes
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .config import Config

from engine.logging import get_logger

from .platform_win.api import (
    AC_SRC_ALPHA,
    AC_SRC_OVER,
    BLENDFUNCTION,
    HTCAPTION,
    HTTRANSPARENT,
    ULW_ALPHA,
    WM_DESTROY,
    WM_NCHITTEST,
    WNDCLASSEXW,
    WS_EX_LAYERED,
    WS_EX_TOOLWINDOW,
    WS_EX_TOPMOST,
    WS_EX_TRANSPARENT,
    WS_POPUP,
    GdiplusStartupInput,
    gdi32,
    gdiplus,
    kernel32,
    user32,
)

# Import the new HUD
try:
    from .hud_renderer import HUD_AVAILABLE, HudOverlay
except ImportError:
    HUD_AVAILABLE = False
    HudOverlay = Any  # type: ignore

logger = get_logger("IndicatorUI")


class GdiFallbackWindow:
    """Fallback implementation using GDI+ if Skia is unavailable."""

    def __init__(self, design_style="glass", click_through=True):
        self.is_recording = False
        self.partial_text = ""
        self.visible = False
        self.design_style = design_style
        self._click_through = click_through
        self._hwnd = None
        self._width, self._height = 340, 60
        self._class_name = "Voice2TextGdiFallback"
        from .platform_win.api import WNDPROC

        self._wnd_proc_ptr = WNDPROC(self._wnd_proc)
        self._status_override = None

        try:
            token = ctypes.c_ulonglong()
            gdiplus.GdiplusStartup(
                ctypes.byref(token), ctypes.byref(GdiplusStartupInput(1, None, False, False)), None
            )
        except Exception:
            pass

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_NCHITTEST:
            return HTTRANSPARENT if self._click_through else HTCAPTION
        if msg == WM_DESTROY:
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def apply_click_through(self, enabled: bool):
        """Dynamically toggles click-through style."""
        self._click_through = enabled
        if not self._hwnd:
            return
        style = user32.GetWindowLongW(self._hwnd, -20)  # GWL_EXSTYLE
        if enabled:
            style |= WS_EX_TRANSPARENT
        else:
            style &= ~WS_EX_TRANSPARENT
        user32.SetWindowLongW(self._hwnd, -20, style)

    def _draw_ui(self):
        if not self._hwnd:
            return
        hdc_screen = user32.GetDC(0)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)

        # New Geometry
        capsule_h = 28.0
        r = 14.0  # radius

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
        gdiplus.GdipSetTextRenderingHint(graphics, 4)

        w, h = float(self._width), float(self._height)

        # Calculate width based on text length
        status_label = (
            (self._status_override or "LISTENING").upper() if self.is_recording else "STANDBY"
        )
        display_text = self.partial_text if self.partial_text else "..."

        # Single-Line Layout Math
        h_padding = 15.0
        content_width = (len(status_label) * 7.0) + (len(display_text) * 8.0) + 30.0
        capsule_w = min(max(120.0, content_width + (h_padding * 2)), self._width - 20)

        x_start = (w - capsule_w) / 2.0
        y_start = (h - capsule_h) / 2.0

        bg_color = 0xD01A1A1A if not self.is_recording else 0xD0222222

        path = ctypes.c_void_p()
        gdiplus.GdipCreatePath(0, ctypes.byref(path))
        gdiplus.GdipAddPathArc(path, x_start, y_start, r * 2, r * 2, 180.0, 90.0)
        gdiplus.GdipAddPathArc(
            path, x_start + capsule_w - r * 2, y_start, r * 2, r * 2, 270.0, 90.0
        )
        gdiplus.GdipAddPathArc(
            path, x_start + capsule_w - r * 2, y_start + capsule_h - r * 2, r * 2, r * 2, 0.0, 90.0
        )
        gdiplus.GdipAddPathArc(path, x_start, y_start + capsule_h - r * 2, r * 2, r * 2, 90.0, 90.0)
        gdiplus.GdipClosePathFigure(path)

        brush = ctypes.c_void_p()
        gdiplus.GdipCreateSolidFill(bg_color, ctypes.byref(brush))
        gdiplus.GdipFillPath(graphics, brush, path)

        # Status Dot
        if self.is_recording:
            dot_color = 0xFF00FFFF if not getattr(self, "_voice_active", False) else 0xFF88FFFF
        else:
            dot_color = 0x88AAAAAA

        if status_label == "FINALIZED":
            dot_color = 0xFF28C850

        led_brush = ctypes.c_void_p()
        gdiplus.GdipCreateSolidFill(dot_color, ctypes.byref(led_brush))
        gdiplus.GdipFillEllipse(
            graphics, led_brush, x_start + h_padding, y_start + (capsule_h / 2.0) - 3.0, 6.0, 6.0
        )

        # Fonts
        font_family = ctypes.c_void_p()
        gdiplus.GdipCreateFontFamilyFromName("Segoe UI", None, ctypes.byref(font_family))

        # Single Line Baseline
        font_status = ctypes.c_void_p()
        gdiplus.GdipCreateFont(font_family, 8.0, 1, 3, ctypes.byref(font_status))
        status_brush = ctypes.c_void_p()
        gdiplus.GdipCreateSolidFill(0xBBFFFFFF, ctypes.byref(status_brush))

        s_x = x_start + h_padding + 10.0
        srect = (ctypes.c_float * 4)(s_x, y_start + 7.0, len(status_label) * 8.0, 15.0)
        gdiplus.GdipDrawString(
            graphics, status_label, -1, font_status, ctypes.byref(srect), None, status_brush
        )

        # Text
        font_text = ctypes.c_void_p()
        gdiplus.GdipCreateFont(font_family, 10.0, 0, 3, ctypes.byref(font_text))
        text_brush = ctypes.c_void_p()
        gdiplus.GdipCreateSolidFill(0xFFFFFFFF, ctypes.byref(text_brush))

        t_x = s_x + (len(status_label) * 7.5) + 8.0
        trect = (ctypes.c_float * 4)(
            t_x, y_start + 6.0, capsule_w - (t_x - x_start) - h_padding, 20.0
        )
        gdiplus.GdipDrawString(
            graphics, display_text, -1, font_text, ctypes.byref(trect), None, text_brush
        )

        gdiplus.GdipDeleteGraphics(graphics)
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

        gdiplus.GdipDeleteBrush(brush)
        gdiplus.GdipDeleteBrush(led_brush)
        gdiplus.GdipDeleteBrush(text_brush)
        gdiplus.GdipDeleteFont(font_status)
        gdiplus.GdipDeleteFont(font_text)
        gdiplus.GdipDeleteFontFamily(font_family)
        gdiplus.GdipDeletePath(path)
        gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(0, hdc_screen)

    def _run_loop(self):
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

        # Calculate Position
        rect = wintypes.RECT()
        user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
        work_w = rect.right - rect.left
        work_bottom = rect.bottom

        x_pos = (work_w - self._width) // 2
        y_pos = work_bottom - 10 - self._height

        ex_style = WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW
        if self._click_through:
            ex_style |= WS_EX_TRANSPARENT

        self._hwnd = user32.CreateWindowExW(
            ex_style,
            self._class_name,
            "V2T Fallback",
            WS_POPUP,
            x_pos,
            y_pos,
            self._width,
            self._height,
            None,
            None,
            hinst,
            None,
        )
        self._draw_ui()
        if self.visible:
            user32.ShowWindow(self._hwnd, 5)

        class MSG(ctypes.Structure):
            _fields_ = [
                ("hwnd", wintypes.HWND),
                ("message", ctypes.c_uint),
                ("wParam", ctypes.c_uint64),
                ("lParam", ctypes.c_uint64),
                ("time", wintypes.DWORD),
                ("pt", wintypes.POINT),
            ]

        msg = MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def start(self):
        threading.Thread(target=self._run_loop, daemon=True).start()

    def show(self):
        self.visible = True
        if self._hwnd:
            user32.ShowWindow(self._hwnd, 5)

    def hide(self):
        self.visible = False
        if self._hwnd:
            user32.ShowWindow(self._hwnd, 0)

    def stop(self):
        if self._hwnd:
            user32.PostMessageW(self._hwnd, 0x0010, 0, 0)  # WM_CLOSE

    def update_status(self, is_recording: bool):
        self.is_recording = is_recording
        if is_recording:
            self.partial_text = ""
            self._status_override = None
        self._draw_ui()

    def update_status_icon(self, status: str):
        self._status_override = status
        self._draw_ui()

    def update_partial_text(self, text: str):
        self.partial_text = text
        self._draw_ui()

    def update_voice_active(self, active: bool):
        self._voice_active = active
        self._draw_ui()


class IndicatorWindow:
    """Universal Indicator that uses HudOverlay (Skia) if available, otherwise GdiFallbackWindow."""

    def __init__(self, config: Optional["Config"] = None, design_style="glass"):
        from .config import Config

        self.config = config or Config()
        self._last_final_time = 0.0
        self._shown_at = 0.0
        self._final_flash_until = 0.0
        self._last_redraw_at = 0.0
        self._current_partial_text = ""
        self._committed_text = ""
        self._last_final_segment = ""
        self._max_preview_chars = getattr(self.config.ui.floating_indicator, "max_characters", 180)
        click_through = getattr(self.config.ui.floating_indicator, "click_through", True)

        if HUD_AVAILABLE:
            logger.info("Using Skia-based HudOverlay for recording indicator.")
            self.impl = HudOverlay(config=self.config, click_through=click_through)
        else:
            logger.info("Skia not available. Falling back to GDI+ indicator.")
            self.impl = GdiFallbackWindow(design_style=design_style, click_through=click_through)  # type: ignore

        # Register for config changes
        self.config.register_observer(self._on_config_changed)

    def _on_config_changed(self, config: "Config"):
        """Reacts to configuration updates in-flight."""
        if hasattr(self.impl, "apply_click_through"):
            self.impl.apply_click_through(config.ui.floating_indicator.click_through)

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
        if isinstance(self.impl, HudOverlay):
            threading.Thread(target=self.impl.run, daemon=True).start()
            if hasattr(self.impl, "_ready_event"):
                self.impl._ready_event.wait(timeout=2.0)
        else:
            self.impl.start()

    def show(self):
        if not self.visible:
            self._shown_at = time.time()
        self.impl.show()

    def hide(self):
        self.impl.hide()

    def stop(self):
        self.impl.stop()

    def update_status(self, is_recording: bool):
        if is_recording:
            self._last_final_time = 0.0
            self._current_partial_text = ""
            self._committed_text = ""
            self._last_final_segment = ""

        if hasattr(self.impl, "update_status"):
            self.impl.update_status(is_recording)

        # Trigger immediate render to show initial status
        self._render_preview()

        if not is_recording:
            self._start_linger_timer()

    def _start_linger_timer(self, duration: float = 2.5):
        def _hide_after():
            elapsed = time.time() - self._shown_at
            if elapsed < 0.3:
                time.sleep(0.3 - elapsed)
            time.sleep(duration)
            if not self.is_recording:
                self.hide()

        threading.Thread(target=_hide_after, daemon=True).start()

    def update_partial_text(self, text: str):
        self._current_partial_text = text
        now = time.time()
        if now - self._last_redraw_at < 0.05:
            return
        self._last_redraw_at = now
        self._render_preview()

    def update_voice_active(self, active: bool):
        if hasattr(self.impl, "update_voice_active"):
            self.impl.update_voice_active(active)

    def _render_preview(self):
        full_text = self._committed_text
        if self._current_partial_text:
            if full_text:
                full_text += " "
            full_text += self._current_partial_text

        if not full_text:
            display_text = ""
        elif len(full_text) > self._max_preview_chars:
            display_text = "…" + full_text[-(self._max_preview_chars - 1) :]
        else:
            display_text = full_text

        if hasattr(self.impl, "update_partial_text"):
            self.impl.update_partial_text(display_text)
        else:
            self.impl.update_text(display_text)

    def on_final(self, text: str, linger_seconds: float = 2.0):
        self._last_final_time = time.time()
        clean_text = text.strip()
        if clean_text and clean_text != self._last_final_segment:
            if self._committed_text:
                self._committed_text += " "
            self._committed_text += clean_text
            self._last_final_segment = clean_text

        self._current_partial_text = ""
        self._final_flash_until = time.time() + 0.2

        if hasattr(self.impl, "update_status_icon"):
            self.impl.update_status_icon("finalized")

        self._render_preview()

        if not self.is_recording:
            self.show()
            self._start_linger_timer(linger_seconds)
