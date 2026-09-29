# WP-D06 — Cross-Profile / Batch / Workflow Hardening

**Program:** D — Advanced Table Fitting + Advanced Figure Fitting
**Work Package:** D-06 (prove the fitting is architecture-wide, without duplicate integration)
**Status:** PASS
**Baseline for this WP:** `b789bdb` (`D-05 integrate advanced figure fitting`)
**Specification references:** `SPEC-FUNC-012`, `SPEC-INV-003`, `SPEC-ARCH-009`, `SPEC-ARCH-010`,
Product Specification §3.3, §8, §11.3, §12.

---

## 1. Deliverable

| Artifact | Path |
| --- | --- |
| Cross-profile / batch / workflow regression | `md_converter/tests/test_fitting_cross_profile.py` (15 tests) |
| Measured cross-profile matrix | `Evidence/wp_d06_cross_profile_matrix.json` |
| Artifacts per profile | `Evidence/samples/cross_profile_<profile>.docx` (5 files) |

No product code changed in this WP: D-03/D-05 already placed the single decisions in the shared
render path, so this WP is pure verification (Product Specification §9: no duplicated fitting logic
in GUI, batch, CLI, renderer or post-processor).

## 2. Measured cross-profile matrix

Document: one 6-column table (3 data rows) + one 400×100 px figure; converted through
`ConversionService` (the GUI/batch shared application path) once per profile.

```text
profile              content_width  table_total   min_col   fills_box  figure         aspect  status    static/rendered/post/final
professional_report  15.9209        15.9226       1.3300    True       12.70 x 3.175  4.00    SUCCESS   PASS/PASS/PASS/PASS
business_report      17.0004        16.9986       1.4199    True       12.70 x 3.175  4.00    SUCCESS   PASS/PASS/PASS/PASS
academic             15.0001        15.0001       1.2524    True       12.70 x 3.175  4.00    SUCCESS   PASS/PASS/PASS/PASS
technical            16.6017        16.6017       1.3864    True       12.70 x 3.175  4.00    SUCCESS   PASS/PASS/PASS/PASS
clean_minimal        15.9209        15.9226       1.3300    True       12.70 x 3.175  4.00    SUCCESS   PASS/PASS/PASS/PASS
```

Reading:

* the fitted table width tracks the **resolved** content width of each profile
  (15.92 / 17.00 / 15.00 / 16.60 / 15.92 cm) with no profile identifier anywhere in the decision —
  the variation is a pure consequence of effective geometry;
* every column stays above the 1.2 cm minimum column width;
* the figure keeps the frozen `SPEC-FUNC-023` target width (12.7 cm) in every profile and stays
  inside every box;
* all five profiles finish `SUCCESS` with every quality gate at `PASS`.

Note (measurement detail, not a defect): the table grid summed from `w:gridCol` differs from the
raw section content width by ≤ 0.002 cm because OOXML stores twips (integers). The delivered table
is inside the content box in every case.

## 3. Workflow coverage

| Workflow | How it is exercised | Result |
| --- | --- | --- |
| all five output profiles | 5-profile matrix above + parametrised tests | PASS |
| default profile / no-profile baseline | `test_default_baseline_conversion_applies_the_same_fitting` (identical facts) | PASS |
| single-file conversion | `ConversionService.convert` (same service the GUI single-file path calls) | PASS |
| Serial Batch | GUI batch execution suite run against the Program D code (see §4) + `test_serial_conversions_keep_no_state_between_files` | PASS |
| GUI conversion path | `md_converter/tests/gui/test_batch_execution.py`, `test_worker.py`, `test_conversion_slice.py`, `test_lifecycle.py` (real Qt offscreen path → `GuiWorker` → `ConversionService`) | PASS |
| CLI / application path | `test_cli_path_produces_a_fitted_artifact` (Click runner, real CLI entry point) + `test_public_api_convert.py` | PASS |
| no profile-ID branching | `test_no_profile_identifier_appears_in_fitting_or_render_paths` (regex over `table_fitting.py`, `figure_sizing.py`, `word_renderer.py`, `word_writer.py`) | PASS |
| no batch state leakage | `test_serial_conversions_keep_no_state_between_files` (1/3/6-row documents on one service instance, then compared with a fresh service) | PASS |
| deterministic repeated conversion | `test_repeated_conversion_is_deterministic_per_profile` (5 profiles × 2 runs) | PASS |

## 4. Verification runs (real output)

```text
$ .venv\Scripts\python.exe -m pytest md_converter/tests/gui/test_batch_execution.py \
      md_converter/tests/gui/test_batch_report.py md_converter/tests/gui/test_batch_model.py \
      md_converter/tests/gui/test_conversion_slice.py md_converter/tests/gui/test_worker.py \
      md_converter/tests/gui/test_request_builder.py md_converter/tests/gui/test_lifecycle.py \
      md_converter/tests/application md_converter/tests/test_public_api_convert.py \
      md_converter/tests/test_fitting_cross_profile.py -p no:cacheprovider
185 passed in 31.30s

$ .venv\Scripts\python.exe -m pytest md_converter/tests/test_fitting_cross_profile.py -p no:cacheprovider -q
15 passed

$ .venv\Scripts\python.exe -m ruff check md_converter/tests/test_fitting_cross_profile.py
All checks passed!
$ .venv\Scripts\python.exe -m black --check --no-cache md_converter/tests/test_fitting_cross_profile.py
1 file would be left unchanged.
$ .venv\Scripts\python.exe -m isort --check-only --settings-path pyproject.toml md_converter/tests/test_fitting_cross_profile.py
(no output -> clean)
```

## 5. Environment observations recorded during this WP

1. **Console encoding.** Running `ConversionService` with an *un-redirected* stdout on this Windows
   console raised `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f4ca'` from the
   pre-existing emoji progress print inside `DocxPostProcessor._style_tables`. This is the known
   cp1252 console condition already recorded by P12-09 (`evidence/wp04_cp1252_reconfirm.json`); it is
   not caused by Program D, and Program D's code paths do not print. Program D evidence generation
   redirects stdout (the same technique the existing test suite uses).
2. **Mermaid rendering.** `mmdc` is absent and Chromium cannot be spawned in this sandbox
   (`spawn EPERM`), so diagram-bearing documents use the documented fallback path
   (`ASCI004/ASCI001/DIAG002`). Figure fitting still produces a valid, content-box-compliant image.

Both observations are reported, not repaired (Product Specification §13, `SPEC-INV-012`).

## 6. Scope discipline

Only one new test file plus evidence artifacts were added. No product source file was modified in
this WP, which is itself the evidence that Program D's fitting did not need per-workflow duplicate
integration code.

## 7. WP-D06 conclusion

Table and figure fitting behave consistently across all five profiles, the default baseline, the
single-file GUI service path, Serial Batch and the CLI, with no profile-ID branching, no batch state
leakage and deterministic repeated output.

**Decision: PASS — next WP is D-07 (integrated verification and artifact evidence).**
