# Implementation Plan: Foundation & Core Engine

## Phase 1: Project Skeleton & Configuration
Establish the project structure and implement a robust configuration loader.

- [x] Task: Set up project structure and initial `main.py` entry point (43bea15)
    - [ ] Create `engine/` directory and `main.py`
    - [ ] Verify environment with a simple "Hello Tray" script
- [ ] Task: Implement TOML configuration loader in `engine/config.py`
    - [ ] **Red:** Write tests for loading and validating `config.toml` (missing keys, invalid types)
    - [ ] **Green:** Implement `Config` class using `pydantic` or `tomllib`
    - [ ] **Refactor:** Ensure clean error reporting for user-friendly notifications
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Project Skeleton & Configuration' (Protocol in workflow.md)

## Phase 2: System Tray & State Management
Implement the background utility and visual feedback.

- [ ] Task: Create System Tray Icon and Menu in `engine/ui.py`
    - [ ] **Red:** Write tests for tray state transitions (Idle -> Listening)
    - [ ] **Green:** Implement `TrayApp` using `pystray`
    - [ ] **Refactor:** Decouple UI logic from business logic using an Event/Signal pattern
- [ ] Task: Implement Provider Selection and Config Opening from Tray
    - [ ] **Red:** Write tests for provider switching logic
    - [ ] **Green:** Implement menu actions and radio item updates
- [ ] Task: Conductor - User Manual Verification 'Phase 2: System Tray & State Management' (Protocol in workflow.md)

## Phase 3: Audio Capture Engine
Capture and process microphone input.

- [ ] Task: Implement Audio Streamer in `engine/audio.py`
    - [ ] **Red:** Write tests for audio chunk generation (mocking `sounddevice`)
    - [ ] **Green:** Implement `AudioStreamer` using `sounddevice` callback
    - [ ] **Refactor:** Optimize buffer sizes and handling of sample rates
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Audio Capture Engine' (Protocol in workflow.md)

## Phase 4: Transcription Integration
Connect to OpenAI and AssemblyAI.

- [ ] Task: Implement Transcription Base and OpenAI Provider in `engine/transcription/`
    - [ ] **Red:** Write tests for OpenAI client interaction (mocking `websockets`/`openai`)
    - [ ] **Green:** Implement `OpenAIProvider`
- [ ] Task: Implement AssemblyAI Provider in `engine/transcription/`
    - [ ] **Red:** Write tests for AssemblyAI WebSocket interaction
    - [ ] **Green:** Implement `AssemblyAIProvider`
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Transcription Integration' (Protocol in workflow.md)

## Phase 5: Final Integration & Hotkeys
Bring all components together.

- [ ] Task: Implement Text Injection in `engine/injector.py`
    - [ ] **Red:** Write tests for injection utility (mocking `SendInput`)
    - [ ] **Green:** Implement `inject_text` using `pywin32`
- [ ] Task: Integrate Hotkeys and Orchestrate Flow in `main.py`
    - [ ] **Red:** Write tests for hotkey triggers and state changes
    - [ ] **Green:** Connect Hotkeys -> Audio -> Transcription -> Injection
- [ ] Task: Conductor - User Manual Verification 'Phase 5: Final Integration & Hotkeys' (Protocol in workflow.md)
