from abc import ABC, abstractmethod

import skia

# Internal Constants (Not exposed to user)
CAPSULE_RADIUS = 18.0
CAPSULE_HEIGHT = 44.0
MAX_CAPSULE_WIDTH = 800.0
CAPSULE_PADDING = 8.0
TEXT_SIZE = 16
TEXT_MAX_LENGTH = 100

DOT_BASE_RADIUS = 3.0
DOT_GLOW_RADIUS_OFFSET = 1.5


class HudStyle(ABC):
    @abstractmethod
    def draw(
        self,
        canvas: skia.Canvas,
        width: int,
        height: int,
        text: str,
        is_recording: bool,
        status_override: str | None = None,
        voice_active: bool = False,
        provider: str | None = None,
    ):
        pass


class GlassStyle(HudStyle):
    def __init__(self):
        self.radius = CAPSULE_RADIUS
        self.capsule_height = CAPSULE_HEIGHT  # Increased for larger 16pt font
        self.max_capsule_width = MAX_CAPSULE_WIDTH
        self.padding = CAPSULE_PADDING

    def draw(
        self,
        canvas: skia.Canvas,
        width: int,
        height: int,
        text: str,
        is_recording: bool,
        status_override: str | None = None,
        voice_active: bool = False,
        provider: str | None = None,
    ):
        canvas.clear(skia.ColorTRANSPARENT)

        # 1. Setup Fonts - Increased to 16pt for top-tier readability
        try:
            tf_reg = skia.Typeface.MakeFromName("Segoe UI", skia.FontStyle.Normal())
        except Exception:
            tf_reg = skia.Typeface.MakeDefault()

        font_text = skia.Font(tf_reg, TEXT_SIZE)

        # 2. Content Preparation
        is_listening_placeholder = False
        if not text and is_recording:
            display_text = "Listening..."
            is_listening_placeholder = True
        else:
            display_text = text if text else "..."

        if len(display_text) > TEXT_MAX_LENGTH:
            display_text = "…" + display_text[-(TEXT_MAX_LENGTH - 1) :]

        # Use slightly more transparent paint for placeholder
        if is_listening_placeholder:
            text_paint = skia.Paint(Color=skia.ColorSetARGB(180, 255, 255, 255), AntiAlias=True)
        else:
            text_paint = skia.Paint(Color=skia.ColorWHITE, AntiAlias=True)

        content_blob = skia.TextBlob.MakeFromString(display_text, font_text)
        text_width = font_text.measureText(display_text)

        # 3. Minimalist Layout Math (Dot Only + Text)
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
        baseline_y = rect.fTop + (self.capsule_height / 2.0) + 6.0

        # Dot Position
        dot_x = rect.fLeft + h_padding + 4.0
        dot_y = rect.fTop + (self.capsule_height / 2.0)

        # Dot Visuals (Dynamic based on voice_active)
        base_radius = DOT_BASE_RADIUS
        if voice_active:
            dot_radius = base_radius + 1.0  # Subtle grow
            glow_alpha = 180
            blur_sigma = 3.0
        else:
            dot_radius = base_radius
            glow_alpha = 100
            blur_sigma = 1.5

        # Determine Color
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
        canvas.drawTextBlob(content_blob, dot_x + 14.0, baseline_y - 1.0, text_paint)
