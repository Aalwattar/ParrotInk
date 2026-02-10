# Specification: Smart Interaction & Polish

## 1. Overview
This feature refines the user interaction model to closely mimic Windows Voice Typing (Win+H). The goal is to provide a seamless "Start and Forget" experience where the user can activate transcription and immediately take over manually without conflict. The primary mechanism is a "Smart Toggle" where **any** keyboard interaction stops listening.

## 2. Functional Requirements

### 2.1 Smart Toggle Behavior
- **Activation:** The existing global hotkey (e.g., Ctrl+Alt+V) starts the listening state.
- **Deactivation (Any Key):** Once listening, **ANY** subsequent physical key press on the keyboard (including modifiers, letters, numbers, functional keys, or the hotkey itself) must immediately stop the listening state.
- **Visual Feedback:** The system tray icon must reflect these state transitions instantly (Idle -> Listening -> Idle).

### 2.2 Prioritization of Manual Input
- **Conflict Resolution:** If the listening session is terminated by a key press (indicating the user wants to type manually), the system must **discard** any pending transcription results for that specific session.
- **Rationale:** This prevents "ghost text" from appearing and interrupting the user's manual typing flow. The user's physical input always takes precedence.

### 2.3 Modular Interaction Monitoring
- **Architecture:** The logic for detecting "Stop" triggers (keyboard, and eventually mouse) must be isolated into a separate module or class (e.g., `engine/interaction.py`).
- **Extensibility:** The design must allow for easy addition of new triggers, such as mouse clicks, without modifying the core `AppCoordinator` or `main.py` significantly.

## 3. Non-Functional Requirements
- **Responsiveness:** The "Stop" reaction to a key press must be instantaneous (< 50ms).
- **Decoupling:** The interaction monitor should communicate state changes via callbacks or signals to the `AppCoordinator`.

## 4. Acceptance Criteria
- [ ] Pressing the Hotkey starts the "Listening" state.
- [ ] While "Listening", pressing a random character key (e.g., 'A') immediately stops the listening state.
- [ ] While "Listening", pressing a modifier key (e.g., 'Shift') immediately stops the listening state.
- [ ] If stopped by a key press, **NO** transcription text is injected.
- [ ] Code check: A new module `engine/interaction.py` exists and handles the "Any Key" detection logic.

## 5. Out of Scope
- Implementation of the mouse-click detection (reserved for a future track).
- Changes to transcription provider logic.
