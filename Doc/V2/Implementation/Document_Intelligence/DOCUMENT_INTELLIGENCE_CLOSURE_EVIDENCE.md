# Document Intelligence Upgrade — Closure Evidence (WP-DI-07)

**Program:** Document Intelligence Upgrade (Program B of the Product Competitiveness roadmap)
**Baselines:** `Document_Intelligence_Upgrade_Product_Specification.md` (frozen product
decisions) and `DOCUMENT_INTELLIGENCE_ARCHITECTURE_BASELINE.md` (WP-DI-01)
**Change classification:** G1 (additive presentation layer; no G2 item opened)
**Status:** Implemented and verified within the frozen architecture; the scope
boundary recorded in §8.1 needs a product/architecture decision before any
pre-conversion detection claim is made.

## 1. Deliverable chain

| WP | Deliverable | Commit |
|---|---|---|
| DI-01 | Architecture / diagnostic contract baseline (`DOCUMENT_INTELLIGENCE_ARCHITECTURE_BASELINE.md`) | `9ab47cf` |
| DI-02 | Preflight presentation model (`preflight_model.py` + `WP-DI-02_*`) | `6c401d3` |
| DI-03 | Document-quality GUI integration (`main_window.py` + `WP-DI-03_*`) | `535c7a1` |
| DI-04 | Conversion report strengthening (`result_details.py` + `WP-DI-04_*`) | `21d37d9` |
| DI-05 | Batch compatibility / per-file ownership (`WP-DI-05_*` + verification) | `6d1a7ca` |
| DI-06 | Failure / accessibility / UX hardening (`WP-DI-06_*` + verification) | `31474e2` |
| DI-07 | This closure evidence | `git log` — recorded in §9 |

Each work package landed as its own commit with its own scope, verification and
evidence; the code WPs are independently revertible (model → window → report →
verification).

## 2. Files changed

Added:

```text
md_converter/gui/preflight_model.py
md_converter/tests/gui/test_preflight_model.py
md_converter/tests/gui/test_document_intelligence_ux.py
md_converter/tests/gui/test_document_intelligence_report.py
md_converter/tests/gui/test_document_intelligence_batch.py
md_converter/tests/gui/test_document_intelligence_hardening.py
Doc/V2/Implementation/Document_Intelligence/*        (this package)
```

Extended:

```text
md_converter/gui/main_window.py      (document-quality section + wiring)
md_converter/gui/result_details.py   (strengthened report information architecture)
```

Explicitly untouched: `md_converter/application/*`, `diagnostics/*`,
`parser/`, `pipeline/`, `renderer/` (all QA stages included), `services/`,
`quality_gate.py`, `cli.py`, Golden baselines, themes, packaging, `config.yaml`,
and the frozen GUI state list.

The two input documents supplied with the request
(`Document_Intelligence_Upgrade_Implementation_Plan.md` and the Product
Specification) were left unstaged, exactly like the Serial Batch Conversion
plan and product specification were left unstaged by that program.

## 3. Tests and checks

| Check | Result |
|---|---|
| `pytest md_converter/tests/gui/test_preflight_model.py` | 21 passed |
| `pytest md_converter/tests/gui/test_document_intelligence_ux.py` | 13 passed |
| `pytest md_converter/tests/gui/test_document_intelligence_report.py` | 9 passed |
| `pytest md_converter/tests/gui/test_document_intelligence_batch.py` | 7 passed |
| `pytest md_converter/tests/gui/test_document_intelligence_hardening.py` | 10 passed |
| Focused Document Intelligence tests (total) | 60 passed |
| `pytest md_converter/tests/gui md_converter/tests/application` | 568 passed (508 before this program; +60 new) |
| `pytest md_converter/tests` (full suite, 920 collected) | 918 passed; 2 failures, both pre-existing and unrelated — see §8.2 |
| `ruff check md_converter/gui md_converter/tests/gui` | clean |
| `black --check md_converter/gui md_converter/tests/gui` | clean |
| `isort --check-only md_converter/gui md_converter/tests/gui` | clean |

## 4. Real execution evidence

The execution tests are not mocks: they drive the real window through the real
`GuiWorker`, the real `ConversionService` and the Canonical Core, and assert the
real produced artifacts.

| Assertion | Evidence |
|---|---|
| preflight presentation PASS | `test_panel_lists_findings_after_a_warning_conversion`, `test_document_intelligence_report.py` |
| authoritative diagnostics reused PASS | `test_counts_match_the_authoritative_summary`, `test_retained_wording_is_used_verbatim` |
| warning/error counts correct PASS | `test_mixed_severities_are_counted`, `test_report_counts_match_the_authoritative_counts` |
| warning-only conversion remains allowed PASS | `test_warning_does_not_block_the_conversion` (artifact exists; Open Document enabled) |
| conversion report strengthened PASS | `test_report_leads_with_status_summary_and_output_artifact`, `test_technical_detail_stays_last` |
| output artifact reporting correct PASS | `test_report_leads_with_status_summary_and_output_artifact`, `test_missing_artifact_is_reported_and_not_actionable` |
| batch compatibility PASS | `test_aggregate_batch_report_carries_no_findings`, SBC execution suite still green |
| report ownership per file PASS | `test_each_file_keeps_its_own_findings`, `test_mixed_batch_results_keep_finding_ownership` |
| accessibility PASS | `test_findings_are_keyboard_reachable_when_visible`, `test_findings_are_textual_not_colour_only`, `test_panel_carries_accessible_identities` |
| GUI responsiveness PASS | every conversion runs off the GUI thread; the document-quality section is applied from retained evidence in `_apply_state()`, never from a worker callback computation |
| privacy/locality unchanged PASS | no new import outside the GUI/application boundary, no network call, no account, no telemetry |

