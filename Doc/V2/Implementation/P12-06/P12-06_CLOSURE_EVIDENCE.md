# P12-06 — Error / Diagnostics UX
## Closure Evidence (WP-P12-06-06)

**Status:** PASS — recommended for closure
**Phase:** P12-06 Error / Diagnostics UX
**Authority:** G1 (no G2 stop condition was hit)

---

## 1. Baselines

| Item | SHA |
| --- | --- |
| Product / phase starting baseline (P12-05 closure) | `068e2fcde0e3c3fc35b564f29381795d4f2899a1` |
| P12-06 specification baseline | `37de56e61e48f36383412409344954d800189f00` |
| WP-P12-06-01 Presentation Model closure | `df75392188226672efdabefa78a5aeadf1f75534` |
| WP-P12-06-02 Failure UX closure | `f9bc0483cc9fae43a0e51b43dfbac4fd27619fa1` |
| WP-P12-06-03 Warning UX closure | `0ea26fae1939649da8a3187b2c222fce0f319ea5` |
| WP-P12-06-04 Diagnostics Report closure | `39c0583d9379271cf74bb97dde1cdb64ae6f7817` |
| WP-P12-06-05 Output Actions closure | `b620f34ab718dd4e4e1f2af7c0a8b83de9cf270a` |
| WP-P12-06-06 Verification & Closure | this document; change set uncommitted at HEAD `b620f34` |

## 2. Scope of the phase change

WP-P12-06 changed only the GUI layer and its tests (plus its own work-package
documents):

| File | Delta |
| --- | --- |
| `md_converter/gui/presentation_model.py` | +341 (new) |
| `md_converter/gui/failure_details.py` | +38 (WP-02 surface; now compatibility alias) |
| `md_converter/gui/result_details.py` | +351 (new, unified report) |
| `md_converter/gui/output_actions.py` | +119 (new) |
| `md_converter/gui/main_window.py` | +273 / -4 |
| `md_converter/tests/gui/test_presentation_model.py` | +453 (new) |
| `md_converter/tests/gui/test_failure_ux.py` | +572 (new) |
| `md_converter/tests/gui/test_warning_ux.py` | +527 (new) |
| `md_converter/tests/gui/test_report_view.py` | +610 (new) |
| `md_converter/tests/gui/test_output_actions.py` | +544 (new) |

`git diff --name-only 068e2fc..HEAD` lists exactly these ten files plus the seven
P12-06 documents under `Doc/V2/Implementation/P12-06/`. No Core, parser,
pipeline, renderer, QA, Golden, CLI, configuration or packaging file was
touched.

## 3. Verification results

| Suite | Tests | Passed | Failed | Errors | Skipped |
| --- | --- | --- | --- | --- | --- |
| Full regression (`md_converter/tests`) | 689 | 687 | 2 | 0 | 0 |
| GUI suite (`md_converter/tests/gui`) | 265 | 265 | 0 | 0 | 0 |
| Application / P12-03 suite (`md_converter/tests/application`) | 72 | 72 | 0 | 0 | 0 |
| P12-06 focused (5 GUI test modules) | 90 | 90 | 0 | 0 | 0 |
| CLI / public API / config / QA / Golden / Acceptance | 182 | 182 | 0 | 0 | 0 |

P12-06 focused breakdown: presentation model 21, failure UX 18, warning UX 17,
unified report 18, output actions 16.

**Known pre-existing failures (classification B — approved baseline exception):**

1. `test_packaging_metadata.py::test_pkg_documented_extras_exist_in_metadata`
2. `test_packaging_metadata.py::test_pkg_readme_has_no_legacy_packaging_references`

Both are the two long-standing README / packaging-metadata failures already
recorded in the P12-06 specification baseline. They are unrelated to the GUI work
and were not fixed (the working-tree `README.md` modification that drives them is
pre-existing and untouched).

**P12-06 introduced required regression failures: 0.**

### Static checks

- `black --check`, `ruff check`, `isort --check-only` on the P12-06 file set:
  clean.
- Repository-wide lint baseline: `black` would reformat 24 files and `ruff`
  reports 43 findings, all in pre-existing parser / pipeline / renderer /
  services / test files outside the P12-06 change set (classification C —
  pre-existing baseline condition, deliberately not fixed in this phase).

## 4. Outcome verification (V1–V8)

**V1 — Presentation model.** `present_result` / `present_job_failure` map
SUCCESS → success, SUCCESS_WITH_WARNING → distinct success-with-warning, FAILED →
failure, `JobFailure` → infrastructure failure. The module is Qt-free (a
subprocess probe asserts importing it loads no Qt), the raw application status
enum is interpreted only in `result_mapping.py`, the retained result stays
authoritative, and no second result taxonomy exists.
Evidence: `test_presentation_model.py`, `test_result_mapping.py`.

