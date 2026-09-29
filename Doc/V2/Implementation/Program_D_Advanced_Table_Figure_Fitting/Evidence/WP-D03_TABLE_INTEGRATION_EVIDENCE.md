# WP-D03 — Table Renderer Integration

**Program:** D — Advanced Table Fitting + Advanced Figure Fitting
**Work Package:** D-03 (integrate the D-02 authority into the existing Word table path)
**Status:** PASS
**Baseline for this WP:** `0239c3f` (`D-02 implement deterministic table fitting policy`)
**Specification references:** `SPEC-FUNC-004`, `SPEC-ARCH-005`, `SPEC-ARCH-009`, `SPEC-INV-001`,
`SPEC-INV-002`, `SPEC-INV-003`, `SPEC-INV-006`, `SPEC-QA-001/002`, Product Specification
§3.1, §6, §8, §11.1, §12.

---

## 1. Integration point (thinnest existing boundary)

```text
CompilerContext.compile
  -> WordRenderer.visit_Table                 (adapter, reads the decision)
       -> plan_table_fit(...)                 (WP-D02 pure authority, unchanged)
       -> WordWriter.apply_table_fit(plan)    (atomic OOXML writes only)
```

Two files changed:

| File | Change |
| --- | --- |
| `md_converter/renderer/word_renderer.py` | `visit_Table` computes/applies the fit; new `_apply_table_fit`, `_table_fitting_limits`, `_effective_content_size_cm`; `_figure_bounds_cm` now shares the single geometry helper; `_size_for("table")` honours the bounded font step |
| `md_converter/renderer/word_writer.py` | new `apply_table_column_widths` / `apply_table_fit` atomic writes (`w:tblLayout=fixed`, `w:tblW`, `w:gridCol`, `w:tcW`) |
| `md_converter/tests/test_table_fitting_integration.py` | new end-to-end regression (12 tests) |

Design notes:

* **Decision vs. execution** — all fitting arithmetic lives in the D-02 policy; the renderer only
  reads resolved values (no duplicated fitting logic, Product Specification §9).
* **One geometry point** — `_effective_content_size_cm()` is now the single place that turns a
  rendered section into an effective content box; table fitting and figure fitting consume the same
  values (`SPEC-FUNC-023`, `CLAR-02`).
* **Structure vs. styling** — the Renderer sets column *structure*; borders, header fill and font
  normalisation remain with the Post-Processor (`SPEC-ARCH-005`, `SPEC-ARCH-009`). No earlier code
  was removed and no ownership changed.
* **Failure behaviour** — an unsupported/failed fitting computation degrades to the previous table
  with a structured `RENDER007` warning instead of failing the build silently (`SPEC-INV-006`).
* **Irreducible wide tables** — `RENDER006` records the limitation with the decision payload; all
  cell values, rows and the minimum readable column width are preserved (§6.3). No landscape
  section, no content transformation, no table splitting is added by Program D.

## 2. What is written into the DOCX (and what is not)

Written: `w:tblLayout type="fixed"`, `w:tblW type="dxa"`, `w:tblGrid/w:gridCol@w:w`,
`w:tc/@w:tcPr/w:tcW`.

Not written / not touched: any cell text, `w:gridSpan`, row order, `w:tblStyle`,
`w:tblBorders`, cell shading, hyperlink relationships, paragraph or run content, document order.

## 3. Measured artifacts (real output)

Generator: `ctx.compile(...)` with the accepted regression configuration
(`word_com=False, enable_cover=False, toc=False, style_tables=True`) and
`output_profile=professional_report`. Raw measurements:
`Evidence/wp_d03_table_measurements.json`; artifacts: `Evidence/samples/*.docx`.

```text
normal_table       cols=4  sections=[15.9209]         total=15.9191  within=True   font=9.5  QA=PASS            overflow=0  codes=[]
                   widths=[3.0039, 8.1104, 2.4024, 2.4024]
wide_table         cols=8  sections=[15.9209]         total=15.9173  within=True   font=9.5  QA=PASS            overflow=0  codes=[]
                   widths=[1.9897 x 8]
long_text_table    cols=2  sections=[15.9209]         total=15.9209  within=True   font=9.5  QA=PASS            overflow=0  codes=[]
                   widths=[1.8521, 14.0688]
irreducible_table  cols=25 sections=[15.9209,24.6204,15.9209]  total=29.9861  within=False  font=9.0
                   QA=PASS_WITH_WARN  overflow=1  codes=[RENDER006, QA_RENDERED_WARN, QA_FINAL_WARN]
                   widths=[1.1994 x 25]
```

Reading of the measurements:

