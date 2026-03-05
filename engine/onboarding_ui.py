import os
import sys
from pathlib import Path

# Senior Architecture: Path Shadowing Guard
if __name__ == "__main__":
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    if _script_dir in sys.path:
        sys.path.remove(_script_dir)

import tkinter as tk

import ttkbootstrap as tb
from PIL import Image, ImageTk
from ttkbootstrap.constants import BOTH, CENTER, LEFT, PRIMARY, RIGHT, TOP, X

from .ui_utils import get_resource_path


def show_onboarding_blocking() -> bool:
    """
    Shows a world-class, high-fidelity onboarding popup with visual icons.
    Returns True if 'Don't show again' was checked.
    """
    # 1. WINDOW SETUP
    style = tb.Style(theme="superhero")
    root = style.master
    root.withdraw()

    window = tb.Toplevel(master=root)
    window.title("ParrotInk - Welcome")
    window.attributes("-topmost", True)

    # Cinematic Size and Centering - Increased height to 780 to ensure visibility
    width, height = 640, 780
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    x = (screen_w - width) // 2
    y = (screen_h - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")
    window.resizable(False, False)

    # State
    dont_show_again = tk.BooleanVar(value=False)
    images = []

    def load_icon(name: str, size: int = 32) -> ImageTk.PhotoImage:
        path = Path(get_resource_path(os.path.join("assets", "icons", name)))
        if not path.exists():
            img = Image.new("RGBA", (size, size), (100, 100, 100, 255))
        else:
            img = Image.open(path)
            img = img.resize((size, size), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        images.append(photo)
        return photo

    # Content Container
    content = tb.Frame(window, padding=(40, 40))
    content.pack(fill=BOTH, expand=True)

    # --- 1. BRANDING HEADER ---
    header_frame = tb.Frame(content)
    header_frame.pack(fill=X, pady=(0, 30))

    brand_icon = load_icon("icon.ico", 64)
    tb.Label(header_frame, image=brand_icon).pack(side=TOP, pady=(0, 15))

    tb.Label(
        header_frame,
        text="WELCOME TO PARROTINK",
        font=("Segoe UI", 10, "bold"),
        bootstyle=PRIMARY,
    ).pack(side=TOP)

    tb.Label(
        header_frame,
        text="Your Intelligent Voice Assistant",
        font=("Segoe UI Variable Display", 24, "bold"),
    ).pack(side=TOP, pady=(5, 0))

    # --- 2. INTRODUCTION ---
    intro_text = (
        "ParrotInk runs silently in your System Tray (the area with small icons "
        "next to your clock). Just press your hotkey, speak, and watch your "
        "words appear instantly at your cursor."
    )
    tb.Label(content, text=intro_text, font=("Segoe UI", 12), wraplength=540, justify=CENTER).pack(
        side=TOP, pady=(0, 35)
    )

    # --- 3. VISUAL GUIDE: TRAY COLORS ---
    tb.Label(
        content,
        text="UNDERSTANDING THE TRAY ICON",
        font=("Segoe UI", 9, "bold"),
        foreground="#888888",
    ).pack(anchor="w", pady=(0, 15))

    guide_frame = tb.Frame(content)
    guide_frame.pack(fill=X, pady=(0, 35))

    states = [
        ("tray_idle.ico", "Idle", "Ready & waiting"),
        ("tray_listening.ico", "Listening", "Capturing audio"),
        ("tray_connecting.ico", "Connecting", "Secure link active"),
        ("tray_error.ico", "Error", "Action required"),
    ]

    for i, (icon_name, label, desc) in enumerate(states):
        f = tb.Frame(guide_frame)
        f.grid(row=0, column=i, padx=15, sticky="nsew")
        guide_frame.columnconfigure(i, weight=1)

        icon_img = load_icon(icon_name, 48)
        tb.Label(f, image=icon_img).pack(side=TOP, pady=(0, 10))
        tb.Label(f, text=label, font=("Segoe UI", 10, "bold")).pack(side=TOP)
        tb.Label(f, text=desc, font=("Segoe UI", 8), foreground="#AAAAAA").pack(side=TOP)

    # --- 4. QUICK STEPS ---
    step_frame = tb.Frame(content, bootstyle="secondary", padding=25)
    step_frame.pack(fill=X, pady=(0, 30))

    steps = [
        ("🔑 Setup", "Right-click tray > Settings > API Credentials to add your key."),
        ("❓ Help", "Check the 'Help' menu for hotkeys and documentation."),
    ]

    for title, text in steps:
        sf = tb.Frame(step_frame, bootstyle="secondary")
        sf.pack(fill=X, pady=5)
        tb.Label(sf, text=title, font=("Segoe UI", 11, "bold"), bootstyle="inverse-secondary").pack(
            side=LEFT, padx=(0, 15)
        )
        tb.Label(
            sf,
            text=text,
            font=("Segoe UI", 10),
            bootstyle="inverse-secondary",
            wraplength=400,
            justify=LEFT,
        ).pack(side=LEFT)

    # --- 5. PRO TIP ---
    tb.Label(
        content,
        text="💡 Pro Tip: Drag the icon out of the 'Hidden Icons' arrow to keep it always visible!",
        font=("Segoe UI", 10, "italic"),
        bootstyle="info",
    ).pack(anchor="w", pady=(0, 35))

    # --- FOOTER ---
    footer = tb.Frame(content)
    footer.pack(fill=X, side="bottom")

    tb.Checkbutton(
        footer,
        text="Don't show this again",
        variable=dont_show_again,
        bootstyle="primary-round-toggle",
    ).pack(side=LEFT)

    def on_close():
        window.destroy()
        root.destroy()

    tb.Button(footer, text="GET STARTED", command=on_close, bootstyle=PRIMARY, width=18).pack(
        side=RIGHT
    )

    window.protocol("WM_DELETE_WINDOW", on_close)
    window.focus_force()
    window.grab_set()
    window.wait_window()

    # Senior Architecture: Reset the ttkbootstrap Style singleton.
    try:
        tb.Style.instance = None
    except Exception:
        pass

    return dont_show_again.get()


if __name__ == "__main__":
    # Test runner
    print("Launching world-class onboarding popup...")

    def get_resource_path_local(path):
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), path)

    import engine.onboarding_ui as onboarding_ui

    onboarding_ui.get_resource_path = get_resource_path_local

    result = show_onboarding_blocking()
    print(f"User requested to hide future popups: {result}")
