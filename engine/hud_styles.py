import skia
from abc import ABC, abstractmethod

class HudStyle(ABC):
    @abstractmethod
    def draw(self, canvas: skia.Canvas, width: int, height: int, text: str, is_recording: bool):
        pass

class GlassStyle(HudStyle):
    def __init__(self):
        self.radius = 12.0
        self.capsule_height = 42.0  # Narrower (thinner) for a sleeker look
        self.max_capsule_width = 800.0 # Longer to fit more text
        self.padding = 30.0

    def draw(self, canvas: skia.Canvas, width: int, height: int, text: str, is_recording: bool):
        canvas.clear(skia.ColorTRANSPARENT)

        # 1. Measure Text
        font = skia.Font(skia.Typeface("Segoe UI"), 14)
        blob = skia.TextBlob.MakeFromString(text, font)
        text_width = font.measureText(text)

        # 2. Layout
        # Adjust width to fit text + padding for status dot
        capsule_w = max(120.0, min(text_width + 80.0, self.max_capsule_width))
        rect = skia.Rect.MakeXYWH(self.padding, self.padding, capsule_w, self.capsule_height)
        rrect = skia.RRect.MakeEmpty()
        rrect.setRectXY(rect, self.radius, self.radius)

        # 3. Drop Shadow
        shadow_paint = skia.Paint(
            Color=skia.ColorSetARGB(120, 0, 0, 0), # Slightly darker shadow
            AntiAlias=True,
            ImageFilter=skia.ImageFilters.Blur(12, 12)
        )
        canvas.drawRRect(rrect, shadow_paint)

        # 4. Glass Container (Reduced transparency / Higher Opacity)
        # Increased Alpha from 38/25 to 70/50 for better visibility
        colors = [skia.ColorSetARGB(70, 255, 255, 255), skia.ColorSetARGB(50, 180, 180, 180)]
        pts = [skia.Point(rect.fLeft, rect.fTop), skia.Point(rect.fLeft, rect.fBottom)]
        glass_paint = skia.Paint(
            AntiAlias=True,
            Shader=skia.GradientShader.MakeLinear(pts, colors)
        )
        canvas.drawRRect(rrect, glass_paint)

        # 5. Rim Border (Slightly more visible)
        rim_paint = skia.Paint(
            Style=skia.Paint.kStroke_Style,
            StrokeWidth=1.2,
            Color=skia.ColorSetARGB(100, 255, 255, 255),
            AntiAlias=True
        )
        canvas.drawRRect(rrect, rim_paint)

        # 6. Cyan Glow / Active Dot
        dot_x, dot_y = rect.fLeft + 20.0, rect.centerY()
        dot_radius = 4.0
        if is_recording:
            glow_colors = [skia.ColorCYAN, skia.ColorTRANSPARENT]
            glow_shader = skia.GradientShader.MakeRadial(skia.Point(dot_x, dot_y), dot_radius * 3.0, glow_colors)
            glow_paint = skia.Paint(
                AntiAlias=True, 
                Shader=glow_shader, 
                ImageFilter=skia.ImageFilters.Blur(3, 3)
            )
            canvas.drawCircle(dot_x, dot_y, dot_radius * 2.5, glow_paint)
            canvas.drawCircle(dot_x, dot_y, dot_radius, skia.Paint(Color=skia.ColorCYAN, AntiAlias=True))
        else:
            canvas.drawCircle(dot_x, dot_y, dot_radius, skia.Paint(Color=skia.ColorSetARGB(100, 150, 150, 150), AntiAlias=True))

        # 7. Text (Pure White)
        canvas.drawTextBlob(blob, rect.fLeft + 40.0, rect.centerY() + 6.0, skia.Paint(Color=skia.ColorWHITE, AntiAlias=True))
