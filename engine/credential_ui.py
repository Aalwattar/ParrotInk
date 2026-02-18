from typing import Optional

import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, INFO, PRIMARY, RIGHT, SECONDARY, W, X


def ask_key(master, title: str, prompt: str = "") -> Optional[str]:
    """
    A modern, high-performance API key dialog using ttkbootstrap.
    Designed as a Toplevel child of the persistent GUI master.
    """
    # Create child window
    window = tb.Toplevel(master=master, title=title, resizable=(False, False))
    window.geometry("480x260")
    window.attributes("-topmost", True)

    # Internal state
    result: list[Optional[str]] = [None]

    # Main container
    main_frame = tb.Frame(window, padding=35)
    main_frame.pack(fill=BOTH, expand=True)

    # Header / Title
    tb.Label(main_frame, text=title, font=("Segoe UI Variable Display", 18, "bold")).pack(
        anchor=W, pady=(0, 8)
    )

    # Prompt
    if prompt:
        tb.Label(main_frame, text=prompt, font=("Segoe UI Variable Text", 9), bootstyle=INFO).pack(
            anchor=W, pady=(0, 25)
        )

    # Input Entry - Sophisticated Consolas look
    entry = tb.Entry(main_frame, font=("Consolas", 11), bootstyle=PRIMARY, show="*")
    entry.pack(fill=X, pady=(0, 30))
    entry.focus_set()

    def on_submit(event=None):
        val = entry.get().strip()
        if val:
            result[0] = val
            window.destroy()

    def on_cancel():
        window.destroy()

    # Footer Buttons - Luxury alignment and monochromatic styles
    btn_frame = tb.Frame(main_frame)
    btn_frame.pack(fill=X)

    btn_submit = tb.Button(
        btn_frame, text="Save Key", command=on_submit, bootstyle=PRIMARY, width=14
    )
    btn_submit.pack(side=RIGHT, padx=(12, 0))

    btn_cancel = tb.Button(
        btn_frame, text="Cancel", command=on_cancel, bootstyle=SECONDARY, width=10
    )
    btn_cancel.pack(side=RIGHT)

    # Bind Enter key
    entry.bind("<Return>", on_submit)
    entry.bind("<Escape>", lambda e: on_cancel())

    # Center window relative to master or screen
    window.deiconify()
    window.place_window_center()
    window.lift()
    window.focus_force()

    # Wait for completion (Modal)
    window.grab_set()
    window.wait_window()

    return result[0]
