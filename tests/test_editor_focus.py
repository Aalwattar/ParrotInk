import ctypes

import pytest

from engine.platform_win import editor_focus


@pytest.mark.parametrize("read_only", [True, False])
def test_value_pattern_reports_read_only_without_reading_value(mocker, read_only):
    released = []

    def call(pointer, slot, types, *args):
        if slot == 14:
            assert args[0] == 10002
            args[-1]._obj.value = 77
        elif slot == 5:
            args[-1]._obj.value = int(read_only)
        elif slot == 2:
            released.append(pointer.value)
        else:
            pytest.fail(f"Unexpected native call {slot}")
        return 0

    mocker.patch.object(editor_focus, "_call", side_effect=call)
    clear = mocker.patch.object(editor_focus._oleaut32, "VariantClear", return_value=0)
    assert editor_focus._read_only(ctypes.c_void_p(1)) is read_only
    assert released == [77]
    clear.assert_called_once()


@pytest.mark.parametrize("read_only", [True, False, None])
def test_text_pattern_checks_metadata_and_releases_range(mocker, read_only):
    released = []

    def call(pointer, slot, types, *args):
        if slot == 14:
            if args[0] == 10014:
                args[-1]._obj.value = 77
        elif slot == 5:
            args[-1]._obj.value = 88
        elif slot == 3:
            args[-1]._obj.value = 1
        elif slot == 4:
            args[-1]._obj.value = 99
        elif slot == 9:
            assert args[0] == 40015
            value = args[-1]._obj
            value.vt = 11 if read_only is not None else 0
            value.data.boolean = -1 if read_only else 0
        elif slot == 2:
            released.append(pointer.value)
        else:
            pytest.fail(f"Unexpected native call {slot}")
        return 0

    mocker.patch.object(editor_focus, "_call", side_effect=call)
    clear = mocker.patch.object(editor_focus._oleaut32, "VariantClear", return_value=0)
    assert editor_focus._read_only(ctypes.c_void_p(1)) is read_only
    assert released == [99, 88, 77]
    clear.assert_called_once()


def test_physical_coordinate_context_restores_on_error(mocker):
    from engine.platform_win import dpi

    change = mocker.patch.object(dpi, "_set_context", return_value=123)
    with pytest.raises(RuntimeError), dpi.physical_coordinates():
        raise RuntimeError("test")
    assert change.call_count == 2
    assert change.call_args.args == (123,)


def test_noneditable_target_from_handoff_trace_is_rejected():
    for kind in (50026, 50032):
        assert not editor_focus.FocusedElement((1, 2), kind, (0, 0, 3, 3)).can_dictate


def test_edit_control_with_missing_read_only_metadata_accepts_dictation():
    assert editor_focus.FocusedElement((1, 2), 50004, (0, 0, 100, 30)).can_dictate


@pytest.mark.parametrize("read_only,expected", [(False, True), (True, False), (None, False)])
def test_excel_cell_requires_explicit_writable_metadata(read_only, expected):
    cell = editor_focus.FocusedElement(
        (42, 90645336, 4, 221), 50029, (870, 849, 1310, 878), read_only=read_only
    )
    assert cell.can_dictate is expected


@pytest.mark.parametrize(
    "child_kind,read_only,legacy_excel,parent_class,expected",
    [
        (50003, False, False, "", True),
        (50004, True, False, "", False),
        (50000, False, False, "", False),
        (None, None, False, "", False),
        (50004, False, True, "XLDESK", True),
        (50004, True, True, "XLDESK", False),
        (50004, False, True, "XLMAIN", False),
    ],
)
def test_host_pane_uses_its_focused_descendant(
    mocker, child_kind, read_only, legacy_excel, parent_class, expected
):
    released = []
    class_name = ctypes.create_unicode_buffer("EXCEL6" if legacy_excel else "WebView2Holder")
    parent_class_name = ctypes.create_unicode_buffer(parent_class)

    def call(pointer, slot, types, *args):
        ptr = pointer.value
        if slot == 2:
            released.append(ptr)
            return 0
        output = args[-1]._obj
        if ptr == 1 and slot == 8:
            output.value = 3
        elif ptr == 1 and slot == 23:
            assert args[0] == 30008  # HasKeyboardFocus, never Name or Value.
            assert args[1].vt == 11 and args[1].data.boolean == -1
            output.value = 10
        elif ptr in (3, 13) and slot == 5:
            assert args[0] == 4 and args[1].value == 10  # Descendants only.
            output.value = 5 if child_kind is not None and (ptr == 13 or not legacy_excel) else None
        elif ptr in (3, 13) and slot == 10:
            assert args[0] == 30012  # ClassName, not document text.
            output.vt = 8
            output.data.record[0] = ctypes.addressof(class_name if ptr == 3 else parent_class_name)
        elif ptr == 1 and slot == 14:
            output.value = 11
        elif ptr == 11 and slot == 3:
            output.value = 13
        elif ptr in (3, 5) and slot == 21:
            output.value = 50033 if ptr == 3 else child_kind
        elif ptr in (3, 5) and slot in (28, 35):
            output.value = int(slot == 28)
        elif ptr in (3, 5) and slot == 43:
            output.left, output.top, output.right, output.bottom = 10, 10, 300, 40
        elif ptr in (3, 5) and slot == 4:
            output.value = ptr
        else:
            pytest.fail(f"Unexpected native call {ptr}:{slot}")
        return 0

    def create(*args):
        args[-1]._obj.value = 1
        return 0

    def runtime_element(array, index, value):
        ctypes.cast(value, ctypes.POINTER(ctypes.c_int)).contents.value = array.value
        return 0

    mocker.patch.object(editor_focus, "_call", side_effect=call)
    mocker.patch.object(
        editor_focus,
        "_read_only",
        side_effect=lambda pointer: read_only if pointer.value == 5 else None,
    )
    mocker.patch.object(editor_focus._ole32, "CoInitializeEx", return_value=0)
    mocker.patch.object(editor_focus._ole32, "CoUninitialize")
    mocker.patch.object(editor_focus._ole32, "CoCreateInstance", side_effect=create)
    for name in ("SafeArrayGetLBound", "SafeArrayGetUBound", "SafeArrayDestroy", "VariantClear"):
        mocker.patch.object(editor_focus._oleaut32, name, return_value=0)
    mocker.patch.object(editor_focus._oleaut32, "SafeArrayGetElement", side_effect=runtime_element)

    result = editor_focus.read_focused_element()

    assert result.can_dictate is expected
    resolved = child_kind is not None and (not legacy_excel or parent_class == "XLDESK")
    assert result.runtime_id == ((5,) if resolved else (3,))
    assert 10 in released


