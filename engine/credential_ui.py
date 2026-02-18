import tkinter as tk
from typing import Optional

import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, LEFT, PRIMARY, RIGHT, SECONDARY, X


def ask_key(master, title: str, prompt: str = "") -> Optional[str]:
    """
    A compact, high-impact API Key dialog.
    Large title focus, tightened padding, and symmetrical footer.
    """
    # 1. WINDOW SETUP
    window = tb.Toplevel(master=master)
    window.overrideredirect(True)
    window.attributes("-topmost", True)

    # Ultra-wide cinematic size for long keys
    width, height = 600, 280
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    x = (screen_w - width) // 2
    y = (screen_h - height) // 2
    # FIX: Correctly set both size and position
    window.geometry(f"{width}x{height}+{x}+{y}")

    bg_color = "#0A0A0A"
    window.configure(background=bg_color)

    # Internal state
    result: list[Optional[str]] = [None]

    # Drag Logic
    drag_data = {"x": 0, "y": 0}

    def start_move(event):
        drag_data["x"] = event.x
        drag_data["y"] = event.y

    def do_move(event):
        deltax = event.x - drag_data["x"]
        deltay = event.y - drag_data["y"]
        window.geometry(f"+{window.winfo_x() + deltax}+{window.winfo_y() + deltay}")

    window.bind("<Button-1>", start_move)
    window.bind("<B1-Motion>", do_move)

    # Main centered container
    content = tk.Frame(window, background=bg_color, padx=35, pady=25)
    content.pack(fill=BOTH, expand=True)

    # --- 2. HEADER ---
    header = tk.Frame(content, background=bg_color)
    header.pack(fill=X, pady=(0, 15))

    tk.Label(
        header,
        text="PARROTINK // CREDENTIALS",
        font=("Segoe UI", 7, "bold"),
        foreground="#444444",
        background=bg_color,
    ).pack(side=LEFT)

    close_btn = tk.Label(
        header,
        text="✕",
        background=bg_color,
        foreground="#666666",
        cursor="hand2",
        font=("Segoe UI", 10),
    )
    close_btn.pack(side=RIGHT)
    close_btn.bind("<Button-1>", lambda e: window.destroy())
    close_btn.bind("<Enter>", lambda e: close_btn.configure(foreground="#FFFFFF"))
    close_btn.bind("<Leave>", lambda e: close_btn.configure(foreground="#666666"))

    # --- 3. LARGE TITLE ---
    display_title = title if "Key" in title else f"Set {title} Key"
    tk.Label(
        content,
        text=display_title,
        font=("Segoe UI Variable Display", 18, "bold"),
        foreground="#FFFFFF",
        background=bg_color,
    ).pack(anchor="w", pady=(5, 25))

    # --- 4. INPUT ---
    entry = tb.Entry(
        content,
        font=("Consolas", 11),
        bootstyle=PRIMARY,
        show="*",
    )
    entry.pack(fill=X, pady=(0, 25))
    entry.focus_set()

    def on_submit(event=None):
        val = entry.get().strip()
        if val:
            result[0] = val
            window.destroy()

    # --- 5. FOOTER (Tight Padding) ---
    btn_frame = tk.Frame(content, background=bg_color)
    btn_frame.pack(fill=X, pady=(0, 0))

    tb.Button(
        btn_frame,
        text="SAVE KEY",
        command=on_submit,
        bootstyle=PRIMARY,
        width=12,
    ).pack(side=RIGHT, padx=(10, 0))

    tb.Button(
        btn_frame,
        text="CANCEL",
        command=window.destroy,
        bootstyle=SECONDARY,
        width=10,
    ).pack(side=RIGHT)

    # Bindings
    entry.bind("<Return>", on_submit)
    entry.bind("<Escape>", lambda e: window.destroy())

    # Finalize
    window.deiconify()
    window.lift()
    window.focus_force()
    window.grab_set()
    window.wait_window()

    return result[0]
