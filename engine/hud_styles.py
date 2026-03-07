import sys
import unicodedata
from abc import ABC, abstractmethod
from typing import Optional

import skia

from engine.constants import STATUS_LISTENING
from engine.logging import get_logger

logger = get_logger("HudStyles")

# Internal Constants (Not exposed to user)
CAPSULE_RADIUS = 18.0
CAPSULE_HEIGHT = 44.0
MAX_CAPSULE_WIDTH = 800.0
CAPSULE_PADDING = 8.0
TEXT_SIZE = 16
TEXT_MAX_LENGTH = 100

DOT_BASE_RADIUS = 3.0
DOT_GLOW_RADIUS_OFFSET = 1.5

# Global Text Layout Resources (Lazy Loaded)
_FONT_COLLECTION: Optional[skia.textlayout_FontCollection] = None
_UNICODE_MGR: Optional[skia.Unicode] = None


def _ensure_text_resources():
    """Lazily initializes Skia text layout resources with ICU support."""
    global _FONT_COLLECTION, _UNICODE_MGR
    if _FONT_COLLECTION is not None:
        return

    import os

    icu_found = False
    # 1. Attempt to locate icudtl.dat for Arabic/RTL shaping
    try:
        import skia as sk_mod

        skia_dir = os.path.dirname(sk_mod.__file__)
        # PyInstaller _MEIPASS support
        if hasattr(sys, "_MEIPASS"):
            # Check in the root of the temp folder
            icu_path = os.path.join(sys._MEIPASS, "icudtl.dat")
        else:
            icu_path = os.path.join(skia_dir, "icudtl.dat")

        if os.path.exists(icu_path):
            os.environ["SKIA_ICU_DIR"] = os.path.dirname(icu_path)
            logger.debug(f"Found ICU data at: {icu_path}")
            icu_found = True
        else:
            logger.warning(f"ICU data not found at {icu_path}. RTL shaping may be disabled.")
    except Exception as e:
        logger.debug(f"Failed to locate ICU data path: {e}")

    if icu_found:
        try:
            _UNICODE_MGR = skia.Unicode.ICU_Make()
            if _UNICODE_MGR is None:
                logger.warning("skia.Unicode.ICU_Make() returned None. RTL shaping disabled.")
        except Exception as e:
            logger.error(
                f"Critical error initializing Skia ICU: {e}. Falling back to basic shaping."
            )
            _UNICODE_MGR = None
    else:
        _UNICODE_MGR = None

    _FONT_COLLECTION = skia.textlayout_FontCollection()
    _FONT_COLLECTION.setDefaultFontManager(skia.FontMgr.RefDefault())


def is_rtl(text: str) -> bool:
    """Returns True if the text contains any RTL characters."""
    for char in text:
        try:
            if unicodedata.bidirectional(char) in ("R", "AL", "AN"):
                return True
        except ValueError:
            continue
    return False


class HudStyle(ABC):
    @abstractmethod
    def draw(
        self,
        canvas: skia.Canvas,
        width: int,
        height: int,
        text: str,
        is_recording: bool,
        status_override: Optional[str] = None,
        voice_active: bool = False,
        provider: Optional[str] = None,
        partial_text: str = "",
    ):
        pass


