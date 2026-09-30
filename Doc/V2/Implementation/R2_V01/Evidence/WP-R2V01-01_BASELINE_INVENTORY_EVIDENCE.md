# WP-R2V01-01 — Baseline Freeze & Verification Inventory

**Program:** R2-V01 — Competitive Foundation Integrated Verification (P12-19)
**Work package:** R2V01-01
**Change classification:** G1 — verification only (no product, Core, QA, CLI or
semantic change)
**Governing SPEC:** `CANONICAL_SPEC.md` (FROZEN 1.1) — SPEC-GOAL-002,
SPEC-GOAL-003, SPEC-ARCH-009, SPEC-FUNC-023, SPEC-INV-005
**Evidence date:** 2026-09-30
**Status:** PASS — baseline frozen

## 1. Objective

Freeze the current integrated source baseline and its verification scope before
any R2-V01 work package runs: branch/HEAD, working tree, import path, tool
environment, full test inventory, known failing test IDs, the Program
A/B/C/THL/D/IMG-CFG production/tests/invariants map, and the V02/V03/V04
exclusions. Prove the current source is importable, `ConversionService` is
available, a fast test passes, and sandbox command execution works.

## 2. Git baseline

Captured with read-only git commands before any WP activity:

```text
git rev-parse --abbrev-ref HEAD   -> master
git rev-parse HEAD                -> 7330b1e3a98991771ebafe51b9bb03713ddb2418
git log -1 --oneline              -> 7330b1e IC-06 close image width configuration propagation
```

Recent accepted program closures on this HEAD (context only, not re-opened):

```text
7330b1e IC-06 close image width configuration propagation
99b6a95 IC-05 verify image width configuration propagation
bd1a818 IC-04 guard image width configuration contract
0baba62 IC-03 fix image width configuration propagation
3eb7e2a IC-02 classify image width propagation behavior
24203fe IC-01 inspect image width configuration authority
0884fbe D-08 close advanced table and figure fitting
```

### 2.1 Working tree at baseline (tracked modifications, preserved, never staged)

```text
git status --short (tracked, modified)
  M .gitignore
  M README.md
  M md_converter/cli.py

git diff --name-status
  M .gitignore
  M README.md
  M md_converter/cli.py
```

These three tracked modifications are **pre-existing unrelated dirty state**
(`.gitignore`, `README.md`, `md_converter/cli.py`) and match the R2-V01 product
specification section 6 "known baseline conditions". They are preserved
untouched and are never staged by any R2-V01 work package.

Untracked trees present at baseline (unrelated artifacts — a subset listed;
preserved, never staged):

```text
Doc/V2/... (in-flight governance/product docs, incl. this R2-V01 plan set)
Test/, tests/, tools/, review_packages/, release/, dist/, dist_installer/
MD_Converter_v1.1.0_*/, MDC_p11_*/, input_test/, packaging/windows/*
Doc/MDC_Roadmap_0920.*, EULA.txt, THIRD_PARTY_NOTICES.txt, README_bck.md
```

`pyproject.toml` pins `testpaths = ["md_converter/tests"]`; the root `tests/`
and `Test/` trees are **not** collected by pytest and are unrelated to the
package.

## 3. Environment

```text
interpreter            .venv\Scripts\python.exe   (project root .venv)
python                 3.12.14
md_converter.__file__  ...\MD_Converter\md_converter\__init__.py  (editable, source)
md_converter.__version__ 1.1.0
```

Declared/installed toolchain relevant to verification:

```text
pytest 9.1.1   pytest-cov 7.1.0   ruff 0.16.1   black 26.5.1   isort 8.0.1
playwright 1.62.0   PySide6 6.11.2   python-docx 1.2.0   markdown-it-py 4.2.0
```

Baseline environment quirks recorded (product specification section 6):

1. `.pytest_cache` is ACL-inaccessible in this sandbox, so all R2-V01 pytest
   runs use `-p no:cacheprovider`.
