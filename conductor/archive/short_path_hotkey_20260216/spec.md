# Track Spec: Short Path Hotkey Migration

## Overview
The current hotkey capture architecture is over-engineered, using a passive global listener that monitors all keys and filters them multiple layers away from the OS hook. This causes non-modifier keys (like Space or V) to "leak" into the active application before they can be suppressed.

This track migrates the capture logic to the "Short Path" using the `keyboard` library, which allows for C-level suppression of specific hotkeys.

## Functional Requirements
- **Zero Leakage**: When the hotkey (e.g., `Ctrl+Space`) is pressed, the non-modifier key must be suppressed system-wide.
- **Architectural Simplification**: Remove the `queue.Queue` and `WorkerThread` from the interaction loop.
- **Mode Support**: Support both "Hold to Talk" and "Toggle" modes natively.
- **Dynamic Configuration**: Hotkey changes must apply immediately without restarting the application.

## Non-Functional Requirements
- **Safety**: Use specialized hotkey APIs (`keyboard.add_hotkey`) rather than low-level filters to prevent OS-level freezes.
- **Stability**: Ensure that modifiers (Ctrl, Alt, etc.) are correctly released to prevent "stuck key" scenarios.

## Acceptance Criteria
- [ ] Character leakage is 100% eliminated in Notepad while holding the hotkey.
- [ ] Application architecture is reduced by removing redundant threads and queues.
- [ ] Changing the hotkey in the Tray menu works immediately.
- [ ] Switching between "Hold to Talk" and "Toggle" works without bugs.