@pytest.mark.parametrize("kind", [50007, 50008, 50020])
def test_non_editor_does_not_accept_typing_from_inherited_text_attributes(kind):
    assert not editor_focus.FocusedElement(
        (1, 2), kind, (0, 0, 100, 30), read_only=False
    ).can_dictate


def test_failed_descendant_query_releases_condition(mocker):
    released = []

    def call(pointer, slot, types, *args):
        if slot == 23:
            args[-1]._obj.value = 10
        elif slot == 5:
            raise OSError("Provider unavailable")
        elif slot == 2:
            released.append(pointer.value)
        return 0

    mocker.patch.object(editor_focus, "_call", side_effect=call)
    assert editor_focus._focused_descendant(ctypes.c_void_p(1), ctypes.c_void_p(3)) is None
    assert released == [10]


@pytest.mark.parametrize(
    "linked,writable,expected", [(True, True, True), (False, True, False), (True, False, False)]
)
def test_search_result_resolves_to_its_linked_writable_input(mocker, linked, writable, expected):
    focus = [3]
    kinds = {3: 50007, 4: 50008, 5: 50003}

    def call(pointer, slot, types, *args):
        ptr = pointer.value
        if slot == 2:
            return 0
        output = args[-1]._obj
        if ptr == 1 and slot == 8:
            output.value = focus[0]
        elif ptr == 1 and slot == 14:
            output.value = 2
        elif ptr == 1 and slot == 3:
            output.value = int(args[0].value == args[1].value)
        elif ptr == 2 and slot == 3:
            output.value = 4 if args[0].value == 3 else None
        elif ptr == 2 and slot == 7:
            output.value = 5
        elif ptr in kinds and slot == 21:
            output.value = kinds[ptr]
        elif ptr in kinds and slot in (28, 35):
            output.value = int(slot == 28)
        elif ptr in kinds and slot == 43:
            output.left, output.top, output.right, output.bottom = 10, 10, 300, 40
        elif ptr in kinds and slot == 14:
            if ptr == 5 and args[0] == 10002:
                output.value = 50
            else:
                raise OSError("Unsupported pattern")
        elif ptr == 50 and slot == 5:
            output.value = int(not writable)
        elif ptr == 5 and slot == 10:
            assert args[0] == 30104
            output.vt = 13
            output.data.record[0] = 60
        elif ptr == 60 and slot == 3:
            output.value = int(linked)
        elif ptr == 60 and slot == 4:
            output.value = 4
        elif ptr in kinds and slot == 4:
            output.value = ptr
        else:
            pytest.fail(f"Unexpected native call {ptr}:{slot}")
        return 0

    def create(*args):
        args[-1]._obj.value = 1
        return 0

    def runtime_element(array, index, value):
        ctypes.cast(value, ctypes.POINTER(ctypes.c_int)).contents.value = array.value
        return 0

    mocker.patch.object(editor_focus, "_call", side_effect=call)
    mocker.patch.object(editor_focus._ole32, "CoInitializeEx", return_value=0)
    mocker.patch.object(editor_focus._ole32, "CoUninitialize")
    mocker.patch.object(editor_focus._ole32, "CoCreateInstance", side_effect=create)
    for name in ("SafeArrayGetLBound", "SafeArrayGetUBound", "SafeArrayDestroy", "VariantClear"):
        mocker.patch.object(editor_focus._oleaut32, name, return_value=0)
    mocker.patch.object(editor_focus._oleaut32, "SafeArrayGetElement", side_effect=runtime_element)
    result = editor_focus.read_focused_element()
    assert result.can_dictate is expected
    if expected:
        focus[0] = 5
        assert result.runtime_id == editor_focus.read_focused_element().runtime_id
