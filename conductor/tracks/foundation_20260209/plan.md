# Implementation Plan: Foundation & Core Engine

## Phase 1: Project Skeleton & Configuration [checkpoint: ff90a51]
Establish the project structure and implement a robust configuration loader.

- [x] Task: Set up project structure and initial `main.py` entry point (43bea15)
    - [x] Create `engine/` directory and `main.py`
    - [x] Verify environment with a simple "Hello Tray" script
- [x] Task: Implement TOML configuration loader in `engine/config.py` (ec26af5)
    - [x] **Red:** Write tests for loading and validating `config.toml` (missing keys, invalid types)
    - [x] **Green:** Implement `Config` class using `pydantic` or `tomllib`
    - [x] **Refactor:** Ensure clean error reporting for user-friendly notifications
- [x] Task: Conductor - User Manual Verification 'Phase 1: Project Skeleton & Configuration' (Protocol in workflow.md)

## Phase 2: System Tray & State Management [checkpoint: 6ff0240]
Implement the background utility and visual feedback.

- [x] Task: Create System Tray Icon and Menu in `engine/ui.py` (de38086)
    - [x] **Red:** Write tests for tray state transitions (Idle -> Listening)
    - [x] **Green:** Implement `TrayApp` using `pystray`
    - [x] **Refactor:** Decouple UI logic from business logic using an Event/Signal pattern
- [x] Task: Implement Provider Selection and Config Opening from Tray (d79529e)
    - [x] **Red:** Write tests for provider switching logic
    - [x] **Green:** Implement menu actions and radio item updates
- [x] Task: Conductor - User Manual Verification 'Phase 2: System Tray & State Management' (Protocol in workflow.md)

## Phase 3: Audio Capture Engine [checkpoint: 368888f]
Capture and process microphone input.

- [x] Task: Implement Audio Streamer in `engine/audio.py` (778eb61)
    - [x] **Red:** Write tests for audio chunk generation (mocking `sounddevice`)
    - [x] **Green:** Implement `AudioStreamer` using `sounddevice` callback
    - [x] **Refactor:** Optimize buffer sizes and handling of sample rates
- [x] Task: Conductor - User Manual Verification 'Phase 3: Audio Capture Engine' (Protocol in workflow.md)

## Phase 4: Transcription Integration [checkpoint: cb69717]
Connect to OpenAI and AssemblyAI.

- [x] Task: Implement Transcription Base and OpenAI Provider in `engine/transcription/` (cb69717)
    - [x] **Red:** Write tests for OpenAI client interaction (mocking `websockets`/`openai`)
    - [x] **Green:** Implement `OpenAIProvider`
- [x] Task: Implement AssemblyAI Provider in `engine/transcription/` (cb69717)
    - [x] **Red:** Write tests for AssemblyAI WebSocket interaction
    - [x] **Green:** Implement `AssemblyAIProvider`
- [x] Task: Conductor - User Manual Verification 'Phase 4: Transcription Integration' (Protocol in workflow.md)

## Phase 5: Final Integration & Hotkeys
Bring all components together.

- [ ] Task: Implement Text Injection in `engine/injector.py`
    - [ ] **Red:** Write tests for injection utility (mocking `SendInput`)
    - [ ] **Green:** Implement `inject_text` using `pywin32`
- [ ] Task: Integrate Hotkeys and Orchestrate Flow in `main.py`
    - [ ] **Red:** Write tests for hotkey triggers and state changes
    - [ ] **Green:** Connect Hotkeys -> Audio -> Transcription -> Injection
- [ ] Task: Conductor - User Manual Verification 'Phase 5: Final Integration & Hotkeys' (Protocol in workflow.md)
