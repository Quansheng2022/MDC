# P12-06 — Error / Diagnostics UX
## Specification Baseline

**Product baseline SHA:** `068e2fcde0e3c3fc35b564f29381795d4f2899a1`  
**Authority:** G1 unless a G2 stop condition is hit.  
**Core/Golden/CLI semantic change authority:** NONE.

## Objective
Present existing conversion outcomes, warnings, errors, diagnostics, quality-gate evidence, and output actions clearly in the desktop GUI without redefining underlying application/Core semantics.

```text
Canonical Core
  ↓
ConversionService
  ↓
ConversionResult / JobFailure
  ↓
P12-06 Presentation Model
  ↓
GUI UX
```

## Work Packages
1. WP-P12-06-01 Presentation Model
2. WP-P12-06-02 Failure UX
3. WP-P12-06-03 Warning UX
4. WP-P12-06-04 Conversion Report / Diagnostics View
5. WP-P12-06-05 Open Document / Open Folder Actions
6. WP-P12-06-06 Verification & Closure

## Frozen P12-05 Inputs
- Real GUI conversion works end-to-end.
- Conversion runs off GUI thread; completion returns on GUI thread.
- `ConversionResult` retained intact; `JobFailure` retained separately.
- Direct GUI→Core calls = 0.
- Application-layer Qt imports = 0.
- Single-job lifecycle and safe close policy established.

## Ownership Boundary
P12-06 may present/group/summarize existing evidence and expose safe output actions. It must not redefine `ConversionResult` status, QA rules, diagnostics generation, filename semantics, Canonical decisions, retry/cancellation, settings, or packaging.

## Evidence Preservation
Never replace or destroy retained warnings, errors, diagnostics, `diagnostic_summary`, `quality_gate_report`, `technical_detail`, `output_path`, or `JobFailure`.

## Semantics
```text
SUCCESS → success presentation
SUCCESS_WITH_WARNING → success + warning affordance
FAILED → failure presentation
JobFailure → infrastructure/internal failure presentation
```

## UX Principle
Keep the main window simple: concise status/summary plus optional details. Do not build a permanent diagnostics dashboard.

## Known Deferred Issues
Carry forward unless directly blocking the current WP:
1. Two approved packaging_metadata README failures.
2. DocxPostProcessor emoji/cp1252 defect.
3. Invalid YAML frontmatter silently swallowed.
4. Tests rewriting `output\document.docx`.
5. Unrelated dirty/untracked files.

## G2 Stop Conditions
STOP if P12-06 requires changing result/service/Core/QA semantics, Golden/Canonical behavior, CLI/public API semantics, output naming, or introduces a competing diagnostics taxonomy.

## Exit Criteria
Failure UX, warning UX, read-only diagnostics report, and safe output actions pass; evidence remains intact; Core/Golden/CLI semantic changes = 0; P12-06 introduced failures = 0.

Next phase: **P12-07 — Settings / Product Polish**.
