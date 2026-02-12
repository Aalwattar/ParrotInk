# Implementation Plan: Headless Evaluation Mode (Eval)

Add a test-only, headless CLI mode (`eval`) to `voice2text` that replays a WAV file through the existing transcription pipeline for deterministic accuracy testing.

## Phase 1: Infrastructure & Decoupling
Refactor the application entry point to separate the CLI dispatcher from the UI/Tray logic, ensuring strict import boundaries for the headless mode.

- [x] Task: Create `engine/gui_main.py` and move existing TrayApp/Tkinter startup logic there.
- [x] Task: Create `engine/eval_main.py` as a placeholder for the headless evaluation runner.
- [x] Task: Refactor `main.py` to act as a clean CLI dispatcher using `argparse` sub-commands.
- [x] Task: Write a regression test `tests/test_import_boundaries.py` that asserts `engine.eval_main` does not import `pystray` or `tkinter`.
- [x] Task: Conductor - User Manual Verification 'Infrastructure & Decoupling' (Protocol in workflow.md)

## Phase 2: Audio Replay Engine
Implement the core logic for reading WAV files, downmixing to mono, and pacing the output to simulate real-time microphone input.

- [x] Task: Create `engine/audio/replay.py` with `WavReplayer` class.
    - [x] Implement 16-bit PCM WAV reading.
    - [x] Implement mono downmixing for multi-channel files.
    - [x] Implement real-time pacing (sleep between chunks).
- [x] Task: Write unit tests in `tests/test_audio_replay.py` for `WavReplayer`.
    - [x] Verify mono downmix logic.
    - [x] Verify chunking and timing.
- [x] Task: Conductor - User Manual Verification 'Audio Replay Engine' (Protocol in workflow.md)

## Phase 3: Headless Coordinator & JSON Output
Implement the evaluation runner that connects the `WavReplayer` to the existing transcription providers and captures the metrics for the JSON output.

- [x] Task: Implement `EvalCoordinator` in `engine/eval_main.py`.
    - [x] Support provider selection (OpenAI/AssemblyAI).
    - [x] Track "Time to First Partial" and "Time to First Final".
    - [x] Implement timeout logic.
- [x] Task: Implement the JSON output contract in `EvalCoordinator`.
- [x] Task: Write integration tests in `tests/test_eval_flow.py` (using mocks for providers).
- [x] Task: Conductor - User Manual Verification 'Headless Coordinator & JSON Output' (Protocol in workflow.md)

## Phase 4: Final Integration & CLI Validation
Wire the `eval` command to the `EvalCoordinator` and perform end-to-end validation.

- [ ] Task: Wire `main.py eval` to call `engine.eval_main`.
- [ ] Task: Perform manual end-to-end verification with a sample WAV file.
- [ ] Task: Verify no UI elements or sounds are triggered in `eval` mode.
- [ ] Task: Conductor - User Manual Verification 'Final Integration & CLI Validation' (Protocol in workflow.md)
