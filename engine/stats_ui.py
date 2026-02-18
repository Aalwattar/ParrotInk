from typing import Any, Dict

import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, INFO, LEFT, PRIMARY, RIGHT, SECONDARY, W, X


def show_stats_dialog(master, stats_report: Dict[str, Any]):
    """
    Displays an instant, modern dashboard using ttkbootstrap.
    Designed as a Toplevel child of the persistent GUI master.
    """
    # Create instant child window
    window = tb.Toplevel(
        master=master,
        title="ParrotInk Analytics",
        size=(520, 600),
        resizable=(False, False),
    )

    # Main container with generous padding for luxury feel
    main_frame = tb.Frame(window, padding=35)
    main_frame.pack(fill=BOTH, expand=True)

    # --- Header ---
    header_frame = tb.Frame(main_frame)
    header_frame.pack(fill=X, pady=(0, 30))

    tb.Label(
        header_frame,
        text="Usage Analytics",
        font=("Segoe UI Variable Display", 22, "bold"),
    ).pack(side=LEFT)

    # --- Tabs ---
    # Notebook is styled via the global theme, but we ensure content is clean
    notebook = tb.Notebook(main_frame, bootstyle=PRIMARY)
    notebook.pack(fill=BOTH, expand=True)

    def create_stat_tab(parent, data):
        tab = tb.Frame(parent, padding=25)

        # Hero Stat - Large, clean numbers without boxes
        val = data.get("total_transcriptions", 0)
        hero_frame = tb.Frame(tab)
        hero_frame.pack(fill=X, pady=(10, 30))

        tb.Label(
            hero_frame,
            text=str(val),
            font=("Segoe UI Variable Display", 42, "bold"),
            foreground="white",
        ).pack()
        tb.Label(
            hero_frame,
            text="TOTAL TRANSCRIPTIONS",
            font=("Segoe UI Variable Text", 9, "bold"),
            bootstyle=SECONDARY,
        ).pack()

        # Secondary Stats - Clean alignment, no distracting tiles
        metrics_frame = tb.Frame(tab)
        metrics_frame.pack(fill=X, pady=10)
        metrics_frame.columnconfigure((0, 1), weight=1)

        dur_sec = data.get("total_duration_seconds", 0)
        dur_min = round(dur_sec / 60, 1)

        # Duration Column
        dur_col = tb.Frame(metrics_frame)
        dur_col.grid(row=0, column=0, sticky=W)
        tb.Label(dur_col, text=f"{dur_min}m", font=("Segoe UI Variable Display", 18, "bold")).pack(
            anchor=W
        )
        tb.Label(dur_col, text="DURATION", font=("Segoe UI", 8, "bold"), bootstyle=INFO).pack(
            anchor=W
        )

        # Words Column
        words_col = tb.Frame(metrics_frame)
        words_col.grid(row=0, column=1, sticky=W)
        tb.Label(
            words_col,
            text=str(data.get("total_words", 0)),
            font=("Segoe UI Variable Display", 18, "bold"),
        ).pack(anchor=W)
        tb.Label(words_col, text="WORDS", font=("Segoe UI", 8, "bold"), bootstyle=INFO).pack(
            anchor=W
        )

        # Service Breakdown - Minimalist list
        tb.Label(
            tab,
            text="SERVICE UTILIZATION",
            font=("Segoe UI Variable Text", 8, "bold"),
            bootstyle=SECONDARY,
        ).pack(anchor=W, pady=(35, 10))

        providers = data.get("provider_usage", {})
        if not providers:
            tb.Label(tab, text="No activity data yet.", font=("Segoe UI", 10), bootstyle=INFO).pack(
                anchor=W, pady=5
            )
        else:
            list_frame = tb.Frame(tab)
            list_frame.pack(fill=X)
            for p, count in providers.items():
                row = tb.Frame(list_frame)
                row.pack(fill=X, pady=4)
                tb.Label(row, text=p.title(), font=("Segoe UI", 11)).pack(side=LEFT)
                tb.Label(
                    row, text=str(count), font=("Segoe UI", 11, "bold"), foreground="#CCCCCC"
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