* normal / wide / long-text tables now deliver **explicit, deterministic column widths** that fill
  the effective content width exactly (`15.92 cm` for A4 + 1 in), with `RenderedQA.table_overflow = 0`
  and both `rendered_qa` and `final_artifact_qa` at `PASS` and **zero diagnostics**.
* the wide 8-column table allocates equal widths because all eight columns carry identical content
  evidence — proportional allocation with uniform evidence is intentionally uniform.
* the long-text table gives the content-bearing column ~14.07 cm and the `ID` column 1.85 cm: the
  allocation is content-aware, not equal.
* `irreducible_table` (25 columns) exceeds even the landscape content width: the table keeps every
  cell, keeps the 1.2 cm minimum column width, drops the table font one bounded step to 9.0 pt, and
  reports `RENDER006`; the gate stays `PASS_WITH_WARN` (never `FAIL`). This is the documented §6.3
  limitation, not a silent degradation.
* `QA_RENDERED_WARN`/`QA_FINAL_WARN` in that last case are the pre-existing `table_clipping`
  warnings emitted by `RenderedQA._check_table_overflow`, which measures against `sections[0]`
  (portrait) even when the table rendering section is landscape. Program D did not introduce that
  measurement rule and does not repair it (it is reported here, not silently changed).

## 4. Regression evidence

Targeted renderer / QA / profile regression (D-03 code in place):

```text
$ .venv\Scripts\python.exe -m pytest md_converter/tests/test_page_geometry.py \
      md_converter/tests/test_quality_gate.py md_converter/tests/test_output_profile_rendering.py \
      md_converter/tests/test_output_profiles.py md_converter/tests/test_renderer_v15.py \
      md_converter/tests/test_post_processor.py md_converter/tests/test_simple_table_pass.py \
      md_converter/tests/test_adjacent_tables.py md_converter/tests/test_layout_plan.py \
      md_converter/tests/test_acceptance.py md_converter/tests/test_golden.py \
      md_converter/tests/test_figure_sizing.py md_converter/tests/test_table_fitting.py \
      md_converter/tests/test_table_fitting_integration.py -p no:cacheprovider -q

1 failed, 240 passed, 1 skipped in 71.63s
FAILED md_converter/tests/test_golden.py::test_golden[sample]
  Golden environment mismatch: baseline renderer_backend='playwright', actual renderer_backend='fallback'
SKIPPED md_converter/tests/test_adjacent_tables.py:130 (Windows + Word COM release gate)
```

Post-format re-check of the affected suites:

```text
$ .venv\Scripts\python.exe -m pytest md_converter/tests/test_table_fitting.py \
      md_converter/tests/test_table_fitting_integration.py md_converter/tests/test_page_geometry.py \
      md_converter/tests/test_output_profile_rendering.py -p no:cacheprovider -q
52 passed in 15.41s
```

### Golden failure classification (pre-existing environment condition, not Program D)

```text
$ .venv\Scripts\python.exe -c "...inspect_golden_environment().to_dict()"
{"playwright_installed": true, "chromium_launchable": false, "backend": "fallback",
 "canonical": false, "playwright_version": "1.62.0",
 "chromium_error": "BrowserType.launch: spawn EPERM ... chrome-headless-shell.exe ..."}
```

The Golden baseline declares `renderer_backend="playwright"` and `GOLDEN_ENVIRONMENT.md` makes the
canonical environment mandatory. In this sandbox the Chromium process cannot be spawned
(`spawn EPERM`), so the run is attributed to `fallback` and the Golden test refuses to compare
across backends — before any document comparison happens. Program D does not touch `DiagramPass`,
the Mermaid/Playwright path, the Golden comparison logic or `sample.expected.json`; the failure is
therefore classified as a pre-existing environment condition and is not repaired
(Product Specification §13).

## 5. Quality checks (touched files)

```text
ruff check        -> All checks passed!
black --check     -> 3 files would be left unchanged.
isort --check-only-> clean
```

One formatting correction during the WP: `black` reflowed two long lines inside the new renderer
code (verified: the reformat introduced no changes outside the WP-D03 hunks).

## 6. Scope discipline

`md_converter/renderer/word_renderer.py`, `md_converter/renderer/word_writer.py` and the new
integration test are the only product/test files touched. No theme, config, post-processor,
decision-engine, AST, parser, profile or QA-contract change was made.

## 7. WP-D03 conclusion

The D-02 authority is integrated at the narrowest existing rendering boundary, tables are now
delivered with deterministic explicit widths inside the effective content box, content and
structure are preserved, the readability floor holds, an irreducible wide table is honestly
reported instead of silently degraded, and no new G2-class change was required.

**Decision: PASS — next WP is D-04 (figure fitting policy).**
