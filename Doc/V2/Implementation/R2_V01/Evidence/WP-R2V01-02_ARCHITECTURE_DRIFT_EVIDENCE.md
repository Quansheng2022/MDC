# WP-R2V01-02 — Architecture & Authority Drift Audit

**Program:** R2-V01 — Competitive Foundation Integrated Verification (P12-19)
**Work package:** R2V01-02
**Change classification:** G1 — verification only (static guards + focused
tests; no refactor, no source edit)
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — SPEC-GOAL-002,
SPEC-GOAL-003, SPEC-ARCH-007, SPEC-ARCH-009, SPEC-FUNC-023, SPEC-INV-005
**Baseline:** `7330b1e` (`master`)
**Status:** PASS — protected-contract drift = 0

## 1. Objective

Prove the frozen R2-V01 architecture invariants on the current source:

```text
CLI / GUI / Batch -> ConversionService -> Canonical Core -> Renderer -> QA/PostProcessor -> DOCX
```

with a single canonical compile authority, a single QA authority, one table
fitting authority, one figure fitting authority, one TOC localization
authority, no renderer profile-ID branching, narrow `image_width` propagation,
and unchanged CLI/API/output-naming contracts.

## 2. Method

Two independent, read-only methods:

1. **Static guard** — `Verification/verify_architecture_drift.py` parses every
   production `md_converter/**/*.py` with `ast` (tests excluded) and asserts
   nine drift checks (A1–A9). It imports no product code and mutates nothing.
2. **Existing authority guards** — the repository's own frozen guards are run
   as a cross-check (cross-profile fitting, image-width single-authority,
   TOC single-authority, output-profile rendering, application compatibility).

## 3. Static guard results

```text
.venv\Scripts\python.exe Doc/V2/Implementation/R2_V01/Verification/verify_architecture_drift.py

R2-V01 WP-02 ARCHITECTURE / AUTHORITY DRIFT GUARD
--------------------------------------------------------------------
[PASS] A1 GUI has no compiler-stage import
       gui/* imports limited to application/profiles/gui
[PASS] A2 ConversionService -> CompilerContext.create/compile
       default context factory is CompilerContext.create=True; convert calls context.compile=True; CompilerContext.compile exists=True
[PASS] A3 Serial batch reuses the single-file service path
       batch imports compiler stages=[]; main_window uses ConversionService+GuiWorker+request_builder
[PASS] A4 QA instantiated only by compiler.py / renderer layout QA family
       files instantiating QA = ['compiler', 'renderer/layout/final_artifact_qa']
[PASS] A5 one definition site per table/figure/TOC authority
       plan_table_fit:['renderer/layout/table_fitting']; plan_figure_fit:['renderer/layout/figure_sizing']; toc_heading_for_document_text:['renderer/layout/toc_localization']
[PASS] A6 no profile awareness below compiler/application/gui
       profile imports only in compiler/config/gui/profiles
[PASS] A7 CLI output naming == application sanitize_output_title
       cli='[<>:"/\\|?* ]' svc='[<>:"/\\|?* ]'
[PASS] A8 image_width propagation confined to authorized modules
       files referencing image_width = ['compiler', 'config', 'renderer/layout/figure_sizing', 'renderer/word_renderer']
[PASS] A9 public API exports intact (convert / CompilerContext)
       md_converter.__init__ exports convert + CompilerContext
--------------------------------------------------------------------
checks=9 failed=0
exit=0
```

### 3.1 Focused authority-guard cross-check

```text
pytest test_image_width_configuration.py test_fitting_cross_profile.py \
       test_output_profile_rendering.py test_toc_heading_localization.py \
       test_table_fitting.py test_figure_fitting.py \
       application/test_conversion_compatibility.py  -p no:cacheprovider
137 passed in 43.87s
```

## 4. Authority map (evidence)

| Invariant | Single authority (current source) | Evidence |
|---|---|---|
| GUI → Worker/Application → ConversionService | `gui/main_window.py`, `gui/worker.py`, `gui/request_builder.py`; GUI imports only `application` + `profiles` | A1, A3 |
| Batch → same service | `gui/batch.py` (Qt-free orchestration) + `ConversionService.convert` via the single-file worker | A3 |
| ConversionService → Canonical Core | default context factory is `CompilerContext.create`; `convert` calls `context.compile(...)` | A2 |
| `CompilerContext.compile()` canonical | exists in `md_converter/compiler.py`; callers elsewhere are none (owning module only) | A2 |
| Document Intelligence reuses QA | `gui/preflight_model.py`, `gui/result_details.py`, `application/diagnostics_adapter.py` consume `ConversionResult` evidence; no QA class instantiated outside the compiler + layout QA family | A4 |
| One table fitting authority | `renderer/layout/table_fitting.py::plan_table_fit` (called from `renderer/word_renderer.py`) | A5 |
| One figure fitting authority | `renderer/layout/figure_sizing.py::plan_figure_fit` (called from `renderer/word_writer.py`) | A5 |
| One TOC localization authority | `renderer/layout/toc_localization.py::toc_heading_for_document_text` (called from `renderer/post_processor.py`) | A5 |
| No renderer profile-ID branching | no module under `renderer/` imports `md_converter.profiles`; profile data reaches the renderer only as resolved theme presentation (`with_presentation_overrides`) | A6 |
| IMG-CFG propagation narrow | `image_width` appears only in `config`, `compiler`, `renderer/word_renderer` (`_figure_bounds_cm`), `renderer/layout/figure_sizing` | A8 |
| CLI/API/output naming unchanged | `cli.py` naming regex identical to `application.sanitize_output_title`; `md_converter.__init__` still exports `convert` + `CompilerContext` | A7, A9 |

### 4.1 Unrelated dirty tracked files are non-semantic

The three pre-existing modified tracked files were inspected (not staged):

* `md_converter/cli.py` — diff is **docstring-only** (1 hunk, 2 lines:
  example command text). No behaviour change.
* `.gitignore` — ignore-pattern additions only.
* `README.md` — unrelated documentation content (source of the two known
  README packaging baseline failures, WP-R2V01-01 §5).

## 5. Drift result

```text
protected-contract drift        = 0
authority duplication           = 0
renderer profile-ID branches    = 0
SPEC-FUNC-023 drift             = 0
CLI/API/output-naming change    = 0
new dependency                  = 0
new user-facing setting         = 0
```

## 6. WP conclusion

**PASS.** All nine static architecture/authority checks pass and the repository's
own authority guards pass (137 tests). No protected contract drifted, no
authority was duplicated, and no renderer profile-ID branch exists. No G2
condition and no BLOCKED condition was encountered. Pipeline continues to
R2V01-03.
