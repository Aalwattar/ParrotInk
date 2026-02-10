import sys
from typing import Optional

# Try importing tkinter for GUI prompts
try:
    import tkinter as tk
    from tkinter import simpledialog
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

def ask_key(provider_name: str) -> Optional[str]:
    """
    Prompts the user for an API key.
    Tries to use a GUI dialog (tkinter) first.
    Falls back to console input if tkinter is unavailable.
    """
    if HAS_TKINTER:
        return _ask_key_gui(provider_name)
    else:
        return _ask_key_console(provider_name)

def _ask_key_gui(provider_name: str) -> Optional[str]:
    """Shows a tkinter dialog to prompt for an API key."""
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Ensure dialog is on top
        root.attributes("-topmost", True)
        
        key = simpledialog.askstring(
            f"Set {provider_name} Key",
            f"Enter your {provider_name} API Key:",
            show="*",
            parent=root
        )
        
        root.destroy()
        return key
    except Exception as e:
        print(f"GUI Dialog failed ({e}). Falling back to console.")
        return _ask_key_console(provider_name)

def _ask_key_console(provider_name: str) -> Optional[str]:
    """Prompts for the key via standard input."""
    print(f"\n[!] GUI Tinker is not available -- enter it here.")
    print(f"Please enter your {provider_name} API Key:")
    try:
        # Use input() instead of getpass() to ensure it works in more environments
        # inside an IDE or captured stdout context, though getpass is more secure.
        # Given the instruction "enter or paste", input() is safer for compatibility.
        key = input(f"> ").strip()
        return key if key else None
    except (KeyboardInterrupt, EOFError):
        print("\nInput cancelled.")
        return None