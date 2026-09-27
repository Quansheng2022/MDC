# WP-P12-07-05 — Accessibility / Window Behavior

**Product Baseline SHA:** `f3b4e3d5d15d7b95f20fea19515e2e49d8f3e44e`

## Objective
Complete bounded keyboard, focus, accessibility, geometry, and High-DPI improvements.

## Keyboard / Focus
- logical Tab order
- standard Enter/Space activation
- Esc closes dialogs where appropriate
- at most a few standard shortcuts if clearly useful
- practical focus restoration

No configurable shortcut framework.

## Accessibility
- meaningful accessible names
- understandable labels
- outcome not conveyed by color alone
- report keyboard accessible

## Window Behavior
- restore geometry/size
- sane minimum size
- invalid/off-screen restore safe
- normal close correct
- preserve frozen rule:
```text
while worker.is_running → unsafe close remains blocked
```

## High-DPI
Perform bounded Windows/Qt High-DPI smoke only. No packaging manifest changes.

## Tests
Keyboard/focus, geometry, close safety, accessibility checks, Windows smoke, High-DPI smoke.

## Acceptance
Keyboard/focus/accessibility/window/High-DPI PASS; lifecycle unchanged; Core/Golden/CLI changes=0.
