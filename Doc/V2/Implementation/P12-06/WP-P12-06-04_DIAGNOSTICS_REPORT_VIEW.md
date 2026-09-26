# WP-P12-06-04 — Conversion Report / Diagnostics View

## Objective
Provide one read-only, on-demand diagnostics/report surface from retained evidence.

## Required Content
Status, output path, summary, warnings, errors, diagnostics/summary, quality-gate report, technical detail; JobFailure shown separately.

## UX
Prefer `Details...` → read-only dialog/view. Keep main window simple.

## Privacy
Local only. No upload/cloud/telemetry/support submission.

## Forbidden
No recomputation of diagnostics, no Core/QA calls, no reporting engine, no editable report, no PDF/HTML export.

## Tests
Report opens on demand, renders retained fields, handles missing optional data safely, JobFailure separate, read-only, no Core/QA calls.

## Stop
STOP if report requires recomputing or changing application/Core evidence.
