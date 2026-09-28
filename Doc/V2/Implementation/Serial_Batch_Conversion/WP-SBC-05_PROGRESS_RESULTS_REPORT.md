# WP-SBC-05 — Batch Progress, Results & Report

**Change classification:** G1 (one bounded G0-level surface: the report dialog)
**References:** product specification §8.3/§8.4/§21/§22/§23/§24,
`SERIAL_BATCH_ARCHITECTURE_BASELINE.md` §3

## Implemented

| Surface | Content | Source of truth |
|---|---|---|
| Progress line | `Converting 2 of 3 — B.md` in `statusLabel` while the batch runs. | `BatchRun.progress_text()` |
| Per-file status | Every list row shows a marker *and* a status word (`✓ a.md — succeeded`, `⚠ b.md — warning`, `✗ c.md — failed`). | `BatchItem.marker` / `state_word` |
| Completion summary | `Batch complete` + `N files processed` + `x succeeded · y warning · z failed`, plus `Open Output Folder` and `View Batch Report`. | `BatchRun.summary_text()` |
| Batch report | Read-only aggregate report and per-file rows; a row's `Details...` opens the existing single report surface. | `BatchRun.report_text()`, `result_details.show_result_details` |
| Output actions | Batch-level `Open Output Folder` only. No ambiguous batch-level `Open Document`; per-file documents remain reachable through `Details...`. | `BatchRun.output_directory` (parent of the first retained produced document) |

## Rules kept

* The summary counts are derived from item statuses, never maintained
  separately.
* QA diagnostics are never recomputed or reinterpreted: the report reuses the
  retained per-item presentation summaries.
* The output folder is authoritative; a batch that produced nothing disables
  the folder action instead of guessing a path.
* A one-file batch keeps the accepted single-file completion surface and shows
  no batch summary.

## Verification

`md_converter/tests/gui/test_batch_execution.py`: progress line with position
and file name, per-file status rows, summary counts after all-success and after
partial failure, report aggregation, `View Batch Report` action, Open Output
Folder success and fail-closed case.

`md_converter/tests/gui/test_batch_report.py` (7 tests): aggregate text equals
`BatchRun.report_text()`, summary line, per-row text/tooltip, per-row Details
reuses the single report surface, Details disabled without evidence,
`NOT PROCESSED` rows after an abort, copy-to-clipboard, Escape/Close, keyboard
and accessible names.

`md_converter/tests/gui/test_batch_model.py`: summary derivation, report
content, no output claimed for a failure.

## Acceptance

Batch progress PASS · per-file status PASS · batch summary PASS · batch report
PASS · Open Output Folder PASS · no second QA logic PASS.
