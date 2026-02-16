# Track Spec: Tray Menu Hotkey Label Sync

## Overview
There is a minor UI bug where changing the hotkey successfully updates the application's behavior and the `config.toml`, but the System Tray menu item (e.g., "Change Hotkey (Ctrl+Alt+V)") continues to display the old hotkey until the menu is forced to refresh (usually by repeating the action).

## Functional Requirements
- **Immediate UI Refresh**: Upon a successful hotkey change, the system tray menu must immediately reflect the new hotkey in its label.
- **Consistent State**: The tray menu labels must always be in sync with the current `config` object held by the `AppCoordinator`.

## Non-Functional Requirements
- **Thread Safety**: UI refreshes must occur on the UI thread to prevent the "Impossible Freeze" bug.
- **Minimal Impact**: The refresh logic should be efficient and not cause the tray icon to flicker or disappear.

## Acceptance Criteria
- [ ] Change the hotkey from `Ctrl+Alt+V` to `Ctrl+Space`.
- [ ] Immediately right-click the tray icon.
- [ ] Confirm the menu item now reads "Change Hotkey (Ctrl+Space)" without needing a restart or second change.

## Out of Scope
- Changing the actual hotkey recording logic (which is verified as working).
- Modifying the HUD's hotkey display (which is also working).
