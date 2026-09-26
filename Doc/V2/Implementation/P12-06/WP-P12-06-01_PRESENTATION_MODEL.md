# WP-P12-06-01 — Error / Warning Presentation Model

## Objective
Create a thin Qt-free adapter that converts retained `ConversionResult` or `JobFailure` into structured GUI presentation data. No final dialogs yet.

## Authorized Scope
Preferred: `md_converter/gui/presentation_model.py` and focused tests.

## Required
- SUCCESS, SUCCESS_WITH_WARNING, FAILED, JobFailure mappings.
- Concise title/summary/severity/outcome, optional detail flag, output availability, warning/error counts if directly derivable.
- Preserve original evidence unchanged.
- Qt-free; no Core imports.

## Forbidden
No new error codes, QA reinterpretation, result mutation, fake ConversionResult from JobFailure, dialogs, or conversion-flow changes.

## Tests
Mapping, evidence immutability, deterministic counts, Qt-free boundary, no Core imports.

## Acceptance
One presentation boundary; evidence preserved; tests PASS; Core/Golden/CLI changes = 0.

## Stop
STOP if presentation requires changing application/Core semantics.
