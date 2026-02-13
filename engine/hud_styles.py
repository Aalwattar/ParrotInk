from abc import ABC, abstractmethod

import skia


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
    ):
        pass


class GlassStyle(HudStyle):
    def __init__(self):
        self.radius = 10.0
        self.capsule_height = 50.0  # Taller for 2 lines
        self.max_capsule_width = 800.0
        self.padding = 15.0

    def draw(
        self,
        canvas: skia.Canvas,
        width: int,
        height: int,
        text: str,
        is_recording: bool,
        status_override: str | None = None,
    ):
        canvas.clear(skia.ColorTRANSPARENT)

        # 1. Determine Status Label
        status_label = (status_override or "LISTENING").upper() if is_recording else "STANDBY"

        # 2. Setup Fonts
        try:
            tf_bold = skia.Typeface.MakeFromName("Segoe UI", skia.FontStyle.Bold())
            tf_reg = skia.Typeface.MakeFromName("Segoe UI", skia.FontStyle.Normal())
        except Exception:
            tf_bold = skia.Typeface.MakeDefault()
            tf_reg = skia.Typeface.MakeDefault()

        font_status = skia.Font(tf_bold, 9)
        font_text = skia.Font(tf_reg, 12)

        # 3. Content Preparation
        display_text = text if text else "..."
        # Limit text length visually for the HUD's line width
        if len(display_text) > 120:
            display_text = "…" + display_text[-117:]

        status_blob = skia.TextBlob.MakeFromString(status_label, font_status)
        content_blob = skia.TextBlob.MakeFromString(display_text, font_text)

        text_width = font_text.measureText(display_text)
        status_width = font_status.measureText(status_label)

        # 4. Refined Layout Math
        h_padding = 20.0
        # Calculate width to exactly fit the wider of the two lines + padding
        content_width = max(text_width, status_width + 12.0)  # 12.0 is dot + gap
        capsule_w = max(140.0, min(content_width + (h_padding * 2), self.max_capsule_width))

        x_pos = (width - capsule_w) / 2.0

        # Draw the capsule centered vertically in the window
        rect = skia.Rect.MakeXYWH(x_pos, self.padding, capsule_w, self.capsule_height)
        rrect = skia.RRect.MakeEmpty()
        rrect.setRectXY(rect, self.radius, self.radius)

        # 5. Paint Background & Shadow
        shadow_paint = skia.Paint(
            Color=skia.ColorSetARGB(120, 0, 0, 0),
            AntiAlias=True,
            ImageFilter=skia.ImageFilters.Blur(8, 8),
        )
        canvas.drawRRect(rrect, shadow_paint)

        # Darker glass for better contrast
        colors = [skia.ColorSetARGB(200, 25, 25, 25), skia.ColorSetARGB(180, 15, 15, 15)]
        pts = [skia.Point(rect.fLeft, rect.fTop), skia.Point(rect.fLeft, rect.fBottom)]
        glass_paint = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(pts, colors))
        canvas.drawRRect(rrect, glass_paint)

        rim_paint = skia.Paint(
            Style=skia.Paint.kStroke_Style,
            StrokeWidth=1.0,
            Color=skia.ColorSetARGB(80, 255, 255, 255),
            AntiAlias=True,
        )
        canvas.drawRRect(rrect, rim_paint)

        # 6. Line 1: Status Dot + Label
        dot_x, dot_y = rect.fLeft + h_padding, rect.fTop + 16.0
        dot_radius = 3.0

        dot_color = skia.ColorCYAN
        if status_label == "FINALIZED":
            dot_color = skia.ColorSetARGB(255, 40, 200, 80)  # Green
        elif status_label == "ERROR":
            dot_color = skia.ColorRED
        elif not is_recording:
            dot_color = skia.ColorGRAY

        # Subtle static glow
        if is_recording or status_label == "FINALIZED":
            glow_paint = skia.Paint(
                AntiAlias=True, Color=dot_color, Alpha=120, ImageFilter=skia.ImageFilters.Blur(2, 2)
            )
            canvas.drawCircle(dot_x, dot_y, dot_radius + 1.0, glow_paint)

        canvas.drawCircle(dot_x, dot_y, dot_radius, skia.Paint(Color=dot_color, AntiAlias=True))

        status_paint = skia.Paint(Color=skia.ColorSetARGB(200, 220, 220, 220), AntiAlias=True)
        canvas.drawTextBlob(status_blob, dot_x + 12.0, dot_y + 3.5, status_paint)

        # 7. Line 2: Rolling Preview Text
        text_paint = skia.Paint(Color=skia.ColorWHITE, AntiAlias=True)
        # Perfectly aligned with the dot's horizontal start
        text_x = rect.fLeft + h_padding
        text_y = rect.fTop + 38.0
        canvas.drawTextBlob(content_blob, text_x, text_y, text_paint)
