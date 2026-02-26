import skia
import os

def test_arabic_rendering():
    surface = skia.Surface(400, 200)
    canvas = surface.getCanvas()
    canvas.clear(skia.ColorWHITE)

    text = "Ø§Ù„Ø³Ù„Ø§Ù… Ø¹Ù„ÙŠÙƒÙ…" # "As-salamu alaykum"
    
    # 1. Current Way: TextBlob
    paint = skia.Paint(AntiAlias=True, Color=skia.ColorBLACK)
    font = skia.Font(skia.Typeface("Segoe UI"), 24)
    blob = skia.TextBlob.MakeFromString(text, font)
    canvas.drawTextBlob(blob, 20, 50, paint)
    
    # 2. New Way: textlayout
    font_collection = skia.textlayout_FontCollection()
    font_collection.setDefaultFontManager(skia.FontMgr.RefDefault())
    
    para_style = skia.textlayout_ParagraphStyle()
    para_style.setTextAlign(skia.textlayout_TextAlign.kRight)
    # RTL direction
    # Note: Enum name might vary, let's try to find it
    # para_style.setTextDirection(skia.textlayout_TextDirection.kRtl) 
    
    unicode_mgr = skia.Unicode.ICU_Make()
    builder = skia.textlayout_ParagraphBuilder(para_style, font_collection, unicode_mgr)
    
    text_style = skia.textlayout_TextStyle()
    text_style.setColor(skia.ColorBLACK)
    text_style.setFontSize(24)
    text_style.setFontFamilies(["Segoe UI"])
    
    builder.pushStyle(text_style)
    builder.addText(text)
    builder.pop()
    
    paragraph = builder.Build()
    paragraph.layout(360) # width
    paragraph.paint(canvas, 20, 100)

    image = surface.makeImageSnapshot()
    image.save("arabic_test.png", skia.kPNG)
    print("Saved arabic_test.png. Please inspect visually if possible.")

if __name__ == "__main__":
    try:
        test_arabic_rendering()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
