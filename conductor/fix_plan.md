# Fix Plan: Diarization Output Formatting

**Goal:** Resolve the confusing `[SUNKNOWN]` and `[SA]` outputs, and introduce newlines (`\n`) when speakers change mid-sentence.

**Architecture:**
Update `engine/transcription/speaker_manager.py` to reconstruct the transcript from the word-level data, allowing it to insert speaker labels and newlines exactly where the speaker changes, rather than just prepending to the beginning of the entire sentence.

### Task 1: Refactor SpeakerManager Logic

**Files:**
- Modify: `engine/transcription/speaker_manager.py`
- Modify: `tests/test_speaker_manager.py`

- [ ] **Step 1: Rewrite `format_with_speaker`**
    Iterate through `words`. Track the speaker for each word. If the speaker changes, append a newline (if not the first word) and the clean speaker label before appending the word's text.

- [ ] **Step 2: Add Label Sanitization**
    Create a `_clean_label` method.
    - If "UNKNOWN", map to something graceful (e.g., skip label or show `[?]`). Let's skip it to avoid clutter.
    - Map "A" -> "S1", "B" -> "S2", etc., using a simple dictionary to keep it numeric as requested.

- [ ] **Step 3: Update Unit Tests**
    Test mid-sentence changes and label sanitization.

### Task 2: Verify DOD
- Run `ruff`, `mypy`, `pytest`.