**V2 — Failure UX.** FAILED and `JobFailure` present a clear status, a concise
summary and a bounded `Details...` affordance when evidence exists; both keep
their retained evidence object intact, never fabricate a `ConversionResult`, and
offer no output action. Recovery from FAILED / `JobFailure` to READY via a new
valid source, and reset to EMPTY, both clear the presentation while keeping the
evidence.
Evidence: `test_failure_ux.py`, `test_lifecycle.py`, `test_result_mapping.py`.

**V3 — Warning UX.** SUCCESS_WITH_WARNING keeps its own GUI state and status
text, is never routed through failure semantics, shows the presentation-model
summary, keeps warning evidence discoverable, keeps a valid artifact actionable,
and preserves `latest_result`. SUCCESS ≠ SUCCESS_WITH_WARNING ≠ FAILED is
asserted in state, status text and summary.
Evidence: `test_warning_ux.py` (incl. `test_success_warning_and_failed_stay_distinct`).

**V4 — Unified diagnostics report.** `result_details.py` is the single real
report implementation; `failure_details.py` is a class-free re-export alias
(asserted: exactly one `QDialog` subclass across `md_converter/gui`). The one
read-only surface renders warning, FAILED-result and `JobFailure` reports and
displays title, summary, status/outcome, output path, warnings, errors,
diagnostics, diagnostic summary, quality-gate report and technical detail —
each section only when meaningful evidence exists. No QA recomputation (retained
summary counts win over a recount), no Core call, no evidence mutation, and the
Copy action is clipboard-only.
Evidence: `test_report_view.py`.

**V5 — Output actions.** SUCCESS and SUCCESS_WITH_WARNING with an existing
artifact enable Open Document and Open Folder; FAILED (with or without a
artifact path) and `JobFailure` fail closed; a deleted artifact fails safely with
one concise local message, no fallback path, no reconstruction and no retry.
Path authority is `ConversionResult.output_path` only (asserted by object
identity at the click site); GUI-side filename/path reconstruction is 0; the
actions never trigger a conversion.
Evidence: `test_output_actions.py`.

**V6 — State / UI architecture.** `_apply_state(...)` remains the only writer of
workflow-driven widget state; the result area (`_apply_result_state`) and the
action area (`_apply_output_actions`) are both applied from it. P12-06 added no
second workflow-state mechanism and did not reopen P12-04 / P12-05 decisions.
Evidence: `test_gui_state.py`, `test_main_window.py`, `test_output_actions.py`.

**V7 — Architecture boundaries.** GUI direct `CompilerContext`, parser, AST,
pipeline, renderer and QA imports/calls = 0 (static import and call-target
guards over `md_converter/gui`); application-layer Qt dependency = 0; no second
conversion pipeline, diagnostics pipeline, result taxonomy or output-path
authority.
Evidence: `test_main_window.py::test_gui_layer_imports_no_conversion_core`,
`test_gui_bootstrap.py`, `test_report_view.py`, `test_output_actions.py`.

**V8 — Evidence preservation.** Across failure, warning, report and output-action
flows, `latest_result` and `latest_job_failure` keep object identity where
expected, and `to_dict()`, warnings, errors, diagnostics, `diagnostic_summary`,
`quality_gate_report` and `technical_detail` are unchanged. A `JobFailure` does
not replace a previously retained result.
Evidence: `test_failure_ux.py`, `test_warning_ux.py`, `test_report_view.py`,
`test_output_actions.py`.

## 5. Real Windows smoke (V9)

Bounded real-platform run (real Windows Qt platform, real `MainWindow`, real
OS launches; temporary workspace under `%TEMP%`). Harness script lives outside
the repository.

> **Open Document evidence was corrected after closure** — see §5.1. The original
> harness deleted its temporary artifact immediately after the launcher returned,
> which produced a Microsoft Word "file not found" message. The persistent-artifact
> re-verification below supersedes the original Open Document row.

| Check | Result |
| --- | --- |
| SUCCESS conversion state | `SUCCESS` |
| SUCCESS artifact on disk | `True` |
| SUCCESS: Open Document / Open Folder enabled | `True` / `True` |
| SUCCESS Details affordance | absent by design (plain-SUCCESS boundary) |
| Open Document (real platform launch) | `True` (see §5.1 for the corrected check) |
| Open Folder (real platform launch) | `True` |
| Missing artifact fails safely / no path substitution | `True` / `True` |
| SUCCESS_WITH_WARNING state | `SUCCESS_WITH_WARNING` |
| Warning actions enabled / artifact exists | `True` / `True` |
| Warning report opened and closed (real modal) | `True` |
| FAILED state, actions disabled, action call refused | `True` / `True` / `True` |
| Recovery to READY after failure | `READY` |
| JobFailure state | `FAILED` |
| JobFailure evidence distinct / previous result kept | `True` / `True` |
| JobFailure presentation is infrastructure failure | `True` |
| JobFailure actions disabled / report opened and closed | `True` / `True` |
| Window closed / worker idle after close | `True` / `True` |
| Smoke process exit | `0` (no native crash) |

