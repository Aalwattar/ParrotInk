"""Read editor identity and bounds through Windows UI Automation."""

import ctypes
import uuid
from ctypes import wintypes
from dataclasses import dataclass

from engine.logging import get_logger

logger = get_logger("EditorFocus")

_ole32 = ctypes.WinDLL("ole32")
_ole32.CoInitializeEx.argtypes = [ctypes.c_void_p, wintypes.DWORD]
_ole32.CoInitializeEx.restype = ctypes.c_long
_ole32.CoUninitialize.argtypes = []
_ole32.CoCreateInstance.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_void_p),
]
_ole32.CoCreateInstance.restype = ctypes.c_long
_oleaut32 = ctypes.WinDLL("oleaut32")
_oleaut32.SafeArrayGetLBound.argtypes = [
    ctypes.c_void_p,
    wintypes.UINT,
    ctypes.POINTER(ctypes.c_long),
]
_oleaut32.SafeArrayGetUBound.argtypes = _oleaut32.SafeArrayGetLBound.argtypes
_oleaut32.SafeArrayGetElement.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_long),
    ctypes.c_void_p,
]
_oleaut32.SafeArrayDestroy.argtypes = [ctypes.c_void_p]
for _name in (
    "SafeArrayGetLBound",
    "SafeArrayGetUBound",
    "SafeArrayGetElement",
    "SafeArrayDestroy",
):
    getattr(_oleaut32, _name).restype = ctypes.c_long

_CLSID = (ctypes.c_ubyte * 16).from_buffer_copy(
    uuid.UUID("ff48dba4-60ef-4201-aa87-54103eef594e").bytes_le
)
_IID = (ctypes.c_ubyte * 16).from_buffer_copy(
    uuid.UUID("30cbe57d-d9d0-452a-ab13-7ac5ac4825ee").bytes_le
)


@dataclass(frozen=True)
class FocusedElement:
    runtime_id: tuple[int, ...]
    control_type: int
    bounds: tuple[int, int, int, int]


# Slots and signatures are from the Windows SDK's UIAutomationClient.h.
def _call(pointer, slot, argtypes, *args):
    table = ctypes.cast(pointer, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
    fn = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, *argtypes)(table[slot])
    result = fn(pointer, *args)
    if result < 0:
        raise OSError(f"UI Automation call failed ({result})")
    return result


def read_focused_element() -> FocusedElement | None:
    automation, element, runtime = ctypes.c_void_p(), ctypes.c_void_p(), ctypes.c_void_p()
    initialized = _ole32.CoInitializeEx(None, 0)
    if initialized < 0 and initialized != -2147417850:  # Already initialized as STA.
        return None
    try:
        result = _ole32.CoCreateInstance(_CLSID, None, 1, _IID, ctypes.byref(automation))
        if result < 0:
            raise OSError(f"UI Automation initialization failed ({result})")
        _call(automation, 8, [ctypes.POINTER(ctypes.c_void_p)], ctypes.byref(element))
        if not element:
            return None
        kind = ctypes.c_int()
        rect = wintypes.RECT()
        _call(element, 21, [ctypes.POINTER(ctypes.c_int)], ctypes.byref(kind))
        _call(element, 43, [ctypes.POINTER(wintypes.RECT)], ctypes.byref(rect))
        _call(element, 4, [ctypes.POINTER(ctypes.c_void_p)], ctypes.byref(runtime))
        if not runtime:
            return None
        lower, upper = ctypes.c_long(), ctypes.c_long()
        if _oleaut32.SafeArrayGetLBound(runtime, 1, ctypes.byref(lower)) < 0:
            return None
        if _oleaut32.SafeArrayGetUBound(runtime, 1, ctypes.byref(upper)) < 0:
            return None
        if not 0 <= upper.value - lower.value < 128:
            return None
        identity = []
        for index in range(lower.value, upper.value + 1):
            value, position = ctypes.c_int(), ctypes.c_long(index)
            if (
                _oleaut32.SafeArrayGetElement(runtime, ctypes.byref(position), ctypes.byref(value))
                < 0
            ):
                return None
            identity.append(value.value)
        return FocusedElement(
            tuple(identity), kind.value, (rect.left, rect.top, rect.right, rect.bottom)
        )
    except OSError:
        logger.debug("Editor accessibility unavailable; retaining native control detection")
        return None
    finally:
        if runtime:
            _oleaut32.SafeArrayDestroy(runtime)
        if element:
            _call(element, 2, [])
        if automation:
            _call(automation, 2, [])
        if initialized >= 0:
            _ole32.CoUninitialize()
