import tkinter as tk
from tkinter import ttk
from typing import Any, Dict


def show_stats_dialog(stats_report: Dict[str, Any]):
    """
    Displays a modern Tkinter dialog with the usage statistics.
    """
    root = tk.Tk()
    root.title("ParrotInk - Usage Statistics")
    root.geometry("500x450")
    root.resizable(False, False)

    # Styling
    style = ttk.Style()
    style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
    style.configure("Stat.TLabel", font=("Segoe UI", 10))
    style.configure("Value.TLabel", font=("Segoe UI", 10, "bold"))

    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)

    header = ttk.Label(main_frame, text="Usage Statistics Report", style="Header.TLabel")
    header.pack(pady=(0, 20))

    # Notebook for Tabs
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill=tk.BOTH, expand=True)

    def create_stat_tab(parent, data):
        frame = ttk.Frame(parent, padding="15")

        def add_row(label, value, row):
            ttk.Label(frame, text=label, style="Stat.TLabel").grid(
                row=row, column=0, sticky="w", pady=5
            )
            ttk.Label(frame, text=str(value), style="Value.TLabel").grid(
                row=row, column=1, sticky="e", pady=5
            )

        add_row("Total Transcriptions:", data.get("total_transcriptions", 0), 0)

        duration_sec = data.get("total_duration_seconds", 0)
        duration_min = round(duration_sec / 60, 1)
        add_row("Total Duration (min):", f"{duration_min}m", 1)

        add_row("Total Words:", data.get("total_words", 0), 2)
        add_row("Error Count:", data.get("error_count", 0), 3)

        # Provider Breakdown
        providers = data.get("provider_usage", {})
        if providers:
            ttk.Separator(frame, orient="horizontal").grid(
                row=4, column=0, columnspan=2, sticky="ew", pady=10
            )
            row = 5
            for p, count in providers.items():
                add_row(f"Provider - {p.title()}:", count, row)
                row += 1

        frame.columnconfigure(1, weight=1)
        return frame

    # Add Tabs
    notebook.add(create_stat_tab(notebook, stats_report.get("today", {})), text="Today")
    notebook.add(create_stat_tab(notebook, stats_report.get("this_week", {})), text="This Week")
    notebook.add(create_stat_tab(notebook, stats_report.get("this_month", {})), text="This Month")
    notebook.add(create_stat_tab(notebook, stats_report.get("lifetime", {})), text="Lifetime")

    # Close Button
    btn_close = ttk.Button(main_frame, text="Close", command=root.destroy)
    btn_close.pack(pady=(20, 0))

    # Center the window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    # Bring to front
    root.lift()
    root.attributes("-topmost", True)
    root.after_idle(root.attributes, "-topmost", False)

    root.mainloop()


if __name__ == "__main__":
    # Test stub
    sample_data = {
        "today": {
            "total_transcriptions": 5,
            "total_duration_seconds": 300,
            "total_words": 250,
            "error_count": 0,
            "provider_usage": {"openai": 5},
        },
        "this_week": {
            "total_transcriptions": 25,
            "total_duration_seconds": 1500,
            "total_words": 1250,
            "error_count": 1,
            "provider_usage": {"openai": 25},
        },
        "this_month": {
            "total_transcriptions": 100,
            "total_duration_seconds": 6000,
            "total_words": 5000,
            "error_count": 2,
            "provider_usage": {"openai": 80, "assemblyai": 20},
        },
        "lifetime": {
            "total_transcriptions": 500,
            "total_duration_seconds": 30000,
            "total_words": 25000,
            "error_count": 5,
            "provider_usage": {"openai": 400, "assemblyai": 100},
        },
    }
    show_stats_dialog(sample_data)
