# WP-D07 — Integrated Verification & Artifact Evidence

**Program:** D — Advanced Table Fitting + Advanced Figure Fitting
**Work Package:** D-07 (one bounded integrated verification pass + final measured artifacts)
**Status:** PASS
**Baseline for this WP:** `e26d709` (`D-06 harden fitting across profiles and workflows`)
**Program baseline HEAD:** `5f8bf2a26702c069d9190f5aa6aa937886f93eb4`
**Specification references:** `SPEC-INV-001`–`SPEC-INV-003`, `SPEC-QA-001`–`SPEC-QA-005`,
`SPEC-ARCH-005`, `SPEC-ARCH-009`, Product Specification §11, §12, §13, §14.

---

## 1. Test layers (all executed against the D-01…D-06 code)

| # | Layer | Command / suite | Result |
| --- | --- | --- | --- |
| 1 | Program D focused | 5 Program D test files (`-v`) | **88 passed** (`wp_d07_focused_tests.txt`) |
| 2 | Renderer / post-processor | `test_renderer_v15.py`, `test_post_processor.py`, `test_quality_gate.py`, `test_layout_plan.py`, `test_page_geometry.py` | PASS (in full suite) |
| 3 | Professional Output Profiles | `test_output_profiles.py`, `test_output_profile_rendering.py` | PASS |
| 4 | Serial Batch | `gui/test_batch_execution.py`, `test_batch_report.py`, `test_batch_model.py` | PASS (185-test workflow run) |
| 5 | Document Intelligence path | `gui/test_document_intelligence_*.py` | PASS (in full suite) |
| 6 | TOC Heading Localization | `test_toc_heading_localization.py` | PASS |
| 7 | Application / GUI workflow | `md_converter/tests/application`, GUI subset | PASS (185 passed) |
| 8 | Golden / acceptance | `test_golden.py` (environment-blocked), `test_acceptance.py` | acceptance PASS; Golden environment-blocked (see §5) |
| 9 | Broader regression | full `md_converter/tests` run | **1122 passed, 4 failed (all pre-existing), 2 skipped** (`wp_d07_full_suite.txt`) |
| 10 | Full suite near closure | the run above is the full suite | done |

```text
$ .venv\Scripts\python.exe -m pytest <5 Program D test files> -p no:cacheprovider -v
88 passed in 12.93s

$ .venv\Scripts\python.exe -m pytest md_converter/tests -p no:cacheprovider
4 failed, 1122 passed, 2 skipped in 128.85s
```

## 2. Quality checks on the exact touched Program D files

```text
ruff check          -> All checks passed!
black --check --no-cache -> 9 files would be left unchanged.
isort --check-only  -> clean
```

Full log: `Evidence/wp_d07_lint_format.txt`. One cosmetic `black` reflow of a Program D test file
was applied after the full-suite run; the affected suite was re-run green afterwards (88 passed,
log regenerated after the reflow).

## 3. Required artifact set

### Tables (`Evidence/samples/*.docx`, measurements in `wp_d03_table_measurements.json`)

| Artifact | Columns | Content width | Delivered width | Font | QA |
| --- | --- | --- | --- | --- | --- |
| `normal_table.docx` | 4 | 15.9209 | 15.9191 | 9.5pt | PASS |
| `wide_table.docx` | 8 | 15.9209 | 15.9173 | 9.5pt | PASS |
| `long_text_table.docx` | 2 | 15.9209 | 15.9209 | 9.5pt | PASS |
| `numeric_table.docx` | 6 | 15.9209 | 7.4577 (narrow → not stretched) | 9.5pt | PASS |
| `irreducible_table.docx` | 25 | 24.6204 (landscape) | 29.9861 | 9.0pt | PASS_WITH_WARN + `RENDER006` |
| wide table across 5 profiles | 6 | 15.92 / 17.00 / 15.00 / 16.60 / 15.92 | 15.9226 / 16.9986 / 15.0001 / 16.6017 / 15.9226 | 9.5pt | PASS ×5 |

Merged-cell input: **not reachable** with the current parser/renderer. The probe
(`wp_d07_artifact_measurements.json` → `merged_cell_probe`) shows that the Markdown parser produces
no table node at all for HTML table markup (`html_table_nodes = 0`), and `WordWriter.merge_cells`
is unused by the renderer. Program D therefore records merged-cell fitting as *not applicable with
evidence* and instead verifies the policy against ragged and empty cell rows (WP-D02). No merge
support was added (out of scope, Product Specification §4).

### Figures (`Evidence/samples/figure_*.docx`, measurements in `wp_d05_figure_measurements.json`)

| Artifact | Intrinsic px | Content box | Rendered | Aspect preserved | QA |
| --- | --- | --- | --- | --- | --- |
| `figure_small.docx` | 82×41 | 15.92 × 24.62 | 12.7000 × 6.3500 | yes | PASS |
| `figure_wide.docx` | 400×100 | 15.92 × 24.62 | 12.7000 × 3.1750 | yes | PASS |
| `figure_tall.docx` | 30×70 | 15.92 × 24.62 | 10.5516 × 24.6204 | yes | PASS |
| `figure_landscape.docx` | 200×80 | 15.92 × 24.62 | 12.7000 × 5.0800 | yes | PASS |
| `figure_diagram.docx` | 600×100 (SVG fallback) | 15.92 × 24.62 | 12.7000 × 2.1167 | yes | PASS |
| `figure_wide_narrow_box.docx` | 400×100 | 11.00 × 24.62 | 10.9996 × 2.7499 | yes | PASS |
| representative figure across 5 profiles | 400×100 | 15.92 / 17.00 / 15.00 / 16.60 / 15.92 | 12.7000 × 3.1750 (×5) | yes | PASS ×5 |

