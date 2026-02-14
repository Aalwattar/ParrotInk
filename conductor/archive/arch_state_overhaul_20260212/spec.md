# Track Specification: Architecture & State Overhaul

## Overview
Decompose the `AppCoordinator` "God Object" into specialized controllers and replace boolean-based state tracking with a robust, unified State Machine. This overhaul improves maintainability, reduces side effects, and prepares the application for production stability.

## 1. Functional Scope

### 1.1 Unified AppState (I2)
- **Goal:** Replace `is_listening`, `is_connecting`, `_is_shutting_down`, and `session_cancelled` with a single source of truth.
- **States:** `IDLE`, `CONNECTING`, `LISTENING`, `STOPPING` (transitioning to idle), `ERROR`, `SHUTTING_DOWN`.
- **Logic:** Derived properties in `AppCoordinator` for backward compatibility (e.g., `@property def is_listening(self) -> bool: return self.state == AppState.LISTENING`).

### 1.2 AppCoordinator Decomposition (I1)
- **Goal:** Move logic out of `main.py` into specialized managers.
- **ConnectionManager:** Handles provider lifecycle, authentication, warm-connection timers, and session rotation.
- **AudioPipeline:** Manages the orchestration of `AudioStreamer`, `AudioAdapter`, and the asynchronous pipe to the provider.
- **InputMonitor:** (Already partially started in previous track) Handles keyboard and mouse events.
- **InjectionController:** Manages `SmartInjector` and suppresses duplicate events during typing.

## 2. Technical Goals
- **Single Responsibility:** Each new component should have a clearly defined interface.
- **State Invariants:** Ensure it is impossible to be in an "invalid" state (e.g., listening without an active audio task).
- **Testability:** Enable unit testing of the `ConnectionManager` and `AudioPipeline` without requiring a full `AppCoordinator` or UI.

## 3. Acceptance Criteria
- [ ] `AppCoordinator` is reduced in size by at least 40%.
- [ ] A central `AppState` enum governs all major logic branches.
- [ ] All existing tests pass (`pytest`).
- [ ] `ruff` and `mypy` pass with zero violations.
- [ ] "Definition of Done" Gate is passed.

## 4. Out of Scope
- Changing the underlying transcription providers or audio capture library.
- Modifying UI visual design.
