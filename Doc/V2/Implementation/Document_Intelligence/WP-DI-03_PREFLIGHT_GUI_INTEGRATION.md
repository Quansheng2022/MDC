# WP-DI-03 — Preflight GUI Integration

**Program:** Document Intelligence Upgrade
**Baseline:** `DOCUMENT_INTELLIGENCE_ARCHITECTURE_BASELINE.md` (WP-DI-01)
**Change classification:** G1 — additive GUI surface

## Scope

Choose the smallest compatible UX from the implementation plan and integrate
the preflight presentation model into the main window.

## Chosen UX

A compact, read-only **document-quality section** inside the existing window
(implementation plan §7: "compact pre-conversion section", "report-preview
surface").  No dialog, no wizard, no extra confirmation and no new modal step
is introduced, so the accepted single-file workflow and its frozen Tab chain
are preserved.

| Element | Behaviour |
|---|---|
| `preflightArea` | Standard-layout container, hidden while there is nothing to present. |
| `preflightCaptionLabel` | Visible wording: `Document quality`. |
| `preflightSummaryLabel` | The retained authoritative wording (or the derived counts sentence). |
| `preflightList` | One row per finding: marker + severity word + wording + code; keyboard reachable; accessible name set. |

## Wiring

* populated from `preflight_from_result(result)` in the accepted single-file
  completion path (both the retained-batch-of-one path and the defensive
  no-batch path);
* cleared on every selection change, reset, and item-level worker failure, so
  findings never leak from one document to the next;
* a multi-file batch leaves the section hidden and keeps each file's findings
  in its own per-file report (WP-DI-05);
* `_apply_preflight()` is part of the single `_apply_state()` write path.

## Accepted product rules preserved

* warnings do not block and do not change the outcome (`SUCCESS_WITH_WARNING`);
* existing fatal errors keep their meaning (`FAILED`, no output action);
* severity is textual (marker + word), never colour-only;
* the window reads no raw diagnostic field and composes no finding wording
  (guarded by AST tests).

## Verification

```text
pytest md_converter/tests/gui/test_document_intelligence_ux.py  -> 13 passed
pytest md_converter/tests/gui                                   -> PASS (no regression)
ruff / black / isort on md_converter/gui + md_converter/tests/gui -> clean
```

Covered: hidden before any conversion; hidden for a clean document; findings
listed with counts and severity wording after a warning conversion; error
findings presented; warning-only conversion still produces and offers the
artifact; fatal errors offer no output action; selection change clears the
findings; re-conversion does not duplicate rows; accessible identities;
keyboard reachability and Tab behaviour; textual severity; standard layout.
