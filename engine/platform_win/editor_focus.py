"""Read editor identity and bounds through Windows UI Automation."""

import ctypes
import uuid
from ctypes import wintypes
from dataclasses import dataclass
from typing import Literal

from engine.logging import get_logger
from engine.platform_win.dpi import physical_coordinates
from engine.platform_win.window_focus import native_focus, owns_window, user32, window_from_point

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
    uuid.UUID("e22ad333-b25f-460c-83d0-0581107395c9").bytes_le
)
_IID = (ctypes.c_ubyte * 16).from_buffer_copy(
    uuid.UUID("34723aff-0c9d-49d0-9896-7ab52df8cd8a").bytes_le
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
    text_edit: bool = False

    @property
    def can_dictate(self) -> bool:
        return assess_target(self).decision == "editable"


@dataclass(frozen=True)
class TargetAssessment:
    decision: Literal["editable", "not_editable", "unknown"]
    reason: str


def assess_target(target: FocusedElement | None) -> TargetAssessment:
    if target is None or not target.runtime_id:
        return TargetAssessment("unknown", "focus_unresolved")
    if not target.enabled:
        return TargetAssessment("not_editable", "disabled")
    if target.password:
        return TargetAssessment("not_editable", "password")
    if target.read_only is True:
        return TargetAssessment("not_editable", "read_only")
    left, top, right, bottom = target.bounds
    if right <= left or bottom <= top:
        return TargetAssessment("unknown", "invalid_bounds")
    # Standard text roles have documented editing contracts; custom roles need TextEdit evidence.
    if target.control_type not in (50003, 50004, 50029, 50030) and not target.text_edit:
        return TargetAssessment("unknown", "text_input_unverified")
    if target.read_only is not False:
        return TargetAssessment("unknown", "writability_unavailable")
    return TargetAssessment("editable", "writable_text_target")


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
    value_read_only = None
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
            value_read_only = bool(read_only.value)
            _call(pattern, 2, [])
            pattern = ctypes.c_void_p()
            if value_read_only:
                return True
        if _bool_property(element, 30040) is False:  # IsTextPatternAvailable.
            return value_read_only
        _call(
            element,
            14,
            [ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)],
            10014,
            _TEXT_IID,
            ctypes.byref(pattern),
        )  # TextPattern for rich/multiline editors.
        if not pattern:
            return value_read_only
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


def _bool_property(element, property_id) -> bool | None:
    value = _Variant()
    try:
        _call(
            element, 10, [ctypes.c_int, ctypes.POINTER(_Variant)], property_id, ctypes.byref(value)
        )
        return bool(value.data.boolean) if value.vt == 11 else None
    except OSError:
        return None
    finally:
        _oleaut32.VariantClear(ctypes.byref(value))


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


def _read_element(element) -> FocusedElement:
    kind, enabled, password = ctypes.c_int(), wintypes.BOOL(), wintypes.BOOL()
    rect, runtime = wintypes.RECT(), ctypes.c_void_p()
    _call(element, 21, [ctypes.POINTER(ctypes.c_int)], ctypes.byref(kind))
    _call(element, 43, [ctypes.POINTER(wintypes.RECT)], ctypes.byref(rect))
    _call(element, 28, [ctypes.POINTER(wintypes.BOOL)], ctypes.byref(enabled))
    _call(element, 35, [ctypes.POINTER(wintypes.BOOL)], ctypes.byref(password))
    read_only = _read_only(element) if enabled.value and not password.value else None
    text_edit = _bool_property(element, 30149) is True  # IsTextEditPatternAvailable.
    try:
        _call(element, 4, [ctypes.POINTER(ctypes.c_void_p)], ctypes.byref(runtime))
        if not runtime:
            raise OSError("missing_runtime_id")
        lower, upper = ctypes.c_long(), ctypes.c_long()
        if _oleaut32.SafeArrayGetLBound(runtime, 1, ctypes.byref(lower)) < 0:
            raise OSError("invalid_runtime_id")
        if _oleaut32.SafeArrayGetUBound(runtime, 1, ctypes.byref(upper)) < 0:
            raise OSError("invalid_runtime_id")
        if not 0 <= upper.value - lower.value < 128:
            raise OSError("invalid_runtime_id")
        identity = []
        for index in range(lower.value, upper.value + 1):
            value, position = ctypes.c_int(), ctypes.c_long(index)
            if (
                _oleaut32.SafeArrayGetElement(runtime, ctypes.byref(position), ctypes.byref(value))
                < 0
            ):
                raise OSError("invalid_runtime_id")
            identity.append(value.value)
        return FocusedElement(
            tuple(identity),
            kind.value,
            (rect.left, rect.top, rect.right, rect.bottom),
            bool(enabled.value),
            bool(password.value),
            read_only,
            text_edit,
        )
    finally:
        if runtime:
            _oleaut32.SafeArrayDestroy(runtime)


