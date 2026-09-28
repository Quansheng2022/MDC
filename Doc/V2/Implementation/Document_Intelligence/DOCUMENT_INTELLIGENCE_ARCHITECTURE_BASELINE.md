# WP-DI-01 — Document Intelligence Architecture / Diagnostic Contract Baseline

**Document Type:** Architecture / Contract Baseline
**Program:** Document Intelligence Upgrade (Program B of the Product Competitiveness roadmap)
**Inputs:** `Doc/V2/Product/Document_Intelligence_Upgrade_Product_Specification.md`,
`Doc/V2/Implementation/Document_Intelligence/Document_Intelligence_Upgrade_Implementation_Plan.md`
**Status:** Frozen for the DI work packages
**Change classification:** G1 — controlled presentation-layer work (no G2 item is opened)

## 1. Authority and SPEC references

`CANONICAL_SPEC.md` (FROZEN) is the single Canonical Authority and governs the
compiler contract.  Document Intelligence adds no compiler behaviour, so no
FROZEN entry is modified and no Spec Update is required.  The work is bound by:

| Reference | How it constrains this feature |
|---|---|
| SPEC-GOAL-003 / SPEC-INV-003 | Determinism: grouping, ordering and counts are deterministic and derived from retained evidence. |
| SPEC-GOAL-005 / SPEC-ARCH-013 | The existing quality gates stay the only real Gate; presentation never turns a warning into a gate. |
| SPEC-GOAL-006 | Auditability: SPEC → IMP → Code → Test → Evidence for every work package. |
| SPEC-ARCH-004 / SPEC-ARCH-011 | Renderer and Word structures are untouched: this feature touches no renderer module. |
| SPEC-ARCH-007 | Dependency direction stays one-way: presentation imports the application boundary only. |
| SPEC-INV-005 | The pipeline is never bypassed and no early QA entry point is added. |
| SPEC-INV-006 | Recoverable problems keep producing the canonical Diagnostics; presentation neither adds nor removes one. |
| SPEC-INV-012 | Only the modules listed in §4 are modified; extra observations are reported, not patched. |
| SPEC-QA-001 … SPEC-QA-005 | StaticQA / RenderedQA / Repair / FinalArtifactQA semantics are reused verbatim and never re-implemented. |

## 2. Inspection performed

| Area | Modules inspected | Finding |
|---|---|---|
| Diagnostic authority | `diagnostics/collector.py`, `diagnostics/diagnostic.py` | `DiagnosticCollector` is the single record authority; `Severity` defines `INFO` / `WARNING` / `ERROR` / `FATAL` and `is_error()` covers `ERROR`+`FATAL`. |
| QA stages | `renderer/layout/static_qa.py`, `rendered_qa.py`, `final_artifact_qa.py`, `quality_gate.py` | The three QA stages already emit into the collector (`QA_STATIC_*`, `QA_RENDERED_*`, `QA_FINAL_*`) and the gate contract is `FAIL → QualityGateError`. |
| Pipeline diagnostics | `pipeline/passes/*`, `renderer/post_processor.py` | Fallback / degradation wording already exists: `DIAG001`–`DIAG003` (diagram text fallback, save failure), `POST002` (Word post-processing unavailable), `MD001`/`MD003` (image problems), `NORM001`/`NORM002` (normalisation notes), `ASCI*`, `TABLE*`, `LIST*`. |
| Application adapter | `application/diagnostics_adapter.py` | One adapter translates canonical records into `ApplicationDiagnostic` (display-safe `user_message` + untouched technical `message`), one `DiagnosticSummary` counts them, and `_USER_MESSAGE_MAP` is the only per-code wording authority. |
| Result model | `application/conversion_result.py` | `ConversionResult` retains warnings, errors, all diagnostics, the summary, the quality-gate report and the technical detail; status semantics are `SUCCESS` / `SUCCESS_WITH_WARNING` / `FAILED`. |
| Service | `application/conversion_service.py` | The only conversion entry point; warnings never change the outcome, errors map to `FAILED` with evidence retained. |
| Presentation | `gui/presentation_model.py`, `result_mapping.py`, `state.py` | One Qt-free presentation model owns title/summary/counts; one mapping owns status → GUI state; one frozen state list (`EMPTY/READY/CONVERTING/SUCCESS/SUCCESS_WITH_WARNING/FAILED`). |
| Report surface | `gui/result_details.py` | One read-only report surface for every outcome kind; already renders warnings, errors, diagnostics, summary, gate report and technical detail. |
| Batch | `gui/batch.py`, `gui/batch_report.py` | The aggregate report is derived presentation only; per-file evidence is already retained per item and the per-row `Details...` action already opens the single report surface. |
| Guards | `tests/gui/test_report_view.py`, `test_accessibility_window.py`, `test_main_window_polish.py`, `test_warning_ux.py`, `tests/application/*` | Frozen guards exist for: one dialog set, no Core import from the GUI, the window never reading raw diagnostic fields, the frozen state list, the frozen Tab chain, no colour-only status, and the retained-count rule. |

## 3. Frozen decisions

1. **Diagnostic sources.** `DiagnosticCollector` remains the single QA
   authority, and `DiagnosticsAdapter` remains the single application-facing
   adapter.  Document Intelligence adds no producer: it consumes exactly the
   records the canonical pipeline already emitted (`QA_STATIC_*`,
   `QA_RENDERED_*`, `QA_FINAL_*`, `DIAG00*`, `POST001`/`POST002`, `NORM00*`,
   `MD001`/`MD003`, `PARSE*`, `PIPE001`, `RENDER*`, `TABLE*`, `LIST*`, `ASCI*`).
