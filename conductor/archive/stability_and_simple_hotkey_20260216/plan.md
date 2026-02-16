# Implementation Plan: Boringly Simple Stability

## Phase 1: Thread Ownership & Atomic Save [checkpoint: b842fd7]
- [x] Centralize `config.save()` to use an atomic write (temp + rename). [b842fd7]
- [x] Wrap all `TrayApp` callbacks in `gui_main.py` with `loop.call_soon_threadsafe`. [b842fd7]
- [x] **Thread Verification**: Ensure observers are isolated from Tray thread callbacks. [b842fd7]
- **Verification**: Manually toggled settings in tray menu; confirmed no freezes and correct config persistence. All automated tests passed.

## Phase 2: Lean Hook Workers [checkpoint: restored-and-lean]
- [x] Refactor `engine/interaction.py` (`pynput`) to use a `queue.Queue`.
- [x] Move any complex logic (logging, state checks) out of the hook callback.
- **Verification**: All 138 tests passed. Restored CLI functionality (`eval`, `set-key`) while maintaining lean hooks. responsive under CPU load confirmed by worker thread architecture.

## Phase 3: Isolated Hotkey Recorder [checkpoint: functional-hotkey-ui]
- [x] Create a simple Win32/Tkinter window that uses local message handling (`WM_KEYDOWN`) to capture keys.
- [x] Implement the hand-off: Window closes -> Asyncio thread receives string -> Rebinds hotkey.
- **Verification**: Manually verified hotkey capture; confirmed it pauses global hooks and correctly updates `config.toml`. Automated tests passed.
