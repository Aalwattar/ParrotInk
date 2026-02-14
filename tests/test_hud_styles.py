import skia

from engine.hud_styles import GlassStyle


def test_glass_style_typography():
    style = GlassStyle()
    # We can't easily inspect the Font without drawing,
    # but we can verify the constants if we expose them or just check the code.
    # For now, let's just ensure it can be instantiated and the draw method doesn't crash.
    surface = skia.Surface(200, 100)
    canvas = surface.getCanvas()

    # This will at least catch errors in the draw logic
    style.draw(canvas, 200, 100, "Test Text", is_recording=True)


def test_glass_style_dimensions():
    style = GlassStyle()
    # Target: 16pt font, so capsule height should probably be around 40-44
    assert style.capsule_height >= 40.0
