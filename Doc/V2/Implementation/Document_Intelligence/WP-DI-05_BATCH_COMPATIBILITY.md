# WP-DI-05 — Batch Compatibility / Result Integration

**Program:** Document Intelligence Upgrade
**Baseline:** `DOCUMENT_INTELLIGENCE_ARCHITECTURE_BASELINE.md` (WP-DI-01)
**Change classification:** G1 — verification of an existing boundary

## Scope

Verify (and where needed bound) that Document Intelligence stays compatible with
Serial Batch Conversion: independent per-file reports, a summary-only batch
report, no batch-only diagnostic semantics and no cross-file contamination.

## Findings and behaviour

| Requirement | Implementation |
|---|---|
| Independent report per file | Each `BatchItem` retains its own `ConversionResult` / failure evidence and its own `Presentation`; the per-row `Details...` action opens the single report surface for that item. |
| Batch Report remains summary-only | `BatchRun.report_text()` aggregates status, source, produced document and the presentation summary; it renders no quality findings. |
| No batch-only diagnostic semantics | The batch layer imports only the application result model and the presentation model; it never reads diagnostics. |
| No cross-file contamination | The document-quality section is hidden for a multi-file batch and cleared on every selection change. |
| Mixed result consistency | Success / warning / failure items keep their own status, counts and findings; the batch counts remain derived from the item statuses. |

No production code change was required beyond the wiring decision recorded in
WP-DI-03; this work package adds the verification that pins the boundary.

## Verification

```text
pytest md_converter/tests/gui/test_document_intelligence_batch.py  -> 7 passed
pytest md_converter/tests/gui/test_batch_execution.py              -> PASS (unchanged)
pytest md_converter/tests/gui/test_batch_report.py                 -> PASS (unchanged)
```

Covered: aggregate report carries no findings; aggregate counts stay derived;
per-file ownership (warning does not leak into a clean file's report); mixed
success/warning/failure ownership; no single-file quality panel for a batch;
`Details...` opens the owning file's evidence; an item without retained
evidence offers no details affordance.
