# Implementation Plan: Boringly Simple Stability

## Phase 1: Thread Ownership & Atomic Save
- [x] Centralize `config.save()` to use an atomic write (temp + rename). [c19ad41]
- [x] Wrap all `TrayApp` callbacks in `gui_main.py` with `loop.call_soon_threadsafe`. [c19ad41]
- **Verification**: Verify that changing a setting in the Tray menu no longer has any chance of freezing the app.

## Phase 2: Lean Hook Workers
- [ ] Refactor `engine/interaction.py` (`pynput`) to use a `queue.Queue`.
- [ ] Move any complex logic (logging, state checks) out of the hook callback.
- **Verification**: Verify that dictation start/stop remains responsive under CPU load.

## Phase 3: Isolated Hotkey Recorder
- [ ] Create a simple Win32/Tkinter window that uses local message handling (`WM_KEYDOWN`) to capture keys.
- [ ] Implement the hand-off: Window closes -> Asyncio thread receives string -> Rebinds hotkey.
- **Verification**: Test hotkey recording; ensure it never blocks the system tray or dictation.
