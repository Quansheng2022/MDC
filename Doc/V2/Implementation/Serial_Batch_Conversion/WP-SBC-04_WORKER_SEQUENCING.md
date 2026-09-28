# WP-SBC-04 — Worker Sequencing / Runtime Integration

**Change classification:** G1
**References:** product specification §11/§13/§14/§20, `SERIAL_BATCH_ARCHITECTURE_BASELINE.md` §3
**Scope:** wiring the orchestrator into the existing worker/service path.

## Execution path (unchanged authority)

```text
source
  -> MainWindow._start_batch_job()
  -> build_conversion_request()            (shared builder, unchanged)
  -> GuiWorker.start(ConversionService.convert(request))
  -> ConversionService -> Canonical Core -> one document per source
  -> GuiWorker.succeeded / failed          -> BatchRun.record_*()
  -> GuiWorker.idle                        -> BatchRun.next_source()
```

No second conversion engine, no parallel worker pool, no retry, no
cancellation.

## The one worker-boundary addition

`GuiWorker.finished` is emitted while the job's thread is still cleaning up
(`is_running` is still `True`), so a chained job cannot start from it.
`GuiWorker.idle` is emitted at the end of `_on_thread_finished`, after
`is_running` is `False` and both job references are released. Serial chaining
runs from `idle`, which is why the one-active-conversion invariant does not
depend on event-ordering luck. The worker safety model itself (one private
thread per job, no `terminate()`, deferred deletion before reference release)
is untouched.

## Behaviour

* the GUI stays responsive: every conversion runs off the GUI thread;
* exactly one worker job is active at any moment;
* a job outcome records one item, and the next file starts only from `idle`;
* an ordinary failure (application `FAILED` or item-level worker failure)
  continues the batch;
* `Convert`, the file list, Remove/Clear and Change Output are disabled for the
  whole batch, reusing the existing `CONVERTING` state effects;
* the close policy is unchanged and covers the whole batch.

## Verification

`md_converter/tests/gui/test_batch_execution.py`: three-file serial batch,
peak concurrency measured inside `ConversionService.convert` (must be 1),
execution off the GUI thread, order after a removal, progress line, per-file
status, mid-batch failure continuation, warning continuation, worker-level
failure continuation, second batch after completion, repeated batches
releasing every thread, close blocked during the batch and allowed after,
single-file regression.

`md_converter/tests/gui/test_worker.py`: `idle` is emitted after the references
are released (and after `finished`), and a next job may be started from it.

`md_converter/tests/gui/test_lifecycle.py` and `test_conversion_slice.py` remain
green unchanged, which is the single-file lifecycle regression guard.

## Acceptance

Worker lifecycle PASS · no duplicate workers · no stale thread references ·
GUI responsiveness PASS · close protection PASS · Core/ConversionService drift
= 0.
