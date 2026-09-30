# WP-R2V02-02 — Real Serial Batch Runtime

**Program:** R2-V02 — Packaged Multi-file Runtime Verification (P12-20)
**Work package:** R2V02-02
**Change classification:** G1 — verification only (no product source change)
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — `SPEC-GOAL-003`,
`SPEC-INV-001`, `SPEC-INV-003`, `SPEC-ARCH-007`
**Raw machine record:** `WP-R2V02-02_RESULT.json`
**Status:** PASS

## 1. Scope

Drive one real four-file Serial Batch through the installed packaged GUI and
observe: queue order, strict serial execution, failure isolation, per-file
result, output count and naming, derived summary counts, return to idle, and
`Open Output Folder`. No production instrumentation was added.

## 2. Artifact / files

| Item | Value |
|---|---|
| Installed executable | `%LOCALAPPDATA%\Programs\MD_Converter\MD_Converter.exe` (SHA-256 `68524527…E3021`) |
| Launch mode | detached windowed GUI launch (no inherited standard handles) + sanitized environment, neutral cwd `%TEMP%\mdc_r2v02_wp02_20260930_155602\cwd` |
| Output profile in force | `Professional Report` (canonical default; no override) |
| Queue (selection order) | `01_english.md`, `02_wide_table_figure.md`, `03_failure.md` (deliberate empty source), `04_after_failure.md` |
| Produced documents | `01_english.docx` 29 442 B, `Wide_Table_Report.docx` 31 433 B, `04_after_failure.docx` 29 352 B |
| Evidence tooling | `Verification/mdc_r2v02_verify.ps1 -Phase WP02`, `Verification/make_fixtures.py` |

The documents were selected one at a time through the product's own file dialog
(the picker appends to the ordered selection), and the batch was started with
the product's own primary action.

## 3. Verification result

| Check | Result | Measurement |
|---|---|---|
| installed packaged GUI launches | PASS | main window `MD Converter` visible |
| four files accepted by the real file dialog | PASS | 4 of 4 dialogs accepted a source |
| queue order preserved | PASS | list rows before the run: `01_english.md` / `02_wide_table_figure.md` / `03_failure.md` / `04_after_failure.md` |
| batch surface hidden before the run | PASS | batch summary visible = False |
| batch starts from the product action | PASS | primary action enabled, clicked |
| batch completes and returns to idle | PASS | `BATCH_COMPLETE` after 10.7 s; the primary action is enabled again (state back to `READY`) |
| at most one converting item | PASS | maximum items observed in `converting` state in any of the 57 samples = 1 |
| strict serial prefix order | PASS | samples where a later source was terminal before an earlier one finished = 0 (observed states: `pending`, `converting`, `succeeded`, `failed`) |
| batch report opens | PASS | `View Batch Report` dialog opened |
| summary counts are consistent with per-file results | PASS | `Batch complete — 4 files processed · 3 succeeded · 0 warnings · 1 failed` |
| per-file results and order | PASS | `✓ 01_english.md — succeeded`, `✓ 02_wide_table_figure.md — succeeded`, `✗ 03_failure.md — failed`, `✓ 04_after_failure.md — succeeded` |
| failure isolation | PASS | the source queued after the failure still converted |
| output count and naming | PASS | `01_english.docx`, `Wide_Table_Report.docx` (from the frontmatter title, sanitized), `04_after_failure.docx` — exactly one document per successful source |
| failing item produces no output | PASS | no `03_failure.docx` |
| Open Output Folder | PASS | a new Explorer window titled `output - File Explorer` opened on the batch output directory |

## 4. New failures / classification

None. Introduced packaged failures in this work package: **0**. No
`PACKAGED_PRODUCT_REGRESSION`, `PACKAGING_BUILD_OR_INSTALL_DEFECT`, or
`ENVIRONMENT_FAILURE` was observed.

Bounded harness corrections applied while establishing the observations (no
product change): the queue observation now reads the batch-list rows exposed by
UI Automation instead of relying on status-suffixed rows, the summary check
derives its expectation from the reported per-file rows, UI Automation
enumeration is retried across transient tree rebuilds, and the product settings
restore reports `reg.exe`'s exit code rather than its stderr banner. The
completed run above is the clean re-run after those corrections.

Observation (not a defect): the primary action exposes the stable accessible
name `Convert` regardless of the queued file count, so the batch size is read
from the ordered queue list and the batch summary instead.

## 5. Protected drift result

| Protected contract | Result |
|---|---|
| Product source modified | No (0 files under `md_converter/` changed) |
| Strict serial batch semantics | Preserved (≤ 1 active item; prefix order intact) |
| Failure isolation | Preserved (item 4 converted after item 3 failed) |
| Output naming / path | Unchanged (`<sanitized title|stem>.docx` in the session output directory) |
| Result summary semantics | Unchanged (counts derived from recorded per-file statuses) |
| Product settings store | Restored from backup after the run (`reg exit=0`) |
| Drift | 0 |

## 6. Commit

Commit message: `R2V02-02 verify packaged serial batch runtime`
(exact-file staging: this evidence file, the raw result JSON, the harness
corrections above). The four-commit chain is listed with SHAs in
`R2_V02_CLOSURE_EVIDENCE.md`.

## 7. Status

PASS — the installed packaged application proves the principal multi-file
runtime workflow: real four-file batch, strict serial execution, failure
isolation, correct per-file results, counts, naming and output-folder action.