## 4. Cross-profile matrix (table + figure, one document per profile)

```text
profile              content_width  table_total  min_col  fills_box  figure         QA
professional_report  15.9209        15.9226      1.3300   True       12.70 x 3.175  PASS/PASS/PASS/PASS
business_report      17.0004        16.9986      1.4199   True       12.70 x 3.175  PASS/PASS/PASS/PASS
academic             15.0001        15.0001      1.2524   True       12.70 x 3.175  PASS/PASS/PASS/PASS
technical            16.6017        16.6017      1.3864   True       12.70 x 3.175  PASS/PASS/PASS/PASS
clean_minimal        15.9209        15.9226      1.3300   True       12.70 x 3.175  PASS/PASS/PASS/PASS
```

## 5. Pre-existing conditions (classified, not repaired)

Full suite: `4 failed, 1122 passed, 2 skipped`. Machine-readable classification:
`Evidence/wp_d07_drift_matrix.json` → `pre_existing_failures_classification`.

| Test | Classification | Cause |
| --- | --- | --- |
| `test_golden_environment.py::test_canonical_golden_environment` | PRE_EXISTING_ENVIRONMENT | `Chromium cannot launch: BrowserType.launch: spawn EPERM` (sandbox denies process spawn) |
| `test_golden.py::test_golden[sample]` | PRE_EXISTING_ENVIRONMENT | baseline `renderer_backend='playwright'` vs actual `'fallback'`; the run stops at the environment contract before comparing documents |
| `test_packaging_metadata.py::test_pkg_documented_extras_exist_in_metadata` | PRE_EXISTING_DIRTY_TREE | the pre-existing modified `README.md` no longer documents the `windows`/`mermaid` extras |
| `test_packaging_metadata.py::test_pkg_readme_has_no_legacy_packaging_references` | PRE_EXISTING_DIRTY_TREE | working-tree `README.md` lacks `[project.entry-points`, which `git show HEAD:README.md` still contains |

Two skips are the pre-existing Windows + Word COM release gates
(`test_adjacent_tables.py:130`, `test_word_com_final_artifact.py:199`), unavailable in this sandbox.

Causal exclusion (file level): the complete Program D change set is

```text
md_converter/renderer/layout/table_fitting.py           (new)
md_converter/renderer/layout/figure_sizing.py           (FigureFitPlan + plan_figure_fit)
md_converter/renderer/word_renderer.py                  (table/image adapters)
md_converter/renderer/word_writer.py                    (atomic width/extent writes)
md_converter/tests/test_table_fitting.py                (new)
md_converter/tests/test_table_fitting_integration.py    (new)
md_converter/tests/test_figure_fitting.py               (new)
md_converter/tests/test_figure_fitting_integration.py   (new)
md_converter/tests/test_fitting_cross_profile.py        (new)
Doc/V2/Implementation/Program_D_Advanced_Table_Figure_Fitting/**  (Program D evidence)
```

None of the 4 failing tests' subjects (`README.md`, `pyproject.toml`, `tests/golden/**`,
DiagramPass/Mermaid, `golden_environment.py`) appears in that set.

## 6. Zero-drift matrix (summary)

| Drift | Status |
| --- | --- |
| Core drift | ZERO |
| Canonical drift | ZERO |
| QA semantic drift | ZERO |
| ConversionService semantic drift | ZERO |
| CLI / public API breaking drift | ZERO |
| Output naming / path drift | ZERO |
| Profile branching | ZERO |
| Content mutation | ZERO |
| Aspect-ratio distortion | ZERO |
| Readability-floor violations introduced | ZERO |
| Semantic Golden baseline change | ZERO |
| Introduced failures | ZERO |
| Open blockers | ZERO |

Full evidence per row: `Evidence/wp_d07_drift_matrix.json`.

## 7. Known limitations carried by Program D (honest scope record)

1. **Irreducible wide tables** — a table whose minimum width (columns × 1.2 cm) exceeds the
   effective content width is delivered at the readability floor with full content, a bounded font
   step and `RENDER006`; it may still exceed the content box. No landscape section is added by
   Program D (Product Specification §6.3).
2. **Landscape-table QA measurement** — `RenderedQA._check_table_overflow` measures column widths
   against `sections[0]` (portrait), so a fitted landscape table can raise the pre-existing
   `table_clipping` *warning*. Program D reports this and does not change the QA rule.
3. **Intrinsic-size no-upscale** — deferred, G2-class (WP-D01 §6.1, WP-D04 §3, WP-D05 §6).
4. **`image_width` configuration wiring** — discovered pre-existing defect (WP-D05 §5), reported
   and not repaired (`SPEC-INV-012`).
5. **Merged-cell fitting** — not reachable with the current parser/renderer (§3 above).

## 8. WP-D07 conclusion

Every required test layer ran against the integrated Program D code; every required artifact was
produced and measured; the drift matrix is zero in every category; the four remaining failures are
pre-existing and causally excluded from the Program D change set. No G2 condition was triggered and
no bounded correction pass was needed.

**Decision: PASS — next WP is D-08 (closure).**
