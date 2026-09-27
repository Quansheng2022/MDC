# WP-P12-07-02 — Settings UX

**Product Baseline SHA:** `f3b4e3d5d15d7b95f20fea19515e2e49d8f3e44e`  
**Prerequisite:** WP-P12-07-01 CLOSED.

## Objective
Provide one compact Settings surface over accepted GUI preferences.

## Required Interaction
```text
Open Settings
→ edit temporary values
→ Save → persist
→ Cancel → discard
→ Reset to Defaults → GUI defaults only
```

Keep the UI compact; no large settings center.

## Allowed
Checkboxes, simple folder preference controls if needed, Reset, Save, Cancel, one Settings entry point.

## Forbidden
No conversion/QA/filename/diagnostics/telemetry/account/plugin/developer settings.

## Tests
Open, current values load, Save persists, Cancel does not persist, Reset works, reopening reflects state, no conversion triggered, no Core call, application Qt-free.

## Acceptance
Save/Cancel/Reset semantics PASS; conversion unchanged; Core/Golden/CLI changes=0.
