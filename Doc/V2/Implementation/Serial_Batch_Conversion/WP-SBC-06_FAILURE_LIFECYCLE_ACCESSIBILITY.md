# WP-SBC-06 — Failure / Lifecycle / Accessibility Hardening

**Change classification:** G1
**References:** product specification §15/§18/§20/§30/§31,
`SERIAL_BATCH_ARCHITECTURE_BASELINE.md` §3

## Failure matrix (verified behaviour)

| Case | Behaviour | Evidence |
|---|---|---|
| Unsupported / non-Markdown item in the selection | Never enters the list; bounded notice; the valid entries are kept. | `test_mixed_payload_keeps_the_valid_files`, `test_invalid_drop_does_not_change_the_batch`, `test_notice_appears_for_skipped_items_and_clears_on_a_new_selection` |
| Duplicate source path | Filtered by path identity; notice "already in the list". | `test_duplicate_picker_selection_is_added_once`, `test_second_drop_adds_to_the_existing_batch`, model tests |
| Missing source after selection | The service returns a `FAILED` result (input error); the item is recorded and the batch continues. | `test_failure_in_the_middle_continues_and_is_summarised` |
| Conversion failure | `FAILED` item, no output claimed, remaining files continue. | same test |
| Warning result | `SUCCESS_WITH_WARNING` item, still a produced document, batch continues. | `test_warning_continuation` |
| Worker-level failure on one file | Recorded as an item-level infrastructure failure; the batch continues (the boundary itself is proven reusable). | `test_worker_level_failure_continues_the_batch` |
| Output collision / locked output | No batch-only rule exists: existing single-file output semantics apply per item, and an item failure is recorded like any other. | design (no override, no rename, no retry) + `request_builder` unchanged |
| Batch-level infrastructure failure | `BatchRun.abort(reason)` stops the remaining files, keeps the results, shows the bounded notice and reports the remaining rows as `NOT PROCESSED`. | `test_open_output_folder_is_unavailable_without_a_document`, model `test_abort_preserves_results_and_reports_remaining_files`, `test_details_action_is_disabled_without_evidence` |
| Missing produced artifact | `Open Output Folder` is disabled when nothing was produced; a vanished artifact fails safely through the shared action helper. | `test_open_output_folder_is_unavailable_without_a_document` |
| Close during a batch | Refused until the whole batch finished and the worker is idle. | `test_close_is_blocked_during_a_batch_and_allowed_after` |
| Stale selection / cleared list | `Clear` fully resets the workflow; a new selection drops the previous run and summary. | `test_clear_empties_the_selection`, `test_new_selection_clears_the_previous_batch_summary` |

No automatic retry, no auto-rename, no batch-only overwrite rule was
introduced (product specification §18).

## Accessibility

* The list, Remove, Clear, Convert, the batch actions and the report surface
  are keyboard reachable; the tab order includes the new controls and skips
  hidden ones.
* Every outcome carries explicit wording, never colour alone (`marker + word`
  in the list, textual progress and summary, text status in the report).
* The new controls carry accessible names; no stylesheet, palette or colour is
  used (the accepted "no colour-only signal" guard remains green).

Evidence: `test_batch_controls_carry_accessible_names`,
`test_batch_list_and_operations_are_keyboard_reachable`,
`test_wording_has_no_technical_jargon`,
`test_report_surface_is_keyboard_reachable`,
`test_status_is_never_conveyed_by_color_alone`,
`test_gui_does_not_style_by_color`,
`test_accessible_names_match_the_visible_wording`.

## High-DPI and real-platform smoke

The bounded High-DPI smoke (`test_high_dpi_smoke_keeps_primary_controls_usable`,
`QT_SCALE_FACTOR=2` in a real Qt process) and the minimum-size layout guard
remain green with the new surfaces present but hidden for an empty selection.
No packaging or manifest change was required.

## Acceptance

Failure continuation PASS · warning continuation PASS · batch-fatal handling
PASS · accessibility PASS · single-file regression PASS · lifecycle PASS.