Real-platform-tested: the whole list above (window, worker, conversions, modal
report open/close, OS launches, missing-artifact path, recovery, close).
Automated-only: the exhaustive outcome/eligibility matrix and all mocked-OS
launch checks in `test_output_actions.py`, plus the report content matrix in
`test_report_view.py`.

### 5.1 Evidence correction — persistent Open Document re-verification

The first smoke generated its DOCX in a `tempfile.mkdtemp(...)` workspace and
then deleted it (an explicit `artifact.unlink()` in the missing-artifact step)
immediately after `QDesktopServices.openUrl(...)` returned. Word starts
asynchronously, so it was handed a path whose file was already gone — hence the
observed *"Sorry, we couldn't find your file. Was it moved, renamed, or
deleted?"*. `launcher accepted = True` was therefore **not** sufficient evidence
of an actual Word open.

Re-verified with a persistent artifact produced by the accepted product path
(`MainWindow` → `GuiWorker` → `ConversionService` → Canonical Core) into the
repository's git-ignored `output/` directory, opened through the real product
action, with the harness kept alive and the artifact left in place:

| Check | Result |
| --- | --- |
| Persistent artifact path | `C:\Users\Quansheng\Documents\projects\MD_Converter\output\p12_06_open_document_smoke_135805.docx` |
| Artifact existed before launch | `True` |
| Artifact size | `37330` bytes (unchanged after open) |
| Valid DOCX / ZIP container | `True` |
| Path authority | `latest_result.output_path` (identity match) |
| Launcher accepted the request | `True` |
| Artifact remained present after launch | `True` |
| Microsoft Word actually opened the document | `True` — Word window title `p12_06_open_document_smoke_135805 [Compatibility Mode] - Word` |
| Open Folder (same persistent artifact) | `True` |
| Missing artifact (dedicated second artifact, deleted) | refused, no substitution, no Word window, no crash |
| Persistent success artifact survived the run | `True` |
| Production code changed for this correction | **NO** |
| P12-06 blocker | **NO** |

Observation (not a defect, no action): while Word holds an artifact open, a new
conversion to the same output name fails closed with an `OUTPUT_ERROR`, because
Word locks the file. The GUI reports it as an ordinary failure; nothing is
reconstructed or overwritten.

The `output/` smoke artifact was intentionally left in place as evidence; the
working tree is otherwise untouched.

Smoke observation (known deferred issue, not owned by P12-06): with a cp1252
console the pipeline's emoji `print` raises `UnicodeEncodeError` and the
conversion fails; the harness streams UTF-8 (`PYTHONIOENCODING=utf-8`) so the
P12-06 UX could be measured. Packaged-environment verification of that defect
belongs to P12-08; **this closure does not claim the cp1252 behaviour is
resolved.**

## 6. Drift check (V11)

| Item | Result |
| --- | --- |
| Direct GUI → Core calls | 0 |
| Application-layer Qt dependency | 0 |
| Core changes | 0 |
| Canonical / specification semantic changes | 0 |
| QA semantic changes | 0 |
| Golden changes | 0 |
| CLI behaviour changes | 0 (the pre-existing working-tree `cli.py` edit is not P12-06) |
| Public API breaking changes | 0 |
| Unauthorized application changes | 0 |
| Second diagnostics system / result taxonomy / path authority | 0 |

## 7. Known deferred issues (carried forward, not fixed)

1. `DocxPostProcessor` emoji / cp1252 console `UnicodeEncodeError` (observed in
   the real-console smoke above; P12-08 owns packaged verification).
2. Invalid YAML frontmatter silently swallowed.
3. Tests rewriting `output\document.docx`.
4. Two approved `packaging_metadata` README failures.
5. Unrelated dirty / untracked working-tree files (including the pre-existing
   `README.md`, `.gitignore` and `cli.py` modifications).
6. Repository-wide lint baseline is not clean (24 `black` files, 43 `ruff`
   findings) — pre-existing, outside the P12-06 change set.
7. The `.venv` still carries a stale non-editable `md_converter` 1.1.0 copy in
   `site-packages`, so tooling must run from the project root
   (`python -m pytest`) for the working tree to win. Not changed in this phase.

## 8. Open blockers

None.

## 9. Decision

P12-06 Error / Diagnostics UX = **CLOSED / ACCEPTED** (recommended).

Recommended next phase: **P12-07 — Settings / Product Polish** (authorized /
next).

The bounded WP-P12-06-06 change set (this document only) is left ready for
review; nothing was staged or committed.
