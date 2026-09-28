# Serial Batch Conversion — Closure Evidence (WP-SBC-07)

**Feature:** Serial Batch Conversion
**Baselines:** `Serial_Batch_Conversion_Product_Specification.md` (frozen
product decisions) and `SERIAL_BATCH_ARCHITECTURE_BASELINE.md` (WP-SBC-01)
**Change classification:** G1 (additive GUI orchestration; no G2 item opened)
**Status:** Implemented and verified; recommended for the next release
candidate only after the open items in §8 are dispositioned.

## 1. Deliverable chain

| WP | Deliverable | Commit |
|---|---|---|
| SBC-01 | Architecture / contract baseline (`SERIAL_BATCH_ARCHITECTURE_BASELINE.md`) | see `git log` — recorded in §9 |
| SBC-02 | Multi-file selection & batch list UX (`WP-SBC-02_*`) | see `git log` — recorded in §9 |
| SBC-03 | Batch model & serial orchestrator (`WP-SBC-03_*`) | same bounded delivery commit |
| SBC-04 | Worker sequencing / runtime integration (`WP-SBC-04_*`) | same bounded delivery commit |
| SBC-05 | Progress / results / report (`WP-SBC-05_*`) | same bounded delivery commit |
| SBC-06 | Failure / lifecycle / accessibility hardening (`WP-SBC-06_*`) | same bounded delivery commit |
| SBC-07 | This closure evidence | see `git log` — recorded in §9 |

SBC-02…SBC-06 landed as one bounded delivery because the window integration is a
single cohesive change (the selection surface, the orchestrator wiring, the
progress/summary surfaces and their tests cannot be split into independently
green commits without inventing intermediate states). Each WP keeps its own
scope, verification and evidence above.

## 2. Files changed

Added:

```text
md_converter/gui/batch.py                    (Qt-free selection + serial run model)
md_converter/gui/batch_report.py             (lightweight batch report surface)
md_converter/tests/gui/test_batch_model.py
md_converter/tests/gui/test_batch_selection_ux.py
md_converter/tests/gui/test_batch_execution.py
md_converter/tests/gui/test_batch_report.py
```

Extended:

```text
md_converter/gui/main_window.py     (selection surface, batch wiring, summary)
md_converter/gui/worker.py          (additive "idle" signal)
md_converter/gui/state.py           (complete_batch(): CONVERTING -> READY)
md_converter/gui/file_picker.py     (multi-selection dialog)
md_converter/gui/drop_zone.py       (multi-file payload acceptance)
md_converter/gui/output_actions.py  (open_directory for the batch folder action)
md_converter/tests/gui/test_worker.py, test_drag_and_drop.py, test_file_picker.py,
                            test_output_selection.py, test_preferences.py,
                            test_accessibility_window.py, test_report_view.py
Doc/V2/Implementation/Serial_Batch_Conversion/*  (this package)
```

Explicitly untouched: `md_converter/application/*` (request/result/service),
`parser/`, `pipeline/`, `renderer/`, `services/`, `quality_gate.py`, Golden
baselines, `cli.py`, themes, packaging.

## 3. Tests and checks

| Check | Result |
|---|---|
| `pytest md_converter/tests/gui` (whole GUI suite) | PASS |
| `pytest md_converter/tests/gui md_converter/tests/application` | PASS |
| Focused batch suites (66 new tests: 25 model + 16 selection UX + 18 execution + 7 report) | PASS |
| `tests/gui/test_worker.py` including the two new `idle` tests | PASS |
| `pytest md_converter/tests` (full suite) | 2 failures, both pre-existing and unrelated — see §8 |
| `ruff check md_converter/gui md_converter/tests/gui` | clean |
| `black --check md_converter/gui md_converter/tests/gui` | clean |
| `isort --check-only md_converter/gui md_converter/tests/gui` | clean |

## 4. Real execution evidence

The execution tests are not mocks: they drive real widgets through the real
worker into the real `ConversionService` and the Canonical Core, and assert
real artifacts on disk.

| Assertion | Evidence |
|---|---|
| multi-file selection PASS | `test_multi_selection_shows_the_ordered_list` |
| multi-file drag/drop PASS | `test_multiple_markdown_files_are_added_as_a_batch` |
| duplicate handling PASS | `test_duplicate_picker_selection_is_added_once`, `test_second_drop_adds_to_the_existing_batch` |
| serial execution PASS | `test_three_file_batch_produces_one_document_per_source` |
| active conversions ≤ 1 | `test_at_most_one_conversion_is_active` (peak measured inside `ConversionService.convert`) |
| continue-after-failure PASS | `test_failure_in_the_middle_continues_and_is_summarised` |
| warning continuation PASS | `test_warning_continuation` |
| per-file status PASS | `test_per_file_status_is_shown_in_the_list` |
| batch progress PASS | `test_progress_line_reports_position_and_current_file` |
| batch summary PASS | `test_failure_in_the_middle_continues_and_is_summarised`, model summary tests |
| batch report PASS | `test_batch_report_lists_every_source`, `test_batch_report.py` |
| one document per successful source | `test_three_file_batch_produces_one_document_per_source` (3 distinct artifacts, each in the chosen folder, each `PK…`) |
| single-file compatibility PASS | `test_single_file_selection_keeps_the_single_file_surface` |
| GUI responsiveness PASS | every conversion runs off the GUI thread; peak concurrency 1; the window keeps processing events during the batch |
| worker lifecycle PASS | `test_close_is_blocked_during_a_batch_and_allowed_after`, `test_batch_leaves_no_worker_or_thread_reference` |
| privacy/locality PASS | no new network capability, no account, no upload, no telemetry (no new imports outside the GUI/application boundary) |

