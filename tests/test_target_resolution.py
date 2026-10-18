"""Provider shapes, without application names or document contents."""

import ctypes
from dataclasses import replace

import pytest

from engine.platform_win import editor_focus as focus


def target(identity=1, kind=50004, read_only=False, **changes):
    return focus.FocusedElement(
        (identity,), kind, (10, 10, 100, 30), read_only=read_only, **changes
    )


@pytest.mark.parametrize(
    "item,decision,reason",
    [
        (None, "unknown", "focus_unresolved"),
        (target(enabled=False), "not_editable", "disabled"),
        (target(password=True), "not_editable", "password"),
        (target(read_only=True), "not_editable", "read_only"),
        (target(read_only=None), "unknown", "writability_unavailable"),
        (target(kind=50000), "unknown", "text_input_unverified"),  # Button with writable value.
        (target(kind=50007), "unknown", "text_input_unverified"),  # Rename-capable list item.
        (target(kind=50020), "unknown", "text_input_unverified"),  # Inherited text attributes.
        (target(kind=50025, text_edit=True), "editable", "writable_text_target"),
        (target(kind=50025), "unknown", "text_input_unverified"),
        (target(kind=50033, text_edit=True), "editable", "writable_text_target"),
        (target(kind=50033), "unknown", "text_input_unverified"),  # Non-text value control.
        (target(kind=50003, read_only=None), "unknown", "writability_unavailable"),
        (replace(target(), runtime_id=()), "unknown", "focus_unresolved"),
        (replace(target(), bounds=(0, 0, 0, 20)), "unknown", "invalid_bounds"),
    ],
)
def test_assessment(item, decision, reason):
    assessment = focus.assess_target(item)
    assert (assessment.decision, assessment.reason) == (decision, reason)
    if item:
        assert item.can_dictate is (decision == "editable")


@pytest.fixture
def provider(mocker):
    # Native root=100, input host=200, its provider parent=150, stale sibling=300.
    nodes = {
        3: (target(3, 50033, None), True, 200),
        4: (target(4, 50033, None), False, 150),
        5: (target(5), True, 0),
        6: (target(6, 50003), True, 300),
    }
    children = {3: [], 4: [3, 5, 6]}
    released = []
    settings = {"root": False, "fail": False, "count": None, "global": 3}

    def call(pointer, slot, types, *args):
        ptr = pointer.value
        if slot == 2:
            released.append(ptr)
            return 0
        output = args[-1]._obj
        if ptr == 1:
            if slot == 23:
                assert args[0] == 30008  # HasKeyboardFocus only.
                output.value = 10
            elif slot == 8:
                output.value = settings["global"]
            elif slot == 6:
                assert args[0] == 200
                output.value = 3
            elif slot == 14:
                output.value = 11
            else:
                pytest.fail(f"Unexpected automation slot {slot}")
        elif ptr == 11 and slot == 3:
            output.value = 4
        elif ptr in nodes:
            if slot == 36:
                output.value = 100 if ptr == 4 and settings["root"] else nodes[ptr][2]
            elif slot == 26:
                output.value = int(nodes[ptr][1])
            elif slot == 6:
                assert args[0] == 4 and args[1].value == 10
                if settings["fail"]:
                    raise OSError("provider_failed")
                output.value = ptr + 20
            else:
                pytest.fail(f"Unexpected element slot {slot}")
        elif ptr - 20 in children:
            items = children[ptr - 20]
            if slot == 3:
                output.value = len(items) if settings["count"] is None else settings["count"]
            elif slot == 4:
                output.value = items[args[0]]
            else:
                pytest.fail(f"Unexpected array slot {slot}")
        else:
            pytest.fail(f"Unexpected pointer {ptr}")
        return 0

    mocker.patch.object(focus, "_call", side_effect=call)
    mocker.patch.object(focus, "_read_element", side_effect=lambda ptr: nodes[ptr.value][0])
    mocker.patch.object(focus, "window_from_point", return_value=200)
    mocker.patch.object(focus, "owns_window", side_effect=lambda owner, hwnd: owner == hwnd)
    mocker.patch.object(focus.user32, "IsChild", side_effect=lambda root, hwnd: hwnd in (150, 200))
    return nodes, children, released, settings


