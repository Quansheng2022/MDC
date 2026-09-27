# WP-P12-07-06 — Verification & Closure

**Product Baseline SHA:** `f3b4e3d5d15d7b95f20fea19515e2e49d8f3e44e`  
**Authority:** Closure only; no new feature work.

## Preconditions
WP-P12-07-01 through 05 CLOSED.

## Verify
1. Settings/persistence: defaults, persistence, folders, geometry, reset, GUI ownership only.
2. Settings UX: Save persists, Cancel discards, Reset correct, no conversion trigger.
3. About/Privacy: identity, version authority, bounded privacy wording, no network feature.
4. Product Polish: workflow/states unchanged; P12-06 diagnostics/output behavior preserved.
5. Keyboard/Accessibility/Window: Tab/focus/dialog behavior, accessibility, geometry, off-screen safety, close protection, High-DPI.
6. Architecture drift:
```text
GUI→Core direct calls = 0
Application Qt dependency = 0
Conversion semantics changed = 0
Diagnostics semantics changed = 0
Output semantics changed = 0
Core/Canonical/QA/Golden changes = 0
CLI/public API breaking changes = 0
```

## Regression
Run once:
- complete GUI suite
- P12-07 focused tests
- application regression
- relevant CLI/public API/config/QA
- full regression
- Golden/Acceptance
- real Windows GUI smoke

Known approved baseline failures may remain pre-existing if unchanged. Required: P12-07 introduced failures=0.

## Closure Evidence
Create exactly:
`Doc/V2/Implementation/P12-07/P12-07_CLOSURE_EVIDENCE.md`

Record baselines, WP closure SHAs, tests, settings evidence, UX evidence, About/Privacy, polish, keyboard/accessibility/window/High-DPI, drift, deferred issues, blockers, closure decision.

## Exit
If all checks pass:
```text
P12-07 Settings / Product Polish = CLOSED / ACCEPTED
P12-08 Packaging / Installer = AUTHORIZED / NEXT
```
