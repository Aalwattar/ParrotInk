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

- [ ] Task: Create `engine/audio/replay.py` with `WavReplayer` class.
    - [ ] Implement 16-bit PCM WAV reading.
    - [ ] Implement mono downmixing for multi-channel files.
    - [ ] Implement real-time pacing (sleep between chunks).
- [ ] Task: Write unit tests in `tests/test_audio_replay.py` for `WavReplayer`.
    - [ ] Verify mono downmix logic.
    - [ ] Verify chunking and timing.
- [ ] Task: Conductor - User Manual Verification 'Audio Replay Engine' (Protocol in workflow.md)

## Phase 3: Headless Coordinator & JSON Output
Implement the evaluation runner that connects the `WavReplayer` to the existing transcription providers and captures the metrics for the JSON output.

- [ ] Task: Implement `EvalCoordinator` in `engine/eval_main.py`.
    - [ ] Support provider selection (OpenAI/AssemblyAI).
    - [ ] Track "Time to First Partial" and "Time to First Final".
    - [ ] Implement timeout logic.
- [ ] Task: Implement the JSON output contract in `EvalCoordinator`.
- [ ] Task: Write integration tests in `tests/test_eval_flow.py` (using mocks for providers).
- [ ] Task: Conductor - User Manual Verification 'Headless Coordinator & JSON Output' (Protocol in workflow.md)

## Phase 4: Final Integration & CLI Validation
Wire the `eval` command to the `EvalCoordinator` and perform end-to-end validation.

- [ ] Task: Wire `main.py eval` to call `engine.eval_main`.
- [ ] Task: Perform manual end-to-end verification with a sample WAV file.
- [ ] Task: Verify no UI elements or sounds are triggered in `eval` mode.
- [ ] Task: Conductor - User Manual Verification 'Final Integration & CLI Validation' (Protocol in workflow.md)