2. **Severity semantics.** `INFO` / `WARNING` / `ERROR` / `FATAL` keep their
   canonical meaning; nothing is re-labelled, no warning is promoted and no
   error is softened.  A presentation severity (`success` / `warning` /
   `error`) remains a 1:1 projection owned by the presentation model.
3. **Wording authority.** Per-finding wording is the adapter's
   `user_message` (`_USER_MESSAGE_MAP` plus the retained technical message).
   The presentation layer composes **counts-only** wording and passes the
   retained `DiagnosticSummary.user_message` through verbatim, so the preflight
   view and the conversion report cannot phrase the same evidence differently.
   No second wording map and no per-code wording is created.
4. **Report data flow.**
   `ConversionResult` → `present_result` / `present_job_failure` (outcome,
   title, summary, counts) → `preflight_from_result` (grouped findings) →
   `result_details.build_report_text` (the one report surface) → GUI and the
   batch report's per-row `Details...`.
5. **Preflight integration point.** The retained application result is the
   integration point.  The GUI has no pre-conversion QA entry point, and none
   may be added without explicit G2 authority (see §6, stop condition 1).
   The document-quality surface therefore presents the findings the
   authoritative conversion already reported for the current document: it is
   populated when the result is retained, cleared when the selection changes,
   and it never blocks, delays or duplicates a conversion.
6. **Batch boundary.** Findings are owned by exactly one document.  The batch
   layer aggregates only statuses and counts; the batch report stays
   summary-only; a multi-file batch presents no single file's findings as the
   batch's own; each item keeps its own report through the existing per-row
   `Details...` action.
7. **Preflight-eligible findings.** Every retained diagnostic is
   preflight-eligible, because it already exists as evidence the moment a
   conversion attempt produced it.  Eligibility is presentation-only: it is
   grouped by severity, ordered deterministically and counted from the items.
8. **Post-conversion-only findings.** *Every* diagnostic produced by the
   canonical stages is post-conversion-only under the frozen architecture — the
   parser, pipeline, StaticQA, RenderedQA, FinalArtifactQA and the
   post-processor are the only producers, and the accepted pipeline order
   (SPEC-INV-005) does not expose a pre-render QA entry point.  This program
   therefore does **not** claim pre-conversion detection it cannot deliver;
   adding an early QA entry point is an explicitly identified G2 stop
   condition and was not taken.
9. **Duplicate suppression rule.** No suppression is applied.  A retained
   record produces exactly one finding, so the presented counts always equal
   the authoritative counts (`DiagnosticSummary`) and can never drift.
   Suppression would be permitted only for identical diagnostic identity and
   would have to be authorized separately; a finding is never repeated inside
   one presentation group.
10. **Presentation boundary.** The new surface is an in-window, read-only,
    Qt-free-modelled section: no new `GuiState`, no new dialog module, no new
    shortcut, no styling by colour, no second report implementation, and no
    new import of a Core compiler stage from the GUI.

## 4. Architecture delta

```text
ConversionResult (retained, unchanged)
  ├── presentation_model      outcome / title / summary          (P12-06, unchanged)
  ├── preflight_model         group / order / count / label      (DI-02, new)
  │      ├── document-quality section in MainWindow              (DI-03, new)
  │      └── strengthened report sections in result_details      (DI-04)
  └── batch / batch_report    per-file ownership, aggregate only (DI-05, verified)
```

Files added:

```text
md_converter/gui/preflight_model.py
md_converter/tests/gui/test_preflight_model.py
md_converter/tests/gui/test_document_intelligence_ux.py
md_converter/tests/gui/test_document_intelligence_batch.py
md_converter/tests/gui/test_document_intelligence_hardening.py
Doc/V2/Implementation/Document_Intelligence/*
```

Files extended:

```text
md_converter/gui/main_window.py      (document-quality section + wiring)
md_converter/gui/result_details.py   (strengthened report information architecture)
```

Explicitly untouched: `md_converter/application/*`, `parser/`, `pipeline/`,
`renderer/` (including every QA stage), `services/`, `quality_gate.py`,
`diagnostics/*`, `cli.py`, Golden baselines, themes, packaging, and the frozen
GUI state list.

## 5. Exit criteria

- Single QA authority identified — `DiagnosticCollector` + `DiagnosticsAdapter`.
- Presentation-only boundary identified — `preflight_model` creates no finding.
- No G2 change required — confirmed (no Core/Canonical/QA/Golden/API change).
- Files to touch are bounded — as listed in §4.
- Batch integration strategy identified — per-file ownership, aggregate report
  unchanged.
- Preflight-eligible and post-conversion-only findings classified — §3.7/§3.8.
- Stop conditions dispositioned — §6.

## 6. Mandatory stop conditions

| Stop condition (implementation plan §15) | Status |
|---|---|
| 1. New QA semantics required | Not met — no QA stage is added or changed. An early (pre-render) QA entry point would have met it and was **not** taken. |
| 2. Diagnostic meaning must change | Not met — severities and codes are reused verbatim. |
| 3. Warnings must become blocking | Not met — warnings stay non-blocking. |
| 4. `ConversionService` semantics must change | Not met — the service is untouched. |
| 5. Core / Canonical must change | Not met — no compiler module is touched. |
| 6. Golden semantics must change | Not met — no Golden baseline is read or updated. |
| 7. Output naming / path semantics must change | Not met — `ConversionResult.output_path` stays the only path authority. |
| 8. CLI / public API semantics must change | Not met — `cli.py` and the public API are untouched. |
| 9. A second QA engine is emerging | Not met — one adapter, one record set, one report surface. |
| 10. Batch compatibility requires duplicated diagnostics | Not met — per-file ownership reuses the single report surface. |
