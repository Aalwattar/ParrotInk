"""Gateway settings dialog. Secrets are returned separately from TOML settings."""

import re
import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as tb

from engine.transcription.catalog import models_for_provider


def validate_gateway_settings(account_id: str, gateway_id: str, model: str) -> str | None:
    if not re.fullmatch(r"[a-fA-F0-9]{32}", account_id):
        return "Enter the 32-character Cloudflare account ID from your dashboard."
    if not re.fullmatch(r"[A-Za-z0-9_-]+", gateway_id):
        return "Enter a gateway ID using letters, numbers, hyphens, or underscores."
    if model not in {spec.id for spec in models_for_provider("cloudflare")}:
        return "Select a supported streaming transcription model."
    return None


def ask_cloudflare_settings(master, config) -> dict | None:
    core = config.providers.cloudflare.core
    window = tb.Toplevel(master=master)
    window.title("Cloudflare AI Gateway")
    window.resizable(False, False)
    # A transient child of the tray's withdrawn master also stays withdrawn
    # on Windows. Keep ownership through master without hiding the dialog.
    if master.winfo_viewable():
        window.transient(master)
    window.attributes("-topmost", True)
    content = tb.Frame(window, padding=24)
    content.pack(fill="both", expand=True)
    tb.Label(content, text="Cloudflare AI Gateway", font=("Segoe UI", 17, "bold")).grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(0, 16)
    )
    tb.Label(content, text="Route transcription through your Cloudflare gateway.").grid(
        row=1, column=0, columnspan=2, sticky="w", pady=(0, 12)
    )
    variables = {
        "account_id": tk.StringVar(master=window, value=core.account_id),
        "gateway_id": tk.StringVar(master=window, value=core.gateway_id),
        "model": tk.StringVar(master=window, value=core.model),
        "language": tk.StringVar(master=window, value=core.language),
        "api_token": tk.StringVar(master=window, value=""),
    }
    entries = []
    for row, (field, label) in enumerate(
        (
            ("account_id", "Account ID"),
            ("gateway_id", "Gateway ID"),
            ("model", "Transcription model"),
            ("language", "Language hint (optional)"),
            ("api_token", "API token"),
        ),
        start=2,
    ):
        tb.Label(content, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
        entry: tb.Entry | tb.Combobox
        if field == "model":
            entry = tb.Combobox(
                content,
                textvariable=variables[field],
                width=39,
                values=[s.id for s in models_for_provider("cloudflare")],
                state="readonly",
            )
        else:
            entry = tb.Entry(
                content,
                textvariable=variables[field],
                width=42,
                show="*" if field == "api_token" else "",
            )
        entry.grid(row=row, column=1, sticky="ew", pady=6)
        entries.append(entry)
    tb.Label(
        content,
        text="Leave the token blank to keep the saved credential.\n"
        "Tokens are stored in Windows Credential Manager.",
        wraplength=475,
    ).grid(row=7, column=0, columnspan=2, sticky="w", pady=(4, 10))
    tb.Label(
        content,
        text="Cloudflare models use only your Cloudflare token.\n"
        "Nova-3 and Flux need AI Gateway Run permission.\n"
        "Grok also needs Account > Workers AI > Read token permission.",
        wraplength=475,
    ).grid(row=9, column=0, columnspan=2, sticky="w", pady=(0, 12))
    result = [None]

    def save():
        values = {name: variable.get().strip() for name, variable in variables.items()}
        error = validate_gateway_settings(
            values["account_id"], values["gateway_id"], values["model"]
        )
        if error:
            messagebox.showerror("Gateway settings", error, parent=window)
            return
        result[0] = {
            "core": {
                "account_id": values["account_id"],
                "gateway_id": values["gateway_id"],
                "model": values["model"],
                "language": values["language"],
            },
            "api_token": values["api_token"] or None,
        }
        window.destroy()

    buttons = tb.Frame(content)
    buttons.grid(row=10, column=0, columnspan=2, sticky="e")
    tb.Button(buttons, text="Cancel", command=window.destroy, bootstyle="secondary").pack(
        side="left", padx=(0, 8)
    )
    tb.Button(buttons, text="Save", command=save).pack(side="left")
    window.bind("<Escape>", lambda event: window.destroy())
    window.bind("<Return>", lambda event: save())
    window.update_idletasks()
    window.geometry(
        f"+{(window.winfo_screenwidth() - window.winfo_width()) // 2}"
        f"+{(window.winfo_screenheight() - window.winfo_height()) // 2}"
    )
    window.deiconify()
    window.lift()
    window.focus_force()
    entries[0].focus_set()
    # The tray has no main window that needs a modal input grab. Waiting for
    # this dialog to close is enough, and leaves desktop mouse input untouched.
    try:
        if not window.winfo_viewable():
            window.wait_visibility()
        window.wait_window()
    finally:
        try:
            if window.winfo_exists():
                window.destroy()
        except tk.TclError:
            pass
    return result[0]