2. Console stdout default encoding in this sandbox is `cp1252`; the CLI /
   post-processor print path emits CJK/emoji, so source-level CLI smoke runs set
   `PYTHONUTF8=1` / `PYTHONIOENCODING=utf-8`. Pytest passes without it because
   pytest replaces `sys.stdout` with a UTF-8-capable capture object (see 7.3).
3. Word COM is unavailable in the sandbox; TOC page-number refresh retries and
   then degrades gracefully (documented behaviour) without failing the
   conversion (see 7.3).
4. Chromium cannot launch (`spawn EPERM`) in this sandbox, so the Golden
   environment backend resolves to `fallback`. This is R2-V04 environment debt,
   not source.

## 4. Test inventory

```text
pytest --collect-only  ->  1150 tests collected in 1.26s
test files             ->  75 (application/, gui/, acceptance/, golden/, root)
```

Coverage areas collected: `md_converter/tests/application/*` (7 files),
`md_converter/tests/gui/*` (33 files), plus root-level parser / pipeline /
renderer / theme / placement / QA / release-evidence / packaging / golden /
acceptance suites.

## 5. Known failing baseline test IDs

Full-suite baseline run (once, `-p no:cacheprovider`):

```text
1150 collected  ->  1144 passed  ·  2 skipped  ·  4 failed
```

The 4 baseline failures are exactly the two documented categories and are
**causally excluded** from R2-V01 source authority:

| # | Test node id | Category | Root cause (evidence) | Classification |
|---|---|---|---|---|
| 1 | `test_packaging_metadata.py::test_pkg_documented_extras_exist_in_metadata` | README packaging | reads the dirty working-tree `README.md`; `{dev, mermaid, windows}` not all documented | `PRE_EXISTING_KNOWN_FAILURE` |
| 2 | `test_packaging_metadata.py::test_pkg_readme_has_no_legacy_packaging_references` | README packaging | dirty working-tree `README.md` lacks `[project.entry-points` | `PRE_EXISTING_KNOWN_FAILURE` |
| 3 | `test_golden_environment.py::test_canonical_golden_environment` | Chromium env | `BrowserType.launch: spawn EPERM`; backend resolves to `fallback` | `ENVIRONMENT_FAILURE` (→ `LATER_RELEASE_GATE_DEBT`, R2-V04) |
| 4 | `test_golden.py::test_golden[sample]` | Chromium env | Golden baseline expects `renderer_backend='playwright'`, sandbox yields `'fallback'` | `ENVIRONMENT_FAILURE` (→ `LATER_RELEASE_GATE_DEBT`, R2-V04) |

Both README failures are functions of the **modified working-tree `README.md`**
(an unrelated pre-existing edit), not of `md_converter` source. Neither is
repaired by R2-V01.

## 6. Program inventory (production modules / tests / invariants)

