"""Read editor identity and bounds through Windows UI Automation."""

import ctypes
import uuid
from ctypes import wintypes
from dataclasses import dataclass

from engine.logging import get_logger
from engine.platform_win.dpi import physical_coordinates

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
_oleaut32.VariantClear.argtypes = [ctypes.c_void_p]
_oleaut32.VariantClear.restype = ctypes.c_long
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
_VALUE_IID = (ctypes.c_ubyte * 16).from_buffer_copy(
    uuid.UUID("a94cd8b1-0844-4cd6-9d2d-640537ab39e9").bytes_le
)
_TEXT_IID = (ctypes.c_ubyte * 16).from_buffer_copy(
    uuid.UUID("32eba289-3583-42c9-9c59-3b6d9a1e9b6a").bytes_le
)


@dataclass(frozen=True)
class FocusedElement:
    runtime_id: tuple[int, ...]
    control_type: int
    bounds: tuple[int, int, int, int]
    enabled: bool = True
    password: bool = False
    read_only: bool | None = None

    @property
    def can_dictate(self) -> bool:
        left, top, right, bottom = self.bounds
        return (
            self.control_type in (50003, 50004, 50025, 50029, 50030)
            and self.enabled
            and not self.password
            # Some editable controls omit ValuePattern; their Edit type is still useful.
            and (self.read_only is False or (self.control_type == 50004 and self.read_only is None))
            and right > left
            and bottom > top
        )


class _VariantData(ctypes.Union):
    _fields_ = [
        ("boolean", ctypes.c_short),
        ("record", ctypes.c_void_p * 2),
        ("integer", ctypes.c_longlong),
    ]


class _Variant(ctypes.Structure):
    _fields_ = [("vt", ctypes.c_ushort), ("reserved", ctypes.c_ushort * 3), ("data", _VariantData)]


# Slots and signatures are from the Windows SDK's UIAutomationClient.h.
def _call(pointer, slot, argtypes, *args):
    table = ctypes.cast(pointer, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
    fn = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, *argtypes)(table[slot])
    result = fn(pointer, *args)
    if result < 0:
        raise OSError(f"UI Automation call failed ({result})")
    return result


def _read_only(element) -> bool | None:
    pattern, selection, text_range = ctypes.c_void_p(), ctypes.c_void_p(), ctypes.c_void_p()
    value = _Variant()
    try:
        try:
            _call(
                element,
                14,
                [ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)],
                10002,
                _VALUE_IID,
                ctypes.byref(pattern),
            )  # ValuePattern.
        except OSError:
            pattern = ctypes.c_void_p()
        if pattern:
            read_only = wintypes.BOOL()
            _call(pattern, 5, [ctypes.POINTER(wintypes.BOOL)], ctypes.byref(read_only))
            return bool(read_only.value)
        _call(
            element,
            14,
            [ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)],
            10014,
            _TEXT_IID,
            ctypes.byref(pattern),
        )  # TextPattern for rich/multiline editors.
        if not pattern:
            return None
        _call(pattern, 5, [ctypes.POINTER(ctypes.c_void_p)], ctypes.byref(selection))
        if not selection:
            return None
        length = ctypes.c_int()
        _call(selection, 3, [ctypes.POINTER(ctypes.c_int)], ctypes.byref(length))
        if length.value != 1:
            return None
        _call(
            selection,
            4,
            [ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)],
            0,
            ctypes.byref(text_range),
        )
        if not text_range:
            return None
        _call(
            text_range, 9, [ctypes.c_int, ctypes.POINTER(_Variant)], 40015, ctypes.byref(value)
        )  # IsReadOnly text attribute; no text is read.
        return bool(value.data.boolean) if value.vt == 11 else None  # VT_BOOL.
    except OSError:
        return None
    finally:
        _oleaut32.VariantClear(ctypes.byref(value))
        if text_range:
            _call(text_range, 2, [])
        if selection:
            _call(selection, 2, [])
        if pattern:
            _call(pattern, 2, [])


def _focused_descendant(automation, element):
    """WebView2 can report its host pane while an inner editor owns focus."""
    condition, focused = ctypes.c_void_p(), ctypes.c_void_p()
    value = _Variant()
    value.vt, value.data.boolean = 11, -1  # VT_BOOL, VARIANT_TRUE.
    try:
        _call(
            automation,
            23,
            [ctypes.c_int, _Variant, ctypes.POINTER(ctypes.c_void_p)],
            30008,
            value,
            ctypes.byref(condition),  # HasKeyboardFocus.
        )
        if not condition:
            return None
        _call(
            element,
            5,
            [ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)],
            4,
            condition,
            ctypes.byref(focused),  # FindFirst, TreeScope_Descendants.
        )
        return focused
    except OSError:
        if focused:
            _call(focused, 2, [])
        return None
    finally:
        if condition:
            _call(condition, 2, [])


