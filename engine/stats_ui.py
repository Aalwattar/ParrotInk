from typing import Any, Dict

import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, DEFAULT, EW, INFO, LEFT, PRIMARY, RIGHT, SECONDARY, W, X


def show_stats_dialog(master, stats_report: Dict[str, Any]):
    """
    Displays an instant, modern dashboard using ttkbootstrap.
    Designed as a Toplevel child of the persistent GUI master.
    """
    # Create instant child window
    window = tb.Toplevel(
        master=master,
        title="ParrotInk Analytics",
        size=(520, 580),
        resizable=(False, False),
    )

    # Main container with padding
    main_frame = tb.Frame(window, padding=25)
    main_frame.pack(fill=BOTH, expand=True)

    # --- Header ---
    header_frame = tb.Frame(main_frame)
    header_frame.pack(fill=X, pady=(0, 20))

    tb.Label(
        header_frame,
        text="Usage Analytics",
        font=("Segoe UI Variable Display", 20, "bold"),
        bootstyle=DEFAULT,
    ).pack(side=LEFT)

    # --- Tabs ---
    notebook = tb.Notebook(main_frame, bootstyle=PRIMARY)
    notebook.pack(fill=BOTH, expand=True)

    def create_stat_tab(parent, data):
        tab = tb.Frame(parent, padding=20)

        # Hero Stat
        val = data.get("total_transcriptions", 0)
        hero_frame = tb.Frame(tab)
        hero_frame.pack(fill=X, pady=(10, 20))

        tb.Label(
            hero_frame,
            text=str(val),
            font=("Segoe UI Variable Display", 32, "bold"),
            bootstyle=PRIMARY,
        ).pack()
        tb.Label(
            hero_frame,
            text="TOTAL TRANSCRIPTIONS",
            font=("Segoe UI", 8, "bold"),
            bootstyle=SECONDARY,
        ).pack()

        # Secondary Stats
        metrics_frame = tb.Frame(tab)
        metrics_frame.pack(fill=X, pady=10)
        metrics_frame.columnconfigure((0, 1), weight=1)

        dur_sec = data.get("total_duration_seconds", 0)
        dur_min = round(dur_sec / 60, 1)
        dur_tile = tb.Frame(metrics_frame, bootstyle=SECONDARY, padding=10)
        dur_tile.grid(row=0, column=0, padx=(0, 5), sticky=EW)
        tb.Label(dur_tile, text=f"{dur_min}m", font=("Segoe UI", 14, "bold")).pack()
        tb.Label(dur_tile, text="DURATION", font=("Segoe UI", 7, "bold"), bootstyle=INFO).pack()

        words_tile = tb.Frame(metrics_frame, bootstyle=SECONDARY, padding=10)
        words_tile.grid(row=0, column=1, padx=(5, 0), sticky=EW)
        tb.Label(
            words_tile, text=str(data.get("total_words", 0)), font=("Segoe UI", 14, "bold")
        ).pack()
        tb.Label(words_tile, text="WORDS", font=("Segoe UI", 7, "bold"), bootstyle=INFO).pack()

        # Service Breakdown
        tb.Label(
            tab, text="SERVICE UTILIZATION", font=("Segoe UI", 8, "bold"), bootstyle=SECONDARY
        ).pack(anchor=W, pady=(25, 5))

        providers = data.get("provider_usage", {})
        if not providers:
            tb.Label(tab, text="No activity data yet.", font=("Segoe UI", 10), bootstyle=INFO).pack(
                pady=10
            )
        else:
            list_frame = tb.Frame(tab)
            list_frame.pack(fill=X)
            for p, count in providers.items():
                row = tb.Frame(list_frame)
                row.pack(fill=X, pady=2)
                tb.Label(row, text=p.title(), font=("Segoe UI", 11)).pack(side=LEFT)
                tb.Label(
                    row, text=str(count), font=("Segoe UI", 11, "bold"), bootstyle=PRIMARY
                ).pack(side=RIGHT)

        return tab

    notebook.add(create_stat_tab(notebook, stats_report.get("today", {})), text="Today")
    notebook.add(create_stat_tab(notebook, stats_report.get("this_week", {})), text="Weekly")
    notebook.add(create_stat_tab(notebook, stats_report.get("this_month", {})), text="Monthly")
    notebook.add(create_stat_tab(notebook, stats_report.get("lifetime", {})), text="Lifetime")

    # --- Footer ---
    footer = tb.Frame(main_frame)
    footer.pack(fill=X, pady=(20, 0))

    tb.Button(footer, text="Dismiss", command=window.destroy, bootstyle=SECONDARY, width=12).pack(
        side=RIGHT
    )

    # Bring to front and show
    window.deiconify()
    window.place_window_center()
    window.lift()
    window.focus_force()
