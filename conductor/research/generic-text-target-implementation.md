# Generic text target assessment

18 October 2026. Implementation branch: `codex/generic-text-targets`. Baseline fix `c76ba8f` was committed and pushed to `origin/master` before this work. The throwaway probe and research are preserved in `380957a`, also referenced by local branch `codex/text-target-prototype`.

## What changed

`editor_focus.py` separates UIA metadata acquisition, target resolution, and a pure `assess_target` policy. The existing `FocusedElement.can_dictate` delegates to that policy. `Anchor` exposes the same assessment to startup and uses it through the existing focus checks during recording and immediately before insertion. There is no second insertion policy.

Resolution combines current native focus with focused UIA candidates. It checks native ownership through HWNDs or a physical window lookup inside candidate bounds. It searches the focused provider, native input host, and at most one parent strictly below the foreground window. It accumulates candidates across scopes, collapses repeated runtime IDs, and rejects competing fields, including fields whose permissions are unknown. Only unsupported Pane/Window carriers may yield to their inner editor. Read-only, disabled, password, and TextEdit-capable candidates remain in contention. A changing native focus snapshot is retried once; another change yields unknown. Native wrappers previously in `anchor.py` now live in `window_focus.py` to avoid circular imports.

The EXCEL6/XLDESK helper and all application-class checks are removed. Search suggestions retain the existing generic ControllerFor relationship check; its adjacent-layout limitation remains documented in code.

Assessment reports editable, not_editable, or unknown with a diagnostic reason. Disabled/password/read-only targets are blocked. A writable standard text role or TextEdit-capable custom role supplies positive text semantics. A writable ValuePattern alone on another role remains unknown: it may represent a non-text value. The selected text range takes precedence over a writable whole-control value, so protected/mixed ranges cannot inherit whole-document write permission. Missing metadata stays unknown, including an Edit control without write-permission evidence.

Unknown blocks recording with “Cannot verify this field; click an editable text field.” Diagnostics include the decision and reason, without field names or text. Control scope still binds the original runtime ID; window scope can follow another verified field in the same window. Missing accessibility during click validation now blocks instead of reusing stale bounds.

No new dependency, setting, focus mutation, SetValue insertion, or sample keystroke was added. UI Automation 8 supplies 500 ms connection and transaction timeouts. Those are per-provider-call limits, not an aggregate deadline or process isolation guarantee.

## Evidence and validation

- The [metadata-only prototype](generic-focus-prototype-results.md) resolved selected cells, in-cell editors, and Copilot without application names; the user supplied focus changes.
- The focused regression suite passes 110 tests covering capability decisions, protected/mixed metadata, stale siblings, ambiguity, bounded parent lookup, changing focus, missing targets, startup rejection before network/microphone, recording cancellation, worker insertion guards, shutdown, and logging. Ruff passes for changed Python files.
- The user confirmed dictation works in a selected Excel cell, a double-clicked cell, and Copilot with the first refactored build. Matching anchor logs show the three distinct native targets. Changing focus away from the selected cell also cancelled the session. Final review then narrowed carrier preference and required TextEdit evidence for a Custom role; those conservative guards pass deterministic tests. The final package is verified against the tested source before launch.
- Independent Win32/browser/read-only control families have deterministic coverage where modeled, but have not all been exercised in live applications.

The policy is our documented inference from public Windows contracts, not a claim to reproduce Microsoft's private Win+H implementation. See [API evidence](windows-editable-target-refactor-evidence.md).

## Release review corrections (0.2.44)

The native input host is now inspected even when direct UIA focus reports a writable field. Competing fields therefore remain ambiguous across both sources. Physical bounds cannot override an explicit HWND belonging to an unrelated window; point-based recovery remains available for windowless fields and verified containing ancestors. Regression tests first reproduced both review findings, then passed after the fixes; another test preserves containing-window recovery.

Full repository validation passes Ruff, Mypy (194 source files), locked dependency consistency, and 528 tests with four explicit desktop/HUD skips. The full locked suite also passes with `GITHUB_ACTIONS=true`. The recurring GitHub failure was a focus-change test depending on real provider credentials; it now mocks availability and asserts connection was reached before checking that microphone startup was prevented. Version 0.2.44 is synchronized across project metadata, lockfile, executable resources, and installer metadata.

The configured Gitleaks v8.23.3 hook also crashed with `wasm error: invalid table access` under its installed Go toolchain. The pin is updated to v8.24.0, which includes the [upstream compatibility fix](https://github.com/gitleaks/gitleaks/pull/1763); scanning stays enabled.

## Detection follow-up decisions (29 October 2026)

- **Temporary uncertainty (planned):** Keep the existing two-attempt acquisition limit. Consider one fresh reassessment for an unknown result within that budget, without inserting or reusing cached metadata while uncertain. Require the original editor identity and an editable assessment before insertion. Definite blocked targets and verified editor changes must stop immediately. Test unknown-to-original recovery, persistent uncertainty, blocked targets, and focus changes. Provider-call timeouts are not an aggregate time budget; do not promise a fixed end-to-end delay.
- **Center-point ownership (investigate):** Windowless controls can depend on the native window under their center to establish ownership. Popup obstruction is a plausible failure scenario, not a reproduced Edge bug. First reproduce with a focused windowless field under an overlapping popup. Consider verified UIA ancestor/native-host ownership if that supplies equivalent evidence; never accept an unrelated host or replace ownership proof with arbitrary nearby points.
- **Diagnostics (implemented):** Preserve specific unresolved reasons in the final timed assessment log instead of overwriting them with `focus_unresolved`. Keep logs free of field contents and names.
- **Target management (planned):** Keep `Anchor` as the session target boundary. Consolidate repeated editor identity/editability checks there first, preserving window-scope click behavior and strict original-editor insertion. `InjectionController` continues to own queue cancellation and correction state. Avoid a new service or broad module rewrite unless this small consolidation proves insufficient.
- **Dedicated UIA MTA worker (deferred):** Revisit after live browser tests and reason/timing logs show recurring provider stalls or COM/threading failures. A future worker would own COM initialization, serialized UIA acquisition, shutdown, and stale-session rejection. Measure latency and verify cancellation before adoption. A single worker can still be blocked by a provider; per-call timeouts do not guarantee isolation. No worker or dependency change is currently implemented.
