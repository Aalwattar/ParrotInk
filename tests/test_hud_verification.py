import skia
from engine.hud_styles import GlassStyle

def test_hud_rendering_visual_verification():
    surface = skia.Surface(1000, 400)
    canvas = surface.getCanvas()
    canvas.clear(skia.ColorWHITE)

    style = GlassStyle()
    
    test_cases = [
        "Hello World (English)",
        "\u0627\u0644\u0633\u0644\u0627\u0645 \u0639\u0644\u064a\u0643\u0645 (Arabic)",
        "Hello \u0627\u0644\u0633\u0644\u0627\u0645 (Mixed)",
        "Short",
        "This is a very long transcription text to test the capsule width calculation "
        "and ensure it doesn't exceed the maximum width set in the style constants."
    ]
    
    y_offset = 20
    for text in test_cases:
        sub_surface = skia.Surface(1000, 60)
        sub_canvas = sub_surface.getCanvas()
        style.draw(sub_canvas, 1000, 60, text, is_recording=True)
        
        image = sub_surface.makeImageSnapshot()
        canvas.drawImage(image, 0, y_offset)
        y_offset += 70

    image = surface.makeImageSnapshot()
    image.save("hud_rtl_verification.png", skia.kPNG)
    print("Saved hud_rtl_verification.png.")

if __name__ == "__main__":
    test_hud_rendering_visual_verification()
