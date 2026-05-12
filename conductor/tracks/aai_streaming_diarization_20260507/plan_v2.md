# Implementation Plan: Consultant Architecture for Streaming Diarization

## Objective
Fix the fundamental architectural conflict between single-line "live" diffing (`SmartInjector`) and multi-line structured text (`SpeakerManager`) by implementing the consultant's dual-path injection pattern.

## Key Files & Context
- `engine/transcription/speaker_manager.py`: Needs a rewrite to use `format_final_turn` and handle both word-level and turn-level speaker labels.
- `engine/transcription/assemblyai_provider.py`: Needs to stop formatting partials with speaker labels so they don't pollute the injector's state.
- `engine/injector.py`: Needs `SendInput` validation.
- `tests/test_speaker_manager.py`: Needs new acceptance tests.

## Background & Motivation
The consultant correctly identified that the missing `\n` characters and repeated labels are not a failure of `VK_RETURN`. The issue is that `SmartInjector` (which uses backspaces to correct real-time text) cannot handle newlines. When `SpeakerManager` adds a newline to a *partial* result, the injector tries to backspace over it later, breaking the state. The solution is to isolate diarization to *final turns only*, effectively treating the final output as an append-only stream.

## Implementation Steps

### 1. Refactor `SpeakerManager`
Replace the current implementation with the consultant's `format_final_turn` logic:
- Maintain `current_speaker_on_screen` and `has_sent_any_text` state.
- Handle both `words` array and the parent `turn_speaker` label.
- Output clean, deterministic segments (e.g., `\n[S2] text`).

### 2. Update `AssemblyAIProvider`
Modify `_handle_event` to use two separate paths when `speaker_manager` is active:
- **Partials**: Pass the raw, unformatted `text` to `self.on_partial(text)`. This allows the HUD to update, and the `SmartInjector` can safely backspace this single-line text later.
- **Finals**: Extract `words`, `speaker_label`, and `end_of_turn`. Call `self.speaker_manager.format_final_turn(...)`. If it returns formatted text, pass it to `self.on_final(formatted)`.

### 3. Update `Injector` Error Checking
In `engine/injector.py`, check the return value of `USER32.SendInput`. If the number of events sent does not match `n_inputs`, log a warning with `ctypes.get_last_error()`. Keep the `VK_RETURN` logic for `\n`.

### 4. Implement Acceptance Tests
Write the 5 acceptance tests provided by the consultant in `tests/test_speaker_manager.py`:
1. Turn 1 (no words), Turn 2 (with words).
2. Turn 1 (turn speaker, no words), Turn 2 (turn speaker, words).
3. Mid-turn speaker change.
4. Normal dictation (no manager).
5. UNKNOWN speaker after existing S1.

## Verification & Testing
- Run `uv run pytest -q`.
- Ensure `tests/debug_diarization_logic.py` output cleanly shows the single-line partials being replaced by multi-line finals.
- Verify `ruff` and `mypy` pass.
