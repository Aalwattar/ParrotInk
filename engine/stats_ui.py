import tkinter as tk
from typing import Any, Dict

import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, LEFT, RIGHT, X


def show_stats_dialog(master, stats_report: Dict[str, Any]):
    """
    Technical Luxury HUD v6 - Final Polish.
    Increased tab visibility and absolute stability.
    """
    # --- 1. DESIGN SYSTEM ---
    BG_COLOR = "#0A0A0A"  # Deep Technical Black
    TEXT_WHITE = "#FFFFFF"
    TEXT_MUTED = "#888888"  # Increased visibility for inactive tabs
    ACCENT_CYAN = "#33B5E5"
    ACCENT_PURPLE = "#E040FB"

    # --- 2. WINDOW SETUP ---
    window = tb.Toplevel(master=master)
    window.overrideredirect(True)
    window.geometry("440x700")
    window.configure(background=BG_COLOR)

    # Center window
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    x = (screen_w - 440) // 2
    y = (screen_h - 700) // 2
    window.geometry(f"+{x}+{y}")

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

    # UI State
    hero_val = tk.StringVar()
    dur_val = tk.StringVar()
    word_val = tk.StringVar()
    err_val = tk.StringVar()

    # Dynamic Container Placeholder
    provider_container = tk.Frame(window, background=BG_COLOR)

    def update_ui(tab_name: str):
        key_map = {
            "TODAY": "today",
            "WEEKLY": "this_week",
            "MONTHLY": "this_month",
            "LIFETIME": "lifetime",
        }
        data = stats_report.get(key_map.get(tab_name, "lifetime"), {})

        # 1. Update Metrics
        hero_val.set(str(data.get("total_transcriptions", 0)))
        dur_min = round(data.get("total_duration_seconds", 0) / 60, 1)
        dur_val.set(f"{dur_min}m")
        word_val.set(f"{data.get('total_words', 0):,}")
        err_val.set(str(data.get("error_count", 0)))

        # 2. Update Provider List
        for widget in provider_container.winfo_children():
            widget.destroy()

        providers = data.get("provider_usage", {})
        total_sessions = data.get("total_transcriptions", 0) or 1

        if not providers:
            tk.Label(
                provider_container,
                text="NO ACTIVITY DATA",
                font=("Segoe UI", 8, "bold"),
                foreground="#444444",
                background=BG_COLOR,
            ).pack(anchor="w", pady=20)
        else:
            for name, count in sorted(providers.items(), key=lambda x: x[1], reverse=True):
                row = tk.Frame(provider_container, background=BG_COLOR, pady=10)
                row.pack(fill=X)

                lbl_row = tk.Frame(row, background=BG_COLOR)
                lbl_row.pack(fill=X)

                tk.Label(
                    lbl_row,
                    text=name.upper(),
                    font=("Segoe UI", 9, "bold"),
                    foreground="#BBBBBB",
                    background=BG_COLOR,
                ).pack(side=LEFT)
                tk.Label(
                    lbl_row,
                    text=str(count),
                    font=("Segoe UI", 10, "bold"),
                    foreground=TEXT_WHITE,
                    background=BG_COLOR,
                ).pack(side=RIGHT)

                # Progress Bar
                pct = int((count / total_sessions) * 100)
                bstyle = "info" if "assembly" in name.lower() else "primary"
                if "open" in name.lower():
                    bstyle = "primary"

                tb.Progressbar(row, value=pct, bootstyle=bstyle).pack(fill=X, pady=(5, 0))

        # 3. Nav Highlight
        for name, lbl in nav_labels.items():
            if name == tab_name:
                lbl.configure(foreground=TEXT_WHITE, font=("Segoe UI", 9, "bold"))
            else:
                lbl.configure(foreground=TEXT_MUTED, font=("Segoe UI", 9, "normal"))

    # --- 3. COMPONENTS ---

    # Header
    header = tk.Frame(window, background=BG_COLOR, padx=30, pady=25)
    header.pack(fill=X)

    tk.Label(
        header,
        text="PARROTINK // ANALYTICS",
        font=("Segoe UI", 7, "bold"),
        foreground="#444444",
        background=BG_COLOR,
    ).pack(side=LEFT)

    close_btn = tk.Label(
        header,
        text="✕",
        background=BG_COLOR,
        foreground="#666666",
        cursor="hand2",
        font=("Segoe UI", 12),
    )
    close_btn.pack(side=RIGHT)
    close_btn.bind("<Button-1>", lambda e: window.destroy())
    close_btn.bind("<Enter>", lambda e: close_btn.configure(foreground="#FFFFFF"))
    close_btn.bind("<Leave>", lambda e: close_btn.configure(foreground="#666666"))

    # Nav
    nav = tk.Frame(window, background=BG_COLOR, pady=10)
    nav.pack(fill=X)
    nav_container = tk.Frame(nav, background=BG_COLOR)
    nav_container.pack()

    nav_labels = {}
    for t in ["TODAY", "WEEKLY", "MONTHLY", "LIFETIME"]:
        lbl = tk.Label(
            nav_container,
            text=t,
            foreground=TEXT_MUTED,
            background=BG_COLOR,
            cursor="hand2",
            padx=15,
            pady=5,
        )
        lbl.pack(side=LEFT)
        lbl.bind("<Button-1>", lambda e, n=t: update_ui(n))
        nav_labels[t] = lbl

    # Hero
    hero = tk.Frame(window, background=BG_COLOR, pady=30)
    hero.pack(fill=X)
    tk.Label(
        hero,
        textvariable=hero_val,
        font=("Segoe UI Variable Display", 72),
        foreground=TEXT_WHITE,
        background=BG_COLOR,
    ).pack()
    tk.Label(
        hero,
        text="TOTAL TRANSCRIPTIONS",
        font=("Segoe UI", 8, "bold"),
        foreground="#666666",
        background=BG_COLOR,
    ).pack()

    # Grid
    grid = tk.Frame(window, background=BG_COLOR, padx=60, pady=20)
    grid.pack(fill=X)
    grid.columnconfigure((0, 1, 2), weight=1)

    def add_col(col, var, label, color=TEXT_WHITE):
        f = tk.Frame(grid, background=BG_COLOR)
        f.grid(row=0, column=col, sticky="nsew")
        tk.Label(
            f, textvariable=var, font=("Segoe UI", 18, "bold"), foreground=color, background=BG_COLOR
        ).pack()
        tk.Label(
            f, text=label, font=("Segoe UI", 6, "bold"), foreground="#444444", background=BG_COLOR
        ).pack()

    add_col(0, dur_val, "DURATION")
    add_col(1, word_val, "WORDS")
    add_col(2, err_val, "ERRORS", color="#CC3333")

    # Provider Frame
    provider_frame = tk.Frame(window, background=BG_COLOR, padx=60, pady=40)
    provider_frame.pack(fill=X)
    tk.Label(
        provider_frame,
        text="SERVICE INTELLIGENCE",
        font=("Segoe UI", 7, "bold"),
        foreground="#555555",
        background=BG_COLOR,
    ).pack(anchor="w", pady=(0, 20))

    provider_container = tk.Frame(provider_frame, background=BG_COLOR)
    provider_container.pack(fill=X)

    # INIT
    update_ui("LIFETIME")

    window.deiconify()
    window.lift()
    window.focus_force()
