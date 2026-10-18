"""THROWAWAY: test native ownership of focused UIA targets, without reading text.

Run: python -m engine.platform_win.editor_focus_prototype --watch 45
Self-check: python -m engine.platform_win.editor_focus_prototype --self-test
No application names, class names, text values, input, or production imports use this probe.
"""

import argparse
import ctypes
import json
import time
from ctypes import wintypes

from engine.anchor import GUITHREADINFO, get_foreground_window, user32, window_from_point
from engine.platform_win import editor_focus as uia
from engine.platform_win.dpi import physical_coordinates

user32.IsChild.argtypes = [wintypes.HWND, wintypes.HWND]
user32.IsChild.restype = wintypes.BOOL


def choose(candidates):
    supported = [item for item in candidates if item.get("read_only") is not None]
    if any(item["focus"] and item["owned"] for item in supported):
        candidates = supported
    owned = {
        tuple(item["identity"]): item
        for item in candidates
        if item["identity"] and item["focus"] and item["owned"]
    }
    return next(iter(owned.values())) if len(owned) == 1 else None


def native_focus():
    info = GUITHREADINFO()
    info.cbSize = ctypes.sizeof(info)
    return (
        (get_foreground_window(), info.hwndFocus)
        if user32.GetGUIThreadInfo(0, ctypes.byref(info))
        else (0, 0)
    )


@physical_coordinates()
def probe():
    before = native_focus()
    if not all(before):
        return {"decision": "unknown", "reason": "native_focus_unavailable"}
    automation, condition, walker = ctypes.c_void_p(), ctypes.c_void_p(), ctypes.c_void_p()
    references, candidates = [], []
    initialized = uia._ole32.CoInitializeEx(None, 0)
    if initialized < 0:
        return {"decision": "unknown", "reason": "com_unavailable"}

    def result(pointer, slot, types, *args):
        output = ctypes.c_void_p()
        uia._call(
            pointer, slot, [*types, ctypes.POINTER(ctypes.c_void_p)], *args, ctypes.byref(output)
        )
        if output:
            references.append(output)
        return output

    def metadata(element):
        kind, focus, native = ctypes.c_int(), wintypes.BOOL(), wintypes.HWND()
        rect = wintypes.RECT()
        uia._call(element, 21, [ctypes.POINTER(ctypes.c_int)], ctypes.byref(kind))
        uia._call(element, 26, [ctypes.POINTER(wintypes.BOOL)], ctypes.byref(focus))
        uia._call(element, 36, [ctypes.POINTER(wintypes.HWND)], ctypes.byref(native))
        uia._call(element, 43, [ctypes.POINTER(wintypes.RECT)], ctypes.byref(rect))
        identity_array = result(element, 4, [])
        identity = []
        if identity_array:
            references.remove(identity_array)
            try:
                lower, upper = ctypes.c_long(), ctypes.c_long()
                assert uia._oleaut32.SafeArrayGetLBound(identity_array, 1, ctypes.byref(lower)) >= 0
                assert uia._oleaut32.SafeArrayGetUBound(identity_array, 1, ctypes.byref(upper)) >= 0
                assert 0 <= upper.value - lower.value < 128
                for index in range(lower.value, upper.value + 1):
                    item, position = ctypes.c_int(), ctypes.c_long(index)
                    assert (
                        uia._oleaut32.SafeArrayGetElement(
                            identity_array, ctypes.byref(position), ctypes.byref(item)
                        )
                        >= 0
                    )
                    identity.append(item.value)
            finally:
                uia._oleaut32.SafeArrayDestroy(identity_array)
        hit = window_from_point((rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2)
        handles = [handle for handle in (native.value, hit) if handle]
        owned = any(handle == before[1] or user32.IsChild(before[1], handle) for handle in handles)
        return {
            "identity": identity,
            "kind": kind.value,
            "focus": bool(focus.value),
            "native": native.value,
            "hit": hit,
            "owned": bool(owned),
            "read_only": uia._read_only(element),
            "bounds": [rect.left, rect.top, rect.right, rect.bottom],
        }

    def inspect(scope, label):
        if not scope:
            return None
        direct = metadata(scope)
        direct["source"] = label
        found = [direct]
        array = result(scope, 6, [ctypes.c_int, ctypes.c_void_p], 4, condition)
        if array:
            count = ctypes.c_int()
            uia._call(array, 3, [ctypes.POINTER(ctypes.c_int)], ctypes.byref(count))
            if count.value > 8:
                raise RuntimeError("too_many_focus_candidates")
            for index in range(count.value):
                element = result(array, 4, [ctypes.c_int], index)
                item = metadata(element)
                item["source"] = label + "/descendant"
                found.append(item)
        candidates.extend(found)
        return choose(candidates)

    try:
        assert (
            uia._ole32.CoCreateInstance(uia._CLSID, None, 1, uia._IID, ctypes.byref(automation))
            >= 0
        )
        value = uia._Variant()
        value.vt, value.data.boolean = 11, -1
        condition = result(automation, 23, [ctypes.c_int, uia._Variant], 30008, value)
        global_focus = result(automation, 8, [])
        native_scope = result(automation, 6, [wintypes.HWND], before[1])
        selected = inspect(global_focus, "uia_focus")
        if selected is None or selected["read_only"] is None:
            selected = inspect(native_scope, "native_focus")
        if (selected is None or selected["read_only"] is None) and native_scope:
            walker = result(automation, 14, [])
            parent = result(walker, 3, [ctypes.c_void_p], native_scope) if walker else None
            if parent:
                handle = wintypes.HWND()
                uia._call(parent, 36, [ctypes.POINTER(wintypes.HWND)], ctypes.byref(handle))
                if handle.value and user32.IsChild(before[0], handle.value):
                    selected = inspect(parent, "parent")
        stable = before == native_focus()
        return {
            "decision": "resolved" if selected and stable else "unknown",
            "reason": "unique_owned_focus" if selected and stable else "ambiguous_or_changed",
            "foreground": before[0],
            "native_focus": before[1],
            "selected": selected,
            "candidates": candidates,
        }
    except (OSError, RuntimeError, AssertionError) as error:
        return {"decision": "unknown", "reason": str(error)}
    finally:
        for reference in reversed(references):
            uia._call(reference, 2, [])
        if automation:
            uia._call(automation, 2, [])
        uia._ole32.CoUninitialize()


def self_test():
    actual = {"identity": [1], "focus": True, "owned": True}
    stale = {"identity": [2], "focus": True, "owned": False}
    other = {"identity": [3], "focus": True, "owned": True}
    assert choose([actual, stale]) is actual
    assert choose([actual, actual]) is actual
    assert choose([actual, other]) is None
    assert choose([stale]) is None
    assert choose([{**actual, "focus": False}]) is None
    assert choose([{**actual, "identity": []}]) is None
    editor = {**actual, "read_only": False}
    host = {**other, "read_only": None}
    assert choose([editor, host]) is editor
    assert choose([editor, {**other, "read_only": True}, host]) is None
    print("PASS: stale siblings, duplicate IDs, ambiguity, and missing focus")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--watch", type=int, default=1)
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        deadline, previous = time.monotonic() + args.watch, None
        while time.monotonic() < deadline:
            current = json.dumps(probe(), sort_keys=True)
            if current != previous:
                print(current, flush=True)
                previous = current
            time.sleep(0.5)