Single-file GUI smoke / warning-report smoke / mixed-result batch smoke are the
`test_document_intelligence_ux.py` and `test_document_intelligence_batch.py`
execution tests above (real conversions, offscreen Qt platform).

## 5. Drift results

```text
ConversionService semantic drift = 0
ConversionRequest / ConversionResult semantic drift = 0
Core drift = 0
Canonical drift = 0            (CANONICAL_SPEC.md governs the compiler; no entry touched)
QA semantic drift = 0          (no QA stage added, changed or re-implemented)
Golden drift = 0               (no Golden baseline read or updated)
CLI / public API breaking drift = 0
output naming / path semantics drift = 0
introduced failures = 0

preflight presentation PASS
authoritative diagnostics reused PASS
warning/error counts correct PASS
warning-only conversion remains allowed PASS
conversion report strengthened PASS
output artifact reporting correct PASS
batch compatibility PASS
report ownership per file PASS
accessibility PASS
GUI responsiveness PASS
privacy/locality unchanged PASS
open blockers = 0
```

## 6. Superseded guards

None.  No accepted test contract was changed: every existing GUI/application
guard (`test_report_view.py`, `test_warning_ux.py`, `test_accessibility_window.py`,
`test_main_window_polish.py`, `test_batch_*`, `tests/application/*`) passes
unchanged, including the frozen dialog set, the frozen Tab chain, the frozen
state list, the "window reads no raw diagnostic field" guard and the
"retained counts are displayed, not recomputed" rule.

## 7. Definition of Done

```text
document quality presented from authoritative diagnostics PASS
no invented finding                                       PASS
warnings never newly block conversion                     PASS
existing fatal errors respected                           PASS
conversion report answers the product questions           PASS
output artifact reporting correct                         PASS
actionable review guidance                                PASS
batch compatibility                                       PASS
per-file report ownership                                 PASS
accessibility baseline                                    PASS
privacy/locality unchanged                                PASS
determinism preserved                                     PASS
```

## 8. Open items and limitations

1. **No pre-conversion detection (scope boundary, needs a decision).** Under the
   frozen architecture the canonical pipeline is the only diagnostic producer,
   and the accepted stage order (`Parser → AST → Pipeline → Renderer →
   Post-Processor`, SPEC-INV-005) exposes no pre-render QA entry point.  The
   document-quality surface therefore presents the findings the authoritative
   conversion already reported; it does not detect issues *before* the first
   conversion attempt.  Adding an early QA entry point is a Core change and was
   correctly treated as a G2 stop condition (baseline §3.8/§6.1).  The product
   specification §6 ("before or during conversion") is satisfied "during
   conversion and immediately after"; a true pre-flight requires explicit
   product/architecture authorization.
2. **Pre-existing, unrelated failures.** `pytest md_converter/tests` reports two
   failures in `test_packaging_metadata.py`
   (`test_pkg_documented_extras_exist_in_metadata`,
   `test_pkg_readme_has_no_legacy_packaging_references`).  They are caused by the
   working tree's already-modified `README.md`, not by this program; they were
   reported, not modified (SPEC-INV-012).  Identical to the SBC closure finding.
3. **Pre-existing environment noise.** The full-suite run prints a Windows
   fatal-exception dump from Word COM automation
   (`post_processor._update_toc_with_word`) during `test_public_api_convert.py`;
   it fails no test and is unrelated to this program.
4. **No packaged/GUI manual smoke.** Verification ran the offscreen Qt platform
   with real widgets, real worker threads, the real service and real artifacts.
   A human packaged-GUI smoke remains part of the next release-candidate gate.
5. **Only one document's findings are presented at a time.** A multi-file batch
   keeps the in-window quality section hidden and presents each file's findings
   in its own report, so a batch never implies a shared quality verdict.

## 9. Commit chain

```text
9ab47cf  DI-01  freeze document intelligence architecture
6c401d3  DI-02  add preflight presentation model
535c7a1  DI-03  integrate document preflight UX
21d37d9  DI-04  strengthen conversion report
6d1a7ca  DI-05  integrate document intelligence with batch results
31474e2  DI-06  harden document intelligence UX
(this commit)  DI-07  close document intelligence upgrade
```

Only the files listed in §2 were staged (`git diff --cached --name-status` was
inspected before every commit).  The working tree's pre-existing modifications
(`.gitignore`, `README.md`, `md_converter/cli.py`) and its other untracked files
were left untouched.

## 10. Final recommendation

Document Intelligence delivers the strongest available part of Program B
without touching a single compiler, QA, Golden or API semantic: the existing
authoritative diagnostics are now grouped, ordered, counted and explained in
both the window and the conversion report, batch behaviour is unchanged and
per-file, and every accepted guard still passes.  Drift is zero across all
protected surfaces.

Recommendation: accept DI-01…DI-06, and take an explicit product/architecture
decision on §8.1 before any external claim of "pre-conversion" quality checks
is made.  The next roadmap step (Program C: Output Profiles, Advanced Table and
Figure Fitting) is independent of that decision.
