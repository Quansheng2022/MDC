# WP-SBC-03 — Batch Model & Serial Orchestrator

**Change classification:** G1
**References:** product specification §10/§11/§15/§16/§19/§21, `SERIAL_BATCH_ARCHITECTURE_BASELINE.md` §3
**Scope:** the Qt-free orchestration model — no GUI wiring, no worker changes.

## Implemented

`md_converter/gui/batch.py` (Qt-free; unit-testable without a display server):

| Type | Responsibility |
|---|---|
| `BatchSelection` | Ordered, duplicate-free selection with injected validation; returns `BatchAddResult(added, duplicates, rejected)` and its bounded `notice_text()`. |
| `BatchItemStatus` | `PENDING` / `CONVERTING` plus four terminal members whose values mirror `PresentationOutcome` exactly (verified by a focused test). |
| `BatchItem` | Source path, status, retained `ConversionResult` *or* retained worker-failure evidence, and the derived `Presentation`; exposes `output_path`, `marker` and `state_word`. |
| `BatchRun` | The serial sequence: `begin()`, `record_result()`, `record_failure()`, `next_source()`, `abort(reason)`, plus the derived counts, progress line, summary and aggregate report. |
| `BatchRunError` | Raised when the serial invariant would be violated (a second job while one item is still converting). |

## Serial invariant

```text
begin()        -> item 1 CONVERTING
record_*()     -> item 1 terminal (FAILED / SUCCESS* / INFRASTRUCTURE_FAILURE)
next_source()  -> raises BatchRunError while an item is still CONVERTING
               -> otherwise item 2 CONVERTING
```

`active conversions <= 1` is therefore a property of the model, not of the
caller's timing.

## Failure policy encoded in the model

* `SUCCESS`, `SUCCESS_WITH_WARNING`, `FAILED` and an item-level infrastructure
  failure are all recorded and allow `next_source()`.
* Only `abort(reason)` stops the queue; remaining items stay `PENDING` and are
  reported as `NOT PROCESSED`. Already recorded results are preserved.
* Counts (`processed/succeeded/warnings/failed/pending`) are derived from item
  statuses on every read; no mutable counter exists.

## Verification

`md_converter/tests/gui/test_batch_model.py` (25 tests): ordering, duplicate
identities, rejection, notice wording, remove/clear, status↔presentation
mirror, marker/word coverage, `begin`/`next_source`/`record_*` invariants,
continue-after-failure, warning continuation, item-level infrastructure
failure, result-to-source attachment, no invented output path, empty run,
defensive de-duplication, abort semantics, derived summary, aggregate report,
Qt-freedom and Core independence.

## Acceptance

Serial execution PASS · maximum active conversions = 1 · deterministic order
PASS · continue-after-failure PASS · warning continuation PASS · summary
correctness PASS · no result/source mismatch PASS.