def test_parent_bridge_prefers_verified_editor_over_native_host(provider, mocker):
    nodes, _, released, _ = provider
    # The stale field's bounds map to another native host even though it reports focus.
    nodes[6] = (replace(nodes[6][0], bounds=(300, 10, 400, 30)), True, 300)
    mocker.patch.object(
        focus, "window_from_point", side_effect=lambda x, y: 300 if x > 200 else 200
    )
    result = focus._resolve_target(ctypes.c_void_p(1), (100, 200))
    assert result == nodes[5][0]
    assert {3, 4, 5, 6, 10, 11, 23, 24}.issubset(released)


def test_distinct_owned_editors_remain_ambiguous_across_scopes(provider):
    # Both provider objects claim the same native host, so neither is authoritative.
    assert focus._resolve_target(ctypes.c_void_p(1), (100, 200)) is None


@pytest.mark.parametrize("read_only", [True, False, None])
def test_unique_provider_preserves_writability_without_guessing(provider, read_only):
    nodes, children, _, _ = provider
    children[4] = [3, 5]
    nodes[5] = (replace(nodes[5][0], read_only=read_only), True, 0)
    result = focus._resolve_target(ctypes.c_void_p(1), (100, 200))
    assert result == nodes[5][0]
    assert result.can_dictate is (read_only is False)


def test_missing_permissions_on_another_editor_cannot_be_ignored(provider):
    nodes, _, _, _ = provider
    nodes[6] = (target(6, read_only=None), True, 0)
    assert focus._resolve_target(ctypes.c_void_p(1), (100, 200)) is None


@pytest.mark.parametrize("enabled,password", [(False, False), (True, True)])
def test_blocked_native_host_cannot_yield_to_writable_descendant(provider, enabled, password):
    nodes, children, _, _ = provider
    nodes[3] = (replace(nodes[3][0], enabled=enabled, password=password), True, 200)
    children[3] = [5]
    children[4] = [3, 5]
    assert focus._resolve_target(ctypes.c_void_p(1), (100, 200)) is None


def test_parent_search_never_expands_to_top_level_window(provider):
    _, _, _, settings = provider
    settings["root"] = True
    result = focus._resolve_target(ctypes.c_void_p(1), (100, 200))
    assert result.read_only is None
    assert not result.can_dictate


@pytest.mark.parametrize("failure", ["fail", "count"])
def test_failed_or_excessive_queries_release_references(provider, failure):
    _, _, released, settings = provider
    settings[failure] = 9 if failure == "count" else True
    with pytest.raises(OSError):
        focus._resolve_target(ctypes.c_void_p(1), (100, 200))
    assert 10 in released and 3 in released


def test_direct_input_does_not_need_parent_recovery(provider):
    nodes, children, _, settings = provider
    settings["global"] = 5
    children[5] = []
    assert focus._resolve_target(ctypes.c_void_p(1), (100, 200)) == nodes[5][0]


@pytest.mark.parametrize(
    "snapshots,expected_calls",
    [
        ([(100, 200), (100, 300), (100, 300), (100, 300)], 2),
        ([(100, 200), (100, 300), (100, 300), (100, 400)], 2),
        ([(0, 0)], 0),
    ],
)
def test_focus_race_retries_once_and_never_returns_stale_target(mocker, snapshots, expected_calls):
    def create(*args):
        args[-1]._obj.value = 1
        return 0

    mocker.patch.object(focus._ole32, "CoInitializeEx", return_value=0)
    uninitialize = mocker.patch.object(focus._ole32, "CoUninitialize")
    mocker.patch.object(focus._ole32, "CoCreateInstance", side_effect=create)
    mocker.patch.object(focus, "_call")
    mocker.patch.object(focus, "native_focus", side_effect=snapshots)
    resolve = mocker.patch.object(focus, "_resolve_target", return_value=target())
    result = focus.read_focused_element()
    stable = len(snapshots) == 4 and snapshots[-2] == snapshots[-1]
    assert result == (target() if stable else None)
    assert resolve.call_count == expected_calls
    uninitialize.assert_called_once()