class GlassStyle(HudStyle):
    def __init__(self):
        self.radius = CAPSULE_RADIUS
        self.capsule_height = CAPSULE_HEIGHT
        self.max_capsule_width = MAX_CAPSULE_WIDTH
        self.padding = CAPSULE_PADDING

    def draw(
        self,
        canvas: skia.Canvas,
        width: int,
        height: int,
        text: str,
        is_recording: bool,
        status_override: Optional[str] = None,
        voice_active: bool = False,
        provider: Optional[str] = None,
        partial_text: str = "",
    ):
        canvas.clear(skia.ColorTRANSPARENT)
        _ensure_text_resources()

        # 1. Content Preparation
        # If we have both, combine them for truncation check
        full_display_text = text + partial_text

        is_listening_placeholder = (
            not full_display_text or full_display_text == STATUS_LISTENING
        ) and is_recording

        if is_listening_placeholder:
            display_committed = STATUS_LISTENING
            display_partial = ""
        else:
            display_committed = text
            display_partial = partial_text

        # Truncation logic (keep the end)
        total_len = len(display_committed) + len(display_partial)
        if total_len > TEXT_MAX_LENGTH:
            # Prioritize keeping partial text visible
            excess = total_len - TEXT_MAX_LENGTH
            if len(display_committed) > excess + 5:
                display_committed = "…" + display_committed[excess + 1 :]
            else:
                # If committed is too short, truncate partial too (rare)
                display_committed = "…"
                display_partial = display_partial[-(TEXT_MAX_LENGTH - 5) :]

        rtl = is_rtl(display_committed + display_partial)

        # 2. Modern Text Layout (Handles RTL/Shaping)
        para_style = skia.textlayout_ParagraphStyle()
        if rtl:
            para_style.setTextAlign(skia.textlayout_TextAlign.kRight)
        else:
            para_style.setTextAlign(skia.textlayout_TextAlign.kLeft)

        builder = skia.textlayout_ParagraphBuilder(para_style, _FONT_COLLECTION, _UNICODE_MGR)

        # Style for Committed (Final) Text
        committed_style = skia.textlayout_TextStyle()
        if is_listening_placeholder:
            committed_style.setColor(skia.ColorSetARGB(180, 255, 255, 255))
        else:
            committed_style.setColor(skia.ColorWHITE)
        committed_style.setFontSize(TEXT_SIZE)
        committed_style.setFontFamilies(["Segoe UI", "Arial", "sans-serif"])

        # Style for Partial (Thinking) Text - Dimmed
        partial_style = skia.textlayout_TextStyle()
        partial_style.setColor(skia.ColorSetARGB(120, 200, 200, 200))  # Muted Gray/Alpha
        partial_style.setFontSize(TEXT_SIZE)
        partial_style.setFontFamilies(["Segoe UI", "Arial", "sans-serif"])

        if display_committed:
            builder.pushStyle(committed_style)
            builder.addText(display_committed)
            builder.pop()

        if display_partial:
            # Add a leading space if needed
            if display_committed and not display_committed.endswith(" "):
                builder.pushStyle(partial_style)
                builder.addText(" ")
                builder.pop()

            builder.pushStyle(partial_style)
            builder.addText(display_partial)
            builder.pop()

        paragraph = builder.Build()
        paragraph.layout(self.max_capsule_width)
        text_width = paragraph.MaxIntrinsicWidth

        # 3. Minimalist Layout Math
        h_padding = 18.0
        dot_section_w = 8.0 + 10.0  # Dot Space + Gap

        total_content_w = dot_section_w + text_width
        capsule_w = max(100.0, min(total_content_w + (h_padding * 2), self.max_capsule_width))

        x_pos = (width - capsule_w) / 2.0
        rect = skia.Rect.MakeXYWH(x_pos, self.padding, capsule_w, self.capsule_height)
        rrect = skia.RRect.MakeEmpty()
        rrect.setRectXY(rect, self.radius, self.radius)

        # 4. Paint Background & Shadow
        shadow_paint = skia.Paint(
            Color=skia.ColorSetARGB(150, 0, 0, 0),
            AntiAlias=True,
            ImageFilter=skia.ImageFilters.Blur(8, 8),
        )
        canvas.drawRRect(rrect, shadow_paint)

        colors = [
            skia.ColorSetARGB(220, 25, 25, 25),
            skia.ColorSetARGB(200, 15, 15, 15),
        ]
        pts = [skia.Point(rect.fLeft, rect.fTop), skia.Point(rect.fLeft, rect.fBottom)]
        glass_paint = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(pts, colors))
        canvas.drawRRect(rrect, glass_paint)

        # 5. Drawing content
        # Dot Position
        dot_x = rect.fLeft + h_padding + 4.0
        dot_y = rect.fTop + (self.capsule_height / 2.0)

        # Provider Label (Subtle, above the dot)
        if provider:
            prov_paint = skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(130, 200, 200, 200))
            prov_font = skia.Font(skia.Typeface("Segoe UI"), 8)
            prov_text = provider.upper()
            prov_width = prov_font.measureText(prov_text)
            # Center it horizontally relative to the dot
            canvas.drawSimpleText(
                prov_text,
                dot_x - (prov_width / 2.0),
                rect.fTop + 10.0,
                prov_font,
                prov_paint,
            )

        # Dot Visuals

        base_radius = DOT_BASE_RADIUS
        if voice_active:
            dot_radius = base_radius + 1.0
            glow_alpha = 180
            blur_sigma = 3.0
        else:
            dot_radius = base_radius
            glow_alpha = 100
            blur_sigma = 1.5

        status_label = (status_override or "LISTENING").upper() if is_recording else "STANDBY"
        dot_color = skia.ColorCYAN
        if status_label == "FINALIZED":
            dot_color = skia.ColorSetARGB(255, 40, 200, 80)
        elif status_label == "ERROR":
            dot_color = skia.ColorRED
        elif not is_recording:
            dot_color = skia.ColorGRAY

        # Glow
        if is_recording or status_label == "FINALIZED":
            glow_paint = skia.Paint(
                AntiAlias=True,
                Color=dot_color,
                Alpha=glow_alpha,
                ImageFilter=skia.ImageFilters.Blur(blur_sigma, blur_sigma),
            )
            canvas.drawCircle(dot_x, dot_y, dot_radius + DOT_GLOW_RADIUS_OFFSET, glow_paint)

        canvas.drawCircle(
            dot_x,
            dot_y,
            dot_radius,
            skia.Paint(Color=dot_color, AntiAlias=True),
        )

        # Transcription Text
        # text_y = rect.fTop + (self.capsule_height - paragraph.Height) / 2.0
        # For Paragraph, paint draws from top-left.
        # If RTL and TextAlign.kRight, the text will be aligned to the RIGHT of the layout width.
        # We laid out with self.max_capsule_width.
        # We need to offset it so it starts after the dot.

        text_x = dot_x + 14.0
        text_y = rect.fTop + (self.capsule_height - paragraph.Height) / 2.0

        # If RTL, paragraph.layout(max_capsule_width) with TextAlign.kRight
        # means the text is at the far right of that max width.
        # We should layout with the ACTUAL text_width instead.
        paragraph.layout(text_width + 1.0)  # Add a tiny buffer

        paragraph.paint(canvas, text_x, text_y)
