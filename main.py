import pystray
from PIL import Image, ImageDraw


def create_image(width, height, color1, color2):
    # Generate a dummy image for the tray icon
    image = Image.new("RGB", (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle((width // 2, 0, width, height // 2), fill=color2)
    dc.rectangle((0, height // 2, width // 2, height), fill=color2)
    return image


def on_quit(icon, item):
    icon.stop()


# Define the menu
menu = pystray.Menu(pystray.MenuItem("Quit", on_quit))

# Create the icon
icon = pystray.Icon("test_icon", create_image(64, 64, "black", "white"), "Voice2Text Test", menu)

if __name__ == "__main__":
    print("Starting tray icon test...")
    # Note: run_detached would be better for a real app, but for testing
    # we can run it in the foreground and stop it via the menu or Ctrl+C
    icon.run()
