# Track Spec: Hotkey Input Suppression (Anti-Leak)

## Overview
Currently, non-modifier keys used in hotkey combinations (e.g., the 'Space' in 'Ctrl+Space' or 'V' in 'Ctrl+Alt+V') are "leaking" through to the active Windows application. This causes unwanted characters or actions (like spaces or 'v's) to be inserted while the user is trying to dictate.

## Functional Requirements
- **Global Suppression**: When a defined hotkey combination is pressed, the non-modifier keys within that combination must be intercepted and suppressed (blocked) from reaching the system-wide input buffer.
- **Mode Agnostic**: Suppression must work reliably in both "Hold to Talk" and "Toggle" modes.
- **Selective Blocking**: Only the keys defined in the `config.toml` hotkey should be suppressed; all other typing must remain unaffected.

## Non-Functional Requirements
- **Low Latency**: The interception must be fast enough that it doesn't introduce perceptible lag to the hotkey trigger itself.
- **Stability**: The hook must not crash or cause the "stuck key" behavior previously addressed in the staleness track.

## Acceptance Criteria
- [ ] Setting a hotkey like `Ctrl+Space` and holding it down does NOT result in spaces being typed into Notepad.
- [ ] Setting a hotkey like `Ctrl+Alt+V` does NOT result in 'v' being typed into the active window.
- [ ] The application correctly triggers "Listening" state despite the keys being suppressed.

## Out of Scope
- Blocking keys that are NOT part of the registered hotkey.
- Suppressing modifier keys (Ctrl, Alt, Shift, Win) as Windows handles these natively without character insertion.
