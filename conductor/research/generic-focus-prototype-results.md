# Generic focus recovery: prototype results

18 October 2026. Prototype question: can native focus ownership replace the Excel class-name bridge without selecting stale Copilot focus?

**Verdict: the observed Excel scenarios pass.** The metadata-only watcher resolved selected cells as writable DataItem controls, Copilot's host as its writable focused ComboBox, and two separate in-cell editing sessions as a writable virtual Edit below the native focus host's parent. The latter had no native HWND; a physical point lookup inside its bounds matched the current native focus HWND. The parent pane had no read-only metadata. No application names or class names participate in this lookup.

The first probe stopped at the focused in-cell pane. The corrected probe continues the bounded lookup when metadata is unavailable and prefers a unique candidate with explicit read-only metadata over its unsupported host. Both writable and read-only candidates participate: a read-only result is never discarded in favor of a writable result. Distinct competing candidates remain unknown. Candidate sets accumulate across lookup scopes so later scopes cannot hide earlier contradictions.

The watcher read only types, bounds, runtime IDs, native HWNDs, focus flags and read-only metadata. It did not read text, screenshots, cell values or field names, send input, or change focus. The user supplied focus changes. The production app was not replaced during this experiment.

Self-checks cover stale siblings with different native ownership, duplicate IDs, multiple owned candidates, missing focus/identity, a provider-backed editor beside its host, and conflicting writable/read-only candidates. Live capture corroborates current native ownership; stale candidate rejection and ambiguity are also tested deterministically.

## Limits and production requirements

- This proves these provider shapes on this machine, not universal coverage or Win+H parity.
- Physical hit testing can be unavailable under occlusion or invalid bounds; do not turn that into a permissive fallback.
- A writable ValuePattern alone is insufficient for arbitrary controls. Resolution and text capability assessment remain separate.
- Retain explicit disabled/password/read-only policy, reject ambiguous or changing focus, and validate again before insertion.
- Search suggestions require their explicit ControllerFor relationship; unrelated siblings must not be selected.
- Real insertion and independent control families still need acceptance checks after implementation.

Prototype source is captured on branch `codex/text-target-prototype`. See [the API evidence](windows-editable-target-refactor-evidence.md) and [the proposal](../editable_target_refactor_proposal.md).