def _excel_editor(automation, element):
    """Resolve Excel's native in-cell pane through its accessibility provider."""
    value = _Variant()
    walker, parent = ctypes.c_void_p(), ctypes.c_void_p()
    try:
        _call(element, 10, [ctypes.c_int, ctypes.POINTER(_Variant)], 30012, ctypes.byref(value))
        # shortcut: EXCEL6 only; extend after verifying another native editor's provider bridge.
        if value.vt != 8 or not value.data.record[0]:
            return None
        if ctypes.wstring_at(value.data.record[0]) != "EXCEL6":
            return None
        _call(automation, 14, [ctypes.POINTER(ctypes.c_void_p)], ctypes.byref(walker))
        if not walker:
            return None
        _call(
            walker,
            3,
            [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)],
            element,
            ctypes.byref(parent),
        )
        if not parent:
            return None
        _oleaut32.VariantClear(ctypes.byref(value))
        _call(parent, 10, [ctypes.c_int, ctypes.POINTER(_Variant)], 30012, ctypes.byref(value))
        if value.vt != 8 or not value.data.record[0]:
            return None
        if ctypes.wstring_at(value.data.record[0]) != "XLDESK":
            return None
        return _focused_descendant(automation, parent)
    except OSError:
        return None
    finally:
        _oleaut32.VariantClear(ctypes.byref(value))
        if parent:
            _call(parent, 2, [])
        if walker:
            _call(walker, 2, [])


def _search_box(automation, element, kind):
    """Resolve a selected suggestion to the writable box that controls its list."""
    references = []
    value = _Variant()

    def related(walker, slot, source):
        result = ctypes.c_void_p()
        _call(
            walker,
            slot,
            [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)],
            source,
            ctypes.byref(result),
        )
        if result:
            references.append(result)
        return result

    try:
        walker = ctypes.c_void_p()
        _call(automation, 14, [ctypes.POINTER(ctypes.c_void_p)], ctypes.byref(walker))
        if not walker:
            return None
        references.append(walker)
        listing = related(walker, 3, element) if kind == 50007 else element
        if not listing:
            return None
        list_kind = ctypes.c_int()
        _call(listing, 21, [ctypes.POINTER(ctypes.c_int)], ctypes.byref(list_kind))
        if list_kind.value != 50008:
            return None
        # shortcut: adjacent linked search boxes only; broaden for a verified alternate layout.
        candidate = related(walker, 7, listing)
        if not candidate:
            return None
        candidate_kind = ctypes.c_int()
        _call(candidate, 21, [ctypes.POINTER(ctypes.c_int)], ctypes.byref(candidate_kind))
        if candidate_kind.value not in (50003, 50004) or _read_only(candidate) is not False:
            return None
        _call(candidate, 10, [ctypes.c_int, ctypes.POINTER(_Variant)], 30104, ctypes.byref(value))
        if value.vt != 13 or not value.data.record[0]:  # ControllerFor element array.
            return None
        controlled = ctypes.c_void_p(value.data.record[0])
        length = ctypes.c_int()
        _call(controlled, 3, [ctypes.POINTER(ctypes.c_int)], ctypes.byref(length))
        for index in range(min(length.value, 16)):
            item = ctypes.c_void_p()
            _call(
                controlled,
                4,
                [ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)],
                index,
                ctypes.byref(item),
            )
            if not item:
                continue
            same = wintypes.BOOL()
            try:
                _call(
                    automation,
                    3,
                    [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(wintypes.BOOL)],
                    item,
                    listing,
                    ctypes.byref(same),
                )
            finally:
                _call(item, 2, [])
            if same.value:
                references.remove(candidate)
                return candidate
        return None
    except OSError:
        return None
    finally:
        _oleaut32.VariantClear(ctypes.byref(value))
        for reference in reversed(references):
            _call(reference, 2, [])


@physical_coordinates()
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
        if kind.value == 50033:
            focused = _focused_descendant(automation, element)
            if not focused:
                focused = _excel_editor(automation, element)
            if focused:
                _call(element, 2, [])
                element = focused
                _call(element, 21, [ctypes.POINTER(ctypes.c_int)], ctypes.byref(kind))
        if kind.value in (50007, 50008):
            search = _search_box(automation, element, kind.value)
            if search:
                _call(element, 2, [])
                element = search
                _call(element, 21, [ctypes.POINTER(ctypes.c_int)], ctypes.byref(kind))
        _call(element, 43, [ctypes.POINTER(wintypes.RECT)], ctypes.byref(rect))
        enabled, password = wintypes.BOOL(), wintypes.BOOL()
        _call(element, 28, [ctypes.POINTER(wintypes.BOOL)], ctypes.byref(enabled))
        _call(element, 35, [ctypes.POINTER(wintypes.BOOL)], ctypes.byref(password))
        read_only = _read_only(element) if enabled.value and not password.value else None
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
            tuple(identity),
            kind.value,
            (rect.left, rect.top, rect.right, rect.bottom),
            bool(enabled.value),
            bool(password.value),
            read_only,
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
