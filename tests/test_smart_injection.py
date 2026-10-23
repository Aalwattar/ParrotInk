import asyncio
import threading
from unittest.mock import patch

import pytest

from engine.transcription.speaker_manager import SpeakerManager


@pytest.mark.asyncio
async def test_cancelled_worker_cannot_insert_after_target_is_reused(coordinator, mocker):
    output = coordinator.injection_controller
    coordinator.loop = asyncio.get_running_loop()
    entered, resume = threading.Event(), threading.Event()

    def delayed_focus():
        entered.set()
        assert resume.wait(2)
        return True

    target = mocker.Mock()
    target.has_focus.side_effect = delayed_focus
    output.begin(target)
    insert = mocker.patch("engine.injector.inject_text")
    output.queue("old partial")
    try:
        assert await asyncio.to_thread(entered.wait, 2)
        output.cancel()
        output.begin(target)
        target.has_focus.side_effect = None
        target.has_focus.return_value = True
        output.queue("new final", is_final=True)
    finally:
        resume.set()
    await output.drain()
    assert "".join(call.args[0] for call in insert.call_args_list) == "new final "


@pytest.mark.asyncio
async def test_new_insertion_session_does_not_backspace_previous_target(coordinator, mocker):
    output = coordinator.injection_controller
    coordinator.loop = asyncio.get_running_loop()
    insert = mocker.patch("engine.injector.inject_text")
    backspace = mocker.patch("engine.injector.inject_backspaces")
    output.queue("old partial")
    await output.drain()
    output.begin(mocker.Mock(has_focus=lambda: True))
    output.queue("new final", is_final=True)
    await output.drain()
    backspace.assert_not_called()
    assert [call.args[0] for call in insert.call_args_list] == ["old partial", "new final", " "]


@pytest.mark.asyncio
async def test_released_target_rejects_late_callbacks(coordinator, mocker):
    coordinator.loop = asyncio.get_running_loop()
    output = coordinator.injection_controller
    insert = mocker.patch("engine.injector.inject_text")
    output.release()
    coordinator.on_final("late final")
    await output.drain()
    insert.assert_not_called()


@pytest.mark.asyncio
async def test_drain_keeps_completed_insertion_failure(coordinator, mocker):
    coordinator.loop = asyncio.get_running_loop()
    output = coordinator.injection_controller
    attempted = threading.Event()

    def fail(*args):
        attempted.set()
        raise OSError("insertion failed")

    mocker.patch("engine.injector.inject_text", side_effect=fail)
    output.queue("final", is_final=True)
    assert await asyncio.to_thread(attempted.wait, 2)
    while output.pending_count:
        await asyncio.sleep(0)
    with pytest.raises(OSError, match="insertion failed"):
        await output.drain()


@pytest.mark.asyncio
@pytest.mark.parametrize("partial_results", [False, True])
@pytest.mark.parametrize("second_speaker", ["A", "B"])
async def test_formatted_turns_preserve_separators_through_insertion(
    coordinator, mocker, partial_results, second_speaker
):
    coordinator.loop = asyncio.get_running_loop()
    coordinator.config.transcription.partial_results = partial_results
    speakers = SpeakerManager()
    screen = ""

    def insert(text):
        nonlocal screen
        screen += text

    def backspace(count):
        nonlocal screen
        screen = screen[:-count]

    mocker.patch("engine.injector.inject_text", side_effect=insert)
    mocker.patch("engine.injector.inject_backspaces", side_effect=backspace)
    for text, speaker in [("Hello", "A"), ("Hi", second_speaker)]:
        coordinator.on_partial(text[:2])
        await coordinator.injection_controller.drain()
        coordinator.on_final(speakers.format_final_turn(text, [], speaker))
        await coordinator.injection_controller.drain()

    label = "S1" if second_speaker == "A" else "S2"
    assert screen == f"[S1] Hello \n[{label}] Hi "
    assert coordinator.injection_controller.injector.last_text == ""
    coordinator.ui_bridge.update_final_text.assert_called_with(f"[{label}] Hi")


@pytest.mark.asyncio
@pytest.mark.parametrize("text", ["Hello", "Hello ", "[S1] Hello\n[S2] Hi"])
async def test_final_insertion_adds_one_trailing_space(coordinator, mocker, text):
    coordinator.loop = asyncio.get_running_loop()
    insert = mocker.patch("engine.injector.inject_text")
    coordinator.on_final(text)
    await coordinator.injection_controller.drain()
    assert "".join(call.args[0] for call in insert.call_args_list) == text.rstrip() + " "


def test_blank_final_does_not_update_or_queue(coordinator, mocker):
    queue = mocker.patch.object(coordinator.injection_controller, "queue")
    coordinator.on_final(" \n\t")
    queue.assert_not_called()
    coordinator.ui_bridge.update_final_text.assert_not_called()
    assert coordinator.session_word_count == 0


@pytest.mark.asyncio
async def test_insertion_guard_runs_after_waiting_for_injection_lock(coordinator, mocker):
    coordinator.loop = asyncio.get_running_loop()
    inject = mocker.patch.object(coordinator.injection_controller.injector, "inject")
    allowed = True
    async with coordinator.injection_controller.lock:
        task = asyncio.create_task(
            coordinator.injection_controller.smart_inject("late text", can_insert=lambda: allowed)
        )
        await asyncio.sleep(0)
        allowed = False
    await task
    inject.assert_not_called()


@pytest.mark.asyncio
async def test_smart_inject_append_only(coordinator):
    coordinator.loop = asyncio.get_running_loop()
    with (
        patch("engine.injector.inject_text") as mock_inject,
        patch("engine.injector.inject_backspaces") as mock_backspace,
    ):
        coordinator.injection_controller.injector.last_text = "Hello"
        await coordinator.injection_controller.smart_inject("Hello world")

        # Should not backspace
        assert not mock_backspace.called
        # Should inject " world"
        mock_inject.assert_called_once_with(" world")
        assert coordinator.injection_controller.injector.last_text == "Hello world"


@pytest.mark.asyncio
async def test_smart_inject_with_backspace(coordinator):
    coordinator.loop = asyncio.get_running_loop()
    with (
        patch("engine.injector.inject_text") as mock_inject,
        patch("engine.injector.inject_backspaces") as mock_backspace,
    ):
        coordinator.injection_controller.injector.last_text = "Hello world"
        await coordinator.injection_controller.smart_inject("Hello there")

        # Should backspace "world" (5 chars)
        mock_backspace.assert_called_once_with(5)
        # Should inject "there"
        mock_inject.assert_called_once_with("there")
        assert coordinator.injection_controller.injector.last_text == "Hello there"


@pytest.mark.asyncio
async def test_smart_inject_complete_change(coordinator):
    coordinator.loop = asyncio.get_running_loop()
    with (
        patch("engine.injector.inject_text") as mock_inject,
        patch("engine.injector.inject_backspaces") as mock_backspace,
    ):
        coordinator.injection_controller.injector.last_text = "Apple"
        await coordinator.injection_controller.smart_inject("Banana")

        # Should backspace "Apple" (5 chars)
        mock_backspace.assert_called_once_with(5)
        # Should inject "Banana"
        mock_inject.assert_called_once_with("Banana")
        assert coordinator.injection_controller.injector.last_text == "Banana"
