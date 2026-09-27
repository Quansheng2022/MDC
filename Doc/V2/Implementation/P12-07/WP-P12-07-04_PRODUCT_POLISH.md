# WP-P12-07-04 — Main Window Product Polish

**Product Baseline SHA:** `f3b4e3d5d15d7b95f20fea19515e2e49d8f3e44e`  
**Authority:** G0/G1 bounded.

## Objective
Polish the existing workflow without redesigning it.

## Authorized
Spacing, margins, alignment, hierarchy, button sizing, consistent labels/capitalization, concise wording, empty-state wording, tooltips, minor layout/dialog sizing.

## Frozen Workflow
```text
EMPTY → READY → CONVERTING → SUCCESS / SUCCESS_WITH_WARNING / FAILED
```

Preserve source/drop, output selection, Convert, result/report, Open Document/Open Folder, lifecycle and duplicate protection.

## Forbidden
No dashboard, sidebar, home screen, wizard, new conversion state/feature/report/settings category/theme engine.

## Tests
Focused GUI regression across existing states and controls. No full regression solely for cosmetics.

## Acceptance
Existing workflow/state semantics unchanged; GUI regression PASS; Core/Golden/CLI changes=0.
