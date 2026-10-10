"""Use physical pixels for native input/accessibility without changing UI scaling."""

import ctypes
from contextlib import contextmanager

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_set_context = _user32.SetThreadDpiAwarenessContext
_set_context.argtypes = [ctypes.c_void_p]
_set_context.restype = ctypes.c_void_p


@contextmanager
def physical_coordinates():
    previous = _set_context(ctypes.c_void_p(-4))  # Per-monitor aware v2.
    if not previous:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        yield
    finally:
        _set_context(previous)
