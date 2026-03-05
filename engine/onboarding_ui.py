import os
import sys

# Senior Architecture: Path Shadowing Guard
# If run directly as a script (e.g. 'python engine/onboarding_ui.py'), the script's
# directory is added to the front of sys.path. This causes 'import logging' in
# libraries like PIL to mistakenly find 'engine/logging.py'.
if __name__ == "__main__":
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    if _script_dir in sys.path:
        sys.path.remove(_script_dir)

import tkinter as tk

import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, LEFT, PRIMARY, RIGHT, X


def show_onboarding_blocking() -> bool:
    """
    Shows a high-fidelity onboarding popup and returns True if 'Don't show again' was checked.
    This is a blocking call that runs its own Tcl/Tk mainloop.
    """
    # 1. WINDOW SETUP
    # We use a standalone root because this runs BEFORE main_gui
    style = tb.Style(theme="superhero")  # Match the app's dark theme
    root = style.master

    # Senior Architecture: Hide the main window and set it as a utility
    root.withdraw()

    window = tb.Toplevel(master=root)
    window.title("ParrotInk - Welcome")

    # Make it always on top as requested
    window.attributes("-topmost", True)

    # Cinematic Size and Centering
    width, height = 580, 520
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    x = (screen_w - width) // 2
    y = (screen_h - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")
    window.resizable(False, False)

    # State
    dont_show_again = tk.BooleanVar(value=False)

    # Content Container
    content = tb.Frame(window, padding=(35, 30))
    content.pack(fill=BOTH, expand=True)

    # --- Header ---
    tb.Label(
        content, text="WELCOME TO PARROTINK", font=("Segoe UI", 9, "bold"), bootstyle=PRIMARY
    ).pack(anchor="w", pady=(0, 10))

    tb.Label(
        content,
        text="Your New Voice Assistant",
        font=("Segoe UI Variable Display", 22, "bold"),
    ).pack(anchor="w", pady=(0, 20))

    # --- Introduction ---
    intro_text = (
        "ParrotInk is now running! Unlike traditional apps, it lives entirely "
        "in your system tray (the area next to your clock)."
    )
    tb.Label(content, text=intro_text, font=("Segoe UI", 12), wraplength=510, justify="left").pack(
        anchor="w", pady=(0, 25)
    )

    # --- Key Instructions (Visual Card style) ---
    instruction_frame = tb.Frame(content, bootstyle="secondary", padding=20)
    instruction_frame.pack(fill=X, pady=(0, 25))

    instructions = [
        (
            "🔑 Setup",
            "Right-click tray > Settings > API Credentials to add your OpenAI or AssemblyAI key.",
        ),
        ("🎨 Colors", "Grey = Idle, Blue = Listening, Red = Error, Yellow = Connecting."),
        ("❓ Help", "Check the 'Help' menu in the tray for hotkeys and documentation."),
    ]

    for title, text in instructions:
        f = tb.Frame(instruction_frame, bootstyle="secondary")
        f.pack(fill=X, pady=5)
        tb.Label(f, text=title, font=("Segoe UI", 11, "bold"), bootstyle="inverse-secondary").pack(
            side=LEFT, padx=(0, 10)
        )
        tb.Label(
            f,
            text=text,
            font=("Segoe UI", 10),
            bootstyle="inverse-secondary",
            wraplength=380,
            justify="left",
        ).pack(side=LEFT)

    # --- Tip ---
    tb.Label(
        content,
        text="💡 Pro Tip: Drag the icon out of the 'Hidden Icons' arrow to keep it visible!",
        font=("Segoe UI", 10, "italic"),
        bootstyle="info",
    ).pack(anchor="w", pady=(0, 30))

    # --- Footer ---
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

    tb.Button(footer, text="GET STARTED", command=on_close, bootstyle=PRIMARY, width=15).pack(
        side=RIGHT
    )

    window.protocol("WM_DELETE_WINDOW", on_close)
    window.focus_force()
    window.grab_set()
    window.wait_window()

    return dont_show_again.get()


if __name__ == "__main__":
    # Test runner
    print("Launching onboarding popup...")
    result = show_onboarding_blocking()
    print(f"User requested to hide future popups: {result}")
