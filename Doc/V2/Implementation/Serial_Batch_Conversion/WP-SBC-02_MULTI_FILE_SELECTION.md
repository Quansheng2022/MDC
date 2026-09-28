# WP-SBC-02 — Multi-file Selection & Batch List UX

**Change classification:** G1
**References:** product specification §8.1/§8.2/§9/§26/§33, `SERIAL_BATCH_ARCHITECTURE_BASELINE.md` §3
**Scope:** GUI selection and presentation only — no execution.

## Implemented

| Element | Detail |
|---|---|
| Multi-file picker | `file_picker.ask_for_markdown_sources()` uses the standard multi-selection dialog; the filter stays `Markdown Files (*.md)`. |
| Multi-file drop | `DropZone.sources_dropped` accepts a payload containing at least one Markdown file and forwards every local path. |
| Shared validation | The picker, the drop area and the selection all use `file_picker.validate_markdown_source` (resolved dynamically through `MainWindow._validate_source`), so one rule applies. |
| Duplicate filtering | `BatchSelection` keys on the absolute, case-normalised path (`source_identity`); no content hashing. |
| Selected-file list | `batchList` shows the files in execution order, with the containing folder added when two entries share a name and the full path as tooltip. |
| List operations | `Remove` (highlighted entries) and `Clear` (whole list). |
| One-file compatibility | The list surface is hidden for zero or one file; the accepted single-file surface and wording are unchanged. |
| Convert wording | `Convert` for one file, `Convert N Files` for two or more. |
| Bounded feedback | `noticeLabel` reports "Added …", "… already in the list." and "Skipped N items that are not Markdown files." |

## Superseded guards (recorded)

* `tests/gui/test_drag_and_drop.py::test_multiple_files_are_rejected` encoded
  the pre-batch decision and is replaced by
  `test_multiple_markdown_files_are_added_as_a_batch`,
  `test_mixed_payload_keeps_the_valid_files` and
  `test_second_drop_adds_to_the_existing_batch`.
* The picker selected one file and replaced the selection; it now answers with
  the whole selection and adds to the batch. The affected guard
  (`test_reselect_updates_source`) is replaced by
  `test_reselect_adds_the_file_to_the_batch` plus
  `test_duplicate_picker_selection_is_added_once`.

## Verification

`md_converter/tests/gui/test_batch_selection_ux.py` (16 tests): empty /
single / multi surface, ordering, duplicate-name context, tooltips, Remove,
Clear, notice lifecycle, invalid payloads, mutation lock during
`CONVERTING`, accessible names, keyboard reachability, wording.

`md_converter/tests/gui/test_batch_model.py` (selection section): order,
path-based duplicate detection, rejection, notice wording, remove/clear.

## Acceptance

Multi-file selection PASS · multi-file drop PASS · duplicate handling PASS ·
remove PASS · clear PASS · single-file compatibility PASS · accessibility PASS.