def _choose_target(candidates):
    # Unsupported native hosts can share focus with their provider-backed editor.
    fields = [
        item
        for item in candidates
        if item[1].control_type not in (50032, 50033)
        or item[1].read_only is not None
        or item[1].text_edit
        or not item[1].enabled
        or item[1].password
    ]
    pool = fields or candidates
    unique = {item[1].runtime_id: item for item in pool}
    return next(iter(unique.values())) if len(unique) == 1 else None


def _resolve_target(automation, snapshot):
    references, candidates = [], []

    def result(pointer, slot, types, *args):
        output = ctypes.c_void_p()
        try:
            _call(
                pointer,
                slot,
                [*types, ctypes.POINTER(ctypes.c_void_p)],
                *args,
                ctypes.byref(output),
            )
        finally:
            if output:
                references.append(output)
        return output

    def inspect(scope):
        if not scope:
            return None
        elements = [scope]
        # Do not search an entire top-level window to recover a missing input host.
        handle = wintypes.HWND()
        _call(scope, 36, [ctypes.POINTER(wintypes.HWND)], ctypes.byref(handle))
        if handle.value != snapshot[0]:
            array = result(scope, 6, [ctypes.c_int, ctypes.c_void_p], 4, condition)
            if array:
                count = ctypes.c_int()
                _call(array, 3, [ctypes.POINTER(ctypes.c_int)], ctypes.byref(count))
                if not 0 <= count.value <= 8:
                    raise OSError("too_many_focus_candidates")
                elements.extend(
                    result(array, 4, [ctypes.c_int], index) for index in range(count.value)
                )
        for element in elements:
            if not element:
                continue
            focus = wintypes.BOOL()
            _call(element, 26, [ctypes.POINTER(wintypes.BOOL)], ctypes.byref(focus))
            if not focus.value:
                continue
            target = _read_element(element)
            native = wintypes.HWND()
            _call(element, 36, [ctypes.POINTER(wintypes.HWND)], ctypes.byref(native))
            left, top, right, bottom = target.bounds
            hit = window_from_point((left + right) // 2, (top + bottom) // 2)
            if owns_window(snapshot[1], native.value) or owns_window(snapshot[1], hit):
                candidates.append((element, target))
        return _choose_target(candidates)

    try:
        value = _Variant()
        value.vt, value.data.boolean = 11, -1
        condition = result(automation, 23, [ctypes.c_int, _Variant], 30008, value)
        if not condition:
            return None
        focused = result(automation, 8, [])
        selected = inspect(focused)
        if selected is None or selected[1].read_only is None:
            native = result(automation, 6, [wintypes.HWND], snapshot[1])
            selected = inspect(native)
            if (selected is None or selected[1].read_only is None) and native:
                walker = result(automation, 14, [])
                parent = result(walker, 3, [ctypes.c_void_p], native) if walker else None
                if parent:
                    handle = wintypes.HWND()
                    _call(parent, 36, [ctypes.POINTER(wintypes.HWND)], ctypes.byref(handle))
                    if handle.value and user32.IsChild(snapshot[0], handle.value):
                        selected = inspect(parent)
        if selected is None:
            return None
        element, target = selected
        if target.control_type in (50007, 50008):
            linked = _search_box(automation, element, target.control_type)
            if linked:
                references.append(linked)
                target = _read_element(linked)
        return target
    finally:
        for reference in reversed(references):
            _call(reference, 2, [])


@physical_coordinates()
def read_focused_element() -> FocusedElement | None:
    automation = ctypes.c_void_p()
    initialized = _ole32.CoInitializeEx(None, 0)
    if initialized < 0 and initialized != -2147417850:
        return None
    try:
        result = _ole32.CoCreateInstance(_CLSID, None, 1, _IID, ctypes.byref(automation))
        if result < 0 or not automation:
            return None
        _call(automation, 61, [wintypes.DWORD], 500)  # IUIAutomation2 connection timeout.
        _call(automation, 63, [wintypes.DWORD], 500)  # IUIAutomation2 transaction timeout.
        for _ in range(2):
            before = native_focus()
            if not all(before):
                return None
            target = _resolve_target(automation, before)
            if before == native_focus():
                return target
        logger.debug("Editor assessment unavailable: focus_changed")
    except OSError:
        logger.debug("Editor assessment unavailable: provider_failure", exc_info=True)
    finally:
        if automation:
            _call(automation, 2, [])
        if initialized >= 0:
            _ole32.CoUninitialize()
    return None