| Program | Production modules (frozen) | Primary tests | Governing invariant |
|---|---|---|---|
| Serial Batch Conversion | `gui/batch.py`, `gui/batch_report.py`, `gui/worker.py` (`idle`), `gui/main_window.py` orchestration | `tests/gui/test_batch_*.py`, `tests/gui/test_document_intelligence_batch.py` | strict serial; `active_conversion_count <= 1`; reuse of the single-file `ConversionService` path |
| Document Intelligence | `gui/preflight_model.py`, `gui/result_details.py`, `gui/presentation_model.py`, `application/diagnostics_adapter.py` | `tests/gui/test_document_intelligence_*.py`, `tests/application/test_diagnostics_adapter.py` | reuses existing QA diagnostics; no second QA authority |
| Professional Output Profiles (Program C) | `profiles/model.py`, `profiles/registry.py`, `profiles/theme_overrides.py` | `tests/test_output_profiles.py`, `tests/test_output_profile_rendering.py`, `tests/gui/test_output_profile_selection.py` | resolved presentation geometry only; no renderer profile-ID branch (SPEC-ARCH-009) |
| TOC Heading Localization (THL) | `renderer/layout/toc_localization.py`, `renderer/layout/language_detection.py` | `tests/test_toc_heading_localization.py`, `tests/test_language_detection.py` | single TOC-title authority; deterministic Han-ideograph predicate |
| Program D — Advanced Table/Figure Fitting | `renderer/layout/table_fitting.py`, `renderer/layout/figure_sizing.py`, `renderer/layout/section_manager.py`, `renderer/layout/decision_engine.py` | `tests/test_table_fitting*.py`, `tests/test_figure_fitting*.py`, `tests/test_figure_sizing.py`, `tests/test_fitting_cross_profile.py` | one table fitting authority; one figure fitting authority; content/aspect-ratio preserved |
| IMG-CFG-01 | `renderer/post_processor.py`; compiler `image_width` config propagation path | `tests/test_image_width_configuration.py` | narrow authorized `image_width` propagation; frozen SPEC-FUNC-023 |

Canonical authority retained (not redefined): `CompilerContext.compile()` is the
single conversion authority (`DEC-P12-02-01`); CLI / GUI / Batch all enter via
`ConversionService` → `CompilerContext` (drift audit in WP-R2V01-02).

## 7. Smoke evidence (current source)

### 7.1 Import + entry-point availability

```text
md_converter.__version__ = 1.1.0
module file = C:\Users\Quansheng\Documents\projects\MD_Converter\md_converter\__init__.py
ConversionService = <class 'md_converter.application.conversion_service.ConversionService'>
CompilerContext.create = <bound method CompilerContext.create of class 'md_converter.compiler.CompilerContext'>
```

### 7.2 Fast test

```text
pytest md_converter/tests/application/test_conversion_service.py -p no:cacheprovider -q
.................                                                        [100%]
17 passed
```

### 7.3 End-to-end service smoke (Markdown -> DOCX)

With `PYTHONUTF8=1` (console encoding workaround, section 3.2):

```text
status = SUCCESS  success = True  exists = True
```

A representative document (heading + bold paragraph + table) converted through
`ConversionService.convert(ConversionRequest(...))` produced a DOCX. Without
`PYTHONUTF8=1` the same smoke returned `FAILED` **only** because the sandbox
console (`cp1252`) cannot encode the post-processor's CJK/emoji `print` output
(`UnicodeEncodeError` in `cp1252.py`); the DOCX was still written. Recorded as
an environment note, not a source defect (see WP-R2V01-05 for the CLI
entry-point re-check).

### 7.4 Sandbox command execution

All baseline commands (`git`, `.venv` Python, `pytest`, `pip list`) executed
successfully, proving sandbox command execution works for this work package.

## 8. R2-V01 scope bounds — explicit exclusions

Deferred to later gates; **not** closed by R2-V01:

* Packaged multi-file / runtime verification → `PENDING R2-V02`
* Native Word / human visual acceptance → `PENDING R2-V03`
* Chromium / Golden-environment retest → `PENDING R2-V04`
* Then R2 RC → Human Acceptance → Production Release.

Out of scope per product specification section 4 (not implemented here): new
features, true Core preflight, no-upscale policy, landscape tables, new
profiles/config/GUI settings, templates/equations/citations/PDF, installer
rebuild, packaged smoke, native Word visual acceptance, Chromium repair, README
cleanup, Golden semantic rewrites.

## 9. WP conclusion

**PASS.** Baseline frozen at `7330b1e` (`master`). 1150 tests collected; known
failing set = 4 (`2 README packaging` + `2 Chromium/Golden`), all causally
excluded. Source is importable, `ConversionService` is available, a fast test
passes, and sandbox command execution works. Unrelated dirty state preserved.

No G2 condition and no BLOCKED condition was encountered. Pipeline continues to
R2V01-02.
