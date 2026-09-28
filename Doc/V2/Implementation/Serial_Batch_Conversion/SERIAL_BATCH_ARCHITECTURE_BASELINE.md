# WP-SBC-01 — Serial Batch Conversion Architecture Baseline

**Document Type:** Architecture / Contract Baseline
**Feature:** Serial Batch Conversion
**Inputs:** `Serial_Batch_Conversion_Product_Specification.md`,
`Serial_Batch_Conversion_Implementation_Plan.md`
**Status:** Frozen for the SBC work packages
**Change classification:** G1 — controlled feature work (no G2 item is opened)

## 1. Authority and SPEC references

`CANONICAL_SPEC.md` (FROZEN 1.1) covers the compiler contract; it does not
mention the desktop GUI. This work package therefore touches no canonical
entry, and it is bound by the entries that constrain any additive layer:

| Reference | How it constrains this feature |
|---|---|
| SPEC-GOAL-002 | The pipeline is never bypassed: every file is still compiled by the accepted single-file path. |
| SPEC-GOAL-003 | Determinism: the batch order is the list order and the summary is derived from the recorded results. |
| SPEC-GOAL-006 / SPEC-INV-012 | Only the modules named in this baseline are modified. |
| SPEC-ARCH-007 | Dependency direction stays one-way; the batch layer calls the application service, never the compiler stages. |
| SPEC-INV-005 | Parser → AST → Pipeline → Renderer → Post-Processor is untouched. |

Two references carried over and re-confirmed after the work packages ran:

* `ConversionService` / `ConversionRequest` / `ConversionResult` semantics:
  **unchanged** (no G2).
* Canonical Core, QA, Golden, CLI and public API: **unchanged** (no G2).

## 2. Inspection performed

| Area | Modules inspected | Finding |
|---|---|---|
| Window / state | `md_converter/gui/main_window.py`, `state.py` | One state model (`EMPTY/READY/CONVERTING/SUCCESS/SUCCESS_WITH_WARNING/FAILED`) drives widget enablement from `STATE_EFFECTS`; `_apply_state()` is the single write path. |
| Worker | `md_converter/gui/worker.py` | One dedicated thread per job; `finished` reports the job outcome *before* the thread and references are released, so a chained job cannot start from it. |
| Result presentation | `presentation_model.py`, `result_mapping.py`, `result_details.py`, `presentation` property on the window | Result → wording/severity/eligibility already has exactly one authority. |
| Request construction | `request_builder.py` | One shared builder; DOCX naming stays in the application layer. |
| Selection | `file_picker.py`, `drop_zone.py` | Single-file dialog and single-file drop, both funnelling into `MainWindow.set_source_file`. |
| Output actions | `output_actions.py` | `ConversionResult.output_path` is the only path authority. |
| Application boundary | `conversion_service.py`, `conversion_request.py`, `conversion_result.py` | One file per call; no batch concept exists and none is required. |
| Existing verification | `tests/gui/*`, `tests/application/*`, P12-05/06/07 closure evidence | Established worker-lifecycle, close-policy, single-job and accessibility guards that the batch work must keep green. |

## 3. Frozen decisions

1. **Batch selection state** lives in the GUI, in a Qt-free value type
   (`md_converter/gui/batch.py`, `BatchSelection`), held by `MainWindow`.
   Order is insertion order, which is the execution order.
2. **Batch orchestration state** lives in the GUI as well (`BatchRun`, also in
   `batch.py`), held by `MainWindow.batch_run`; it never enters the application
   or Core layers.
3. **Completion triggers the next job** through a new worker observation
   point: `GuiWorker.idle` is emitted at the end of `_on_thread_finished`
   (thread exited, references released), and `MainWindow._on_worker_idle()`
   asks `BatchRun.next_source()` for the next file.
4. **Worker lifecycle** is reused unchanged: still exactly one private thread
   per job, no pool, no queue, no cancellation. The only addition is the
   additive `idle` signal; the safety model does not change.
5. **Per-file results** are represented by `BatchItem` (source path, batch
   status, retained `ConversionResult` *or* retained worker failure evidence,
   and the derived `Presentation` from the presentation model).
6. **The batch summary is derived** from the item statuses
   (`processed/succeeded/warnings/failed/pending`); no independently editable
   counter exists, so counts cannot drift.
7. **Single-file compatibility** is preserved: a one-file selection keeps the
   accepted states, surfaces and wording. The batch list appears only for two
   or more files, and a multi-file batch returns the workflow to `READY`
   through `GuiStateModel.complete_batch()` (no new `GuiState` member).
8. **One output directory per batch**: the existing per-request
   `output_dir` configuration intent is used for every item. No naming, path
   or overwrite semantics are added. The batch-level "Open Output Folder"
   action uses `BatchRun.output_directory` (the containing folder of the first
   retained produced document); it is never guessed.
9. **Duplicate detection** is path-based: the identity is the absolute,
   case-normalised text of the path (`os.path.normcase(resolve(...))`). No
   content hashing is introduced.
10. **Batch-fatal** means only: the next job could not be started
    (`GuiWorker.start` refused, or no request could be built for a validated
    source), or the serial invariant was violated. It aborts the remaining
    files, keeps the recorded results and surfaces one bounded notice. An
    ordinary per-file failure — including an item-level worker failure — is
    recorded and the batch continues.

## 4. Architecture delta

```text
MainWindow
  ├── BatchSelection        (ordered, duplicate-free selection)   SBC-02
  ├── BatchRun              (serial sequence, per-item results)   SBC-03
  ├── GuiWorker.idle        (reusable boundary signal)             SBC-04
  ├── batch summary + report (derived presentation)                SBC-05
  └── unchanged: ConversionService -> Canonical Core -> DOCX
```

Files added: `md_converter/gui/batch.py`, `md_converter/gui/batch_report.py`.
Files extended: `md_converter/gui/main_window.py`, `worker.py`, `state.py`,
`file_picker.py`, `drop_zone.py`, `output_actions.py`.
Untouched: `md_converter/core` (absent), `parser/`, `pipeline/`, `renderer/`,
`services/`, `quality_gate.py`, `application/*`, Golden baselines, CLI, theme
files, packaging.

## 5. Authorized verification-contract updates

Two accepted GUI guards encoded the *pre-batch* product decision and are
superseded by the frozen product specification; both updates are recorded in
the closure evidence:

* `tests/gui/test_drag_and_drop.py` — "multiple files are rejected" becomes
  "a multi-file payload adds valid unique files" (product specification §26).
* the `file_picker` / window dialog seam — `ask_for_markdown_source` becomes
  `ask_for_markdown_sources` (multi-selection), and the picker/drop both
  accumulate into the selection instead of replacing it.

`tests/gui/test_report_view.py` explicitly enumerates the bounded dialog
modules and is updated to include the new batch report surface.

## 6. Exit criteria

- No Core change is required — confirmed (no canonical module touched).
- No `ConversionService` semantic change is required — confirmed.
- Serial execution architecture identified — `BatchRun` + `GuiWorker.idle`.
- Worker reuse strategy identified — unchanged worker, additive `idle` signal.
- State model stays small — one added transition, no new `GuiState` member.
- Files to be touched are bounded to the GUI layer — as listed in §4.

## 7. Mandatory stop conditions

None was met. In particular: no request/result semantic change, no QA or
Golden change, no output-naming change, no CLI/public API change, no
concurrency, and no worker-lifecycle redesign.