## 5. Drift results

```text
ConversionService semantic drift = 0
ConversionRequest / ConversionResult semantic drift = 0
Core drift = 0
Canonical drift = 0            (CANONICAL_SPEC.md covers the compiler; no entry touched)
QA drift = 0
Golden drift = 0
CLI / public API breaking drift = 0
output naming / path semantics drift = 0
introduced failures = 0
```

Architecture guards that stayed green unchanged: no Core import from the GUI,
no Markdown/DOCX naming logic in the GUI, no threading outside `worker.py`, no
colour-only status signal, no new configurable shortcut, no second report
implementation.

## 6. Superseded guards (authorized test-contract updates)

| Guard | Before | After | Authority |
|---|---|---|---|
| `test_drag_and_drop.py::test_multiple_files_are_rejected` | multi-file drop rejected | multi-file drop adds valid unique files | product specification §26 |
| `test_file_picker.py::test_reselect_updates_source` | second selection replaces the first | second selection adds to the batch | product specification §9 |
| `test_report_view.py::test_only_one_report_surface_exists` | three dialog modules | four (adds the batch report surface) | product specification §22/§23 |

`test_gui_state.py::test_workflow_states_are_unchanged` and
`test_main_window_polish.py::test_workflow_states_are_unchanged` still pin the
frozen state list; no `GuiState` member was added.

## 7. Definition of Done

```text
multiple MD selection works            PASS
multiple MD drag/drop works            PASS
duplicate handling works               PASS
serial ordering deterministic          PASS
active conversions <= 1                PASS
one file failure does not stop the rest PASS
warnings do not stop the batch         PASS
one DOCX per successful MD             PASS
existing output semantics preserved    PASS
batch progress correct                 PASS
per-file statuses correct              PASS
batch summary correct                  PASS
batch report correct                   PASS
Open Output Folder correct             PASS
single-file workflow preserved         PASS
GUI remains responsive                 PASS
worker lifecycle remains safe          PASS
privacy/locality unchanged             PASS
```

## 8. Open items and limitations

1. **Pre-existing, unrelated failures.** `pytest md_converter/tests` reports two
   failures in `test_packaging_metadata.py`
   (`test_pkg_documented_extras_exist_in_metadata`,
   `test_pkg_readme_has_no_legacy_packaging_references`). They are caused by the
   working tree's already-modified `README.md` (the documented `.[mermaid]` /
   `.[windows]` extras and the `[project.entry-points` section were removed by
   that rewrite), not by this feature. Reported, not modified (SPEC-INV-012).
2. **Pre-existing environment noise.** The full-suite stderr contains a
   `Windows fatal exception: code 0x800706be` dump from
   `post_processor._update_toc_with_word` (Word COM automation, RPC call
   failed) during `test_public_api_convert.py`. It is unrelated to this feature
   and does not fail a test.
3. **No native-display manual smoke.** Verification ran the offscreen Qt
   platform with real widgets, real worker threads, the real service and real
   artifacts, plus the existing High-DPI smoke subprocess. A human packaged-GUI
   smoke (installer/executable) is the remaining step before a release
   candidate, together with a small extension of
   `tools/packaging/windows_gui_smoke.ps1` for a multi-file batch
   (out of scope here: the packaged smoke still drives the single-file flow,
   which this feature preserves unchanged).
4. **Single-file removal affordance.** For exactly one selected file the batch
   list is hidden (frozen single-file surface), so `Remove`/`Clear` are
   available only once two or more files are selected. This preserves the
   accepted single-file workflow; the product specification does not require a
   single-file clear control.

## 9. Commit chain

```text
3f37470  SBC-01     freeze serial batch architecture
39dd391  SBC-02..06 implement serial batch conversion
(this commit)  SBC-07  close serial batch conversion implementation
```

Only the files listed in §2 were staged (`git diff --cached --name-status` was
inspected before each commit). The working tree's pre-existing modifications
(`.gitignore`, `README.md`, `md_converter/cli.py`) and its untracked files were
left untouched, exactly as the plan's Git safety rules require.

## 10. Final recommendation

The feature meets the frozen product decisions with additive orchestration only:
one ordered selection, one serial run, one document per source, continue on
ordinary failure, derived summary, lightweight report, unchanged
`ConversionService`/Core/QA/Golden semantics. Drift is zero across every
protected surface. Recommendation: accept the implementation; run the packaged
GUI multi-file smoke (item §8.3) as part of the next release-candidate gate, and
disposition the pre-existing README/packaging failures (item §8.1) separately.
