# Specification: Fix 'Hold to Talk' Interruption Bug

## 1. Overview
Currently, when `hold_to_talk` is enabled, the dictation session is being prematurely interrupted by other key presses. This is likely because the "Stop on Any Key" logic is still active and conflicting with the "Hold" behavior. This track will ensure that when `hold_to_talk` is enabled, the "Stop on Any Key" feature is completely deactivated.

## 2. Functional Requirements

### 2.1 Conditional 'Stop on Any Key' Deactivation
- **Logic:** If the configuration setting `interaction.hold_to_talk` is set to `true`, the application must disable the global keyboard hook that stops dictation upon pressing "any key".
- **Focus:** In this mode, the system should only listen for the **release** event of the specific hotkey used to start the session.

### 2.2 Input Handling
- While a "Hold to Talk" session is active:
  - **Hotkey Release:** Stop recording immediately.
  - **Any Other Key Press:** Ignore completely (do not stop recording).

## 3. Non-Functional Requirements
- **Performance:** Ensure that the keyboard listener remains lightweight even when filtering for a specific key release.
- **Robustness:** Ensure that the session *always* stops when the hotkey is released, even if other keys are pressed simultaneously.

## 4. Acceptance Criteria
1.  **Configuration Check:** Set `hold_to_talk = true` in `config.toml`.
2.  **Hold to Start:** Press and hold the configured hotkey (e.g., `Caps Lock`) -> Recording starts.
3.  **Interference Test:** While still holding the hotkey, press several other keys (e.g., `Shift`, `Space`, `A`, `B`).
    - **Expected Outcome:** Recording **continues** without interruption.
4.  **Release to Stop:** Release the hotkey.
    - **Expected Outcome:** Recording **stops** immediately.
