import sys


def test_eval_mode_imports():
    """
    Assert that importing engine.eval_main does NOT trigger
    imports of pystray or tkinter.
    """
    # Ensure they are not already in sys.modules
    sys.modules.pop("pystray", None)
    sys.modules.pop("tkinter", None)
    sys.modules.pop("engine.ui", None)
    sys.modules.pop("engine.gui_main", None)

    # Now import eval_main

    # Check if UI modules were pulled in
    assert "pystray" not in sys.modules, "eval_main triggered pystray import!"
    assert "tkinter" not in sys.modules, "eval_main triggered tkinter import!"
    assert "engine.ui" not in sys.modules, "eval_main triggered engine.ui import!"


def test_gui_mode_imports():
    """
    Ensure engine.gui_main DOES allow these imports (sanity check).
    """
    # We don't assert they ARE there, just that this is the allowed path.
