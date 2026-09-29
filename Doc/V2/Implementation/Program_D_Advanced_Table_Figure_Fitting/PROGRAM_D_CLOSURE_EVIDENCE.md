# Program D — Advanced Table Fitting + Advanced Figure Fitting
## Closure Evidence

**Program:** D
**Product:** MD Converter
**Status:** **CLOSED / ACCEPTED**
**Specification:** `Doc/V2/Product/Program_D_Product_Specification.md`
**Implementation plan:** `Doc/V2/Implementation/Program_D/Program_D_Implementation_Plan.md`
**Master instruction:** `Doc/V2/Implementation/Program_D/Program_D_Master_Instruction.md`
**Canonical authority:** `CANONICAL_SPEC.md` (FROZEN, unchanged)

---

## 1. Identity

| Item | Value |
| --- | --- |
| Starting branch | `master` |
| Starting HEAD | `5f8bf2a26702c069d9190f5aa6aa937886f93eb4` (`close TOC heading localization fix`) |
| Ending HEAD | the D-08 closure commit containing this document |
| Work packages | D-01 … D-08, each independently verified, evidenced and committed |
| Program commits | 7 implementation/verification commits + this closure commit |
| G2 conditions triggered | **0** |
| Blocked work packages | **0** |
| Bounded correction passes used | 0 (no work package failed verification) |

## 2. Commit chain

```text
05b05c7  D-01 freeze table and figure fitting architecture
0239c3f  D-02 implement deterministic table fitting policy
81b1594  D-03 integrate advanced table fitting
d059de1  D-04 implement deterministic figure fitting policy
b789bdb  D-05 integrate advanced figure fitting
e26d709  D-06 harden fitting across profiles and workflows
2301d1d  D-07 verify advanced table and figure fitting
<D-08>   D-08 close advanced table and figure fitting
```

Every commit stages exact files only; the pre-existing dirty state (`.gitignore`, `README.md`,
`md_converter/cli.py`) and the unrelated untracked trees were never staged.

## 3. Files changed by Program D

Product code (4 files, 2 new):

```text
md_converter/renderer/layout/table_fitting.py            NEW  pure table fitting authority
md_converter/renderer/layout/figure_sizing.py            FigureFitPlan + plan_figure_fit (single figure authority)
md_converter/renderer/word_renderer.py                   thin adapters: visit_Table / visit_Image, shared geometry helper
md_converter/renderer/word_writer.py                     atomic writes: tblLayout/tblW/gridCol/tcW, image extents
```

Tests (5 files, all new):

```text
md_converter/tests/test_table_fitting.py                  25 policy tests
md_converter/tests/test_table_fitting_integration.py      12 renderer integration tests
md_converter/tests/test_figure_fitting.py                 24 policy tests (17 test functions)
md_converter/tests/test_figure_fitting_integration.py     12 renderer integration tests
md_converter/tests/test_fitting_cross_profile.py          15 cross-profile / batch / CLI tests
```

Evidence:

```text
Doc/V2/Implementation/Program_D_Advanced_Table_Figure_Fitting/
  Evidence/WP-D01_ARCHITECTURE_EVIDENCE.md
  Evidence/WP-D02_TABLE_POLICY_EVIDENCE.md
  Evidence/WP-D03_TABLE_INTEGRATION_EVIDENCE.md
  Evidence/WP-D04_FIGURE_POLICY_EVIDENCE.md
  Evidence/WP-D05_FIGURE_INTEGRATION_EVIDENCE.md
  Evidence/WP-D06_CROSS_PROFILE_BATCH_EVIDENCE.md
  Evidence/WP-D07_INTEGRATED_VERIFICATION_EVIDENCE.md
  Evidence/wp_d03_table_measurements.json
  Evidence/wp_d05_figure_measurements.json
  Evidence/wp_d06_cross_profile_matrix.json
  Evidence/wp_d07_artifact_measurements.json
  Evidence/wp_d07_drift_matrix.json
  Evidence/wp_d07_focused_tests.txt
  Evidence/wp_d07_full_suite.txt
  Evidence/wp_d07_lint_format.txt
  Evidence/samples/*.docx                       (21 measured DOCX artifacts)
  PROGRAM_D_CLOSURE_EVIDENCE.md                 (this document)
```

No compiler core, parser, AST, pipeline pass, profile, config, diagnostics, post-processor, quality
gate, theme, Golden baseline or CLI file was modified.

## 4. Table fitting — policy summary

Single authority: `md_converter/renderer/layout/table_fitting.py::plan_table_fit`.

```text
signal_i  = max visible cell characters of column i          (cheap, language-agnostic)
natural_i = clamp(signal_i, 1, 48) x 0.19 cm, raised to the 1.2 cm minimum column width
required  = Σ natural_i ;  min_total = columns x 1.2 cm

1) required <= content_width and required >= 0.6 x content_width -> fill content width
2) required <= content_width and required <  0.6 x content_width -> keep natural width (narrow)
3) required >  content_width and min_total <= content_width      -> fill, shrink only the excess above the floor
4) min_total >  content_width                                    -> keep floor + full content, squeezed = True

font = base; if squeezed: font = base - 0.5pt; clamped to [8.5pt, base]
```

Delivery: `w:tblLayout type="fixed"`, `w:tblW` (dxa), `w:tblGrid/w:gridCol`, `w:tcPr/w:tcW`.
Decision and execution are separated: the policy is pure, the renderer consumes it, the writer only
writes. An irreducible wide table is preserved, reported via `RENDER006` (with the full decision
payload) and never silently degraded; a fitting failure degrades to the previous table with
`RENDER007`.

## 5. Figure fitting — policy summary

Single authority: `md_converter/renderer/layout/figure_sizing.py::plan_figure_fit`
(`fit_figure_size` is a delegating wrapper, so no duplicated arithmetic remains).

```text
aspect        = intrinsic px width / px height                    (never changed)
width         = min(config target, effective content width)       (target stays a hard ceiling)
height        = width / aspect
if height > effective content height: height = content height; width = height x aspect
below_min_width reported, never enforced by cropping
```

Frozen `SPEC-FUNC-023` semantics are consumed, not altered: no new upscaling exists, the aspect
ratio is preserved, the figure never leaves the content box, and the existing `RENDER005`
readability-floor warning is kept (with a richer payload: aspect ratio and the two reduction
reasons). `ImagePlacement` now carries `aspect_ratio`, `height_limited`, `width_limited`.

## 6. Architecture integration points

```text
CLI / GUI / Serial Batch
  -> ConversionService
     -> CompilerContext.compile
        -> DecisionEngine -> LayoutPlan            (unchanged; landscape table decision untouched)
        -> StaticQA                                (unchanged)
        -> WordRenderer                            (ADAPTER: visit_Table / visit_Image)
             -> plan_table_fit / plan_figure_fit   (single pure authorities)
             -> WordWriter                         (atomic OOXML writes only)
        -> RenderedQA                              (unchanged; now actually measures fitted tables)
        -> DocxPostProcessor                       (unchanged: borders, header fill, TOC, cover)
        -> FinalArtifactQA                         (unchanged; re-measures the published artifact)
```

* one geometry point (`WordRenderer._effective_content_size_cm`) feeds both fitting authorities;
* no fitting logic exists in the GUI, batch, CLI, post-processor or QA layers;
* ownership is preserved (`SPEC-ARCH-005` styling stays with the Post-Processor, `SPEC-ARCH-009`
  structure stays with the Renderer through resolved theme values, `SPEC-ARCH-010` layout decisions
  still come from the `LayoutPlan`).

## 7. Profile / batch / workflow behaviour

```text
profile              content_width  table_total  fills_box  figure         gates
professional_report  15.9209        15.9226      True       12.70 x 3.175  PASS/PASS/PASS/PASS
business_report      17.0004        16.9986      True       12.70 x 3.175  PASS/PASS/PASS/PASS
academic             15.0001        15.0001      True       12.70 x 3.175  PASS/PASS/PASS/PASS
technical            16.6017        16.6017      True       12.70 x 3.175  PASS/PASS/PASS/PASS
clean_minimal        15.9209        15.9226      True       12.70 x 3.175  PASS/PASS/PASS/PASS
```

* profile-aware through **effective geometry**, never through profile names (static scan test);
* default profile is byte-equivalent to the no-profile baseline for the fitting facts;
* single-file, Serial Batch, GUI-worker and CLI paths all produce fitted artifacts;
* no state leakage between serially converted files (1/3/6-row documents on one service instance,
  compared against a fresh service);
* repeated conversion is deterministic per profile.

## 8. Measured artifact summary

Tables (`wp_d03_table_measurements.json`, `wp_d06_cross_profile_matrix.json`,
`wp_d07_artifact_measurements.json`):

| Case | Result |
| --- | --- |
| normal 4-column | 15.9191 cm of 15.9209 cm content, 9.5pt, PASS, 0 diagnostics |
| wide 8-column | 15.9173 cm, 9.5pt, PASS, 0 diagnostics |
| long-text 2-column | 15.9209 cm, content-weighted 1.85 / 14.07 cm, PASS |
| numeric 6-column | 7.4577 cm (narrow → not stretched), PASS |
| 25-column irreducible | 29.9861 cm, 1.2 cm floor per column, font 9.0pt, `RENDER006`, PASS_WITH_WARN (never FAIL) |
| wide table × 5 profiles | 15.92 / 17.00 / 15.00 / 16.60 / 15.92 cm, all PASS |
| merged cells | not reachable through the current parser/renderer (probe recorded) |

Figures (`wp_d05_figure_measurements.json`):

| Case | Intrinsic | Content box | Rendered | Aspect | QA |
| --- | --- | --- | --- | --- | --- |
| small raster | 82×41 px | 15.92 × 24.62 | 12.7000 × 6.3500 cm | preserved | PASS |
| very wide | 400×100 px | 15.92 × 24.62 | 12.7000 × 3.1750 cm | preserved | PASS |
| very tall | 30×70 px | 15.92 × 24.62 | 10.5516 × 24.6204 cm | preserved | PASS |
| landscape | 200×80 px | 15.92 × 24.62 | 12.7000 × 5.0800 cm | preserved | PASS |
| vector/diagram output | 600×100 px fallback | 15.92 × 24.62 | 12.7000 × 2.1167 cm | preserved | PASS |
| oversized target / narrow box | 400×100 px | 11.00 × 24.62 | 10.9996 × 2.7499 cm | preserved | PASS |
| representative × 5 profiles | 400×100 px | 15.92–17.00 | 12.7000 × 3.1750 cm | preserved | PASS |

## 9. Test totals

```text
Program D focused (5 files, verbose)         88 passed
  test_table_fitting.py                      25 passed
  test_table_fitting_integration.py          12 passed
  test_figure_fitting.py                     24 passed
  test_figure_fitting_integration.py         12 passed
  test_fitting_cross_profile.py              15 passed
Pre-existing figure suite still green        test_figure_sizing.py 13 passed
Workflow suite (GUI batch/worker/lifecycle,
  application layer, public API, cross-profile)  185 passed
Full suite `md_converter/tests`              1122 passed, 4 failed (all pre-existing), 2 skipped
```

Clarification of one wording in the sealed WP-D04 evidence: its deliverable table counts the 17
**test functions** in `test_figure_fitting.py`, while `pytest` reports 24 **test cases** after
parametrisation (the WP-D04 run line `37 passed` = 24 figure cases + 13 pre-existing
`test_figure_sizing.py` cases). Both numbers are consistent; the case count is used above.

## 10. Lint / format results (exact touched files)

```text
ruff check               All checks passed!
black --check --no-cache 9 files would be left unchanged
isort --check-only       clean
```

Log: `Evidence/wp_d07_lint_format.txt`. One cosmetic `black` reflow inside
`md_converter/tests/test_figure_fitting.py` (single signature line) was applied during WP-D07's
quality check and is committed with this closure; the file was re-run green afterwards (88 focused
tests passed after the reflow).

## 11. Known pre-existing failures (not repaired)

| Test | Classification | Cause |
| --- | --- | --- |
| `test_golden_environment.py::test_canonical_golden_environment` | environment | `Chromium cannot launch: BrowserType.launch: spawn EPERM` |
| `test_golden.py::test_golden[sample]` | environment | baseline backend `playwright` vs sandbox `fallback`; stops at the environment contract |
| `test_packaging_metadata.py::test_pkg_documented_extras_exist_in_metadata` | dirty tree | pre-existing modified `README.md` no longer documents `windows`/`mermaid` extras |
| `test_packaging_metadata.py::test_pkg_readme_has_no_legacy_packaging_references` | dirty tree | working-tree `README.md` lacks `[project.entry-points`, which `HEAD:README.md` still contains |

Two skips are the pre-existing Windows + Word COM release gates
(`test_adjacent_tables.py:130`, `test_word_com_final_artifact.py:199`).

Causal exclusion: the Program D change set (§3) contains none of the failing tests' subjects.

## 12. Environment observations

1. `black` without `--no-cache` does not terminate in this sandbox (its global cache directory is
   outside the writable roots); every Program D format check uses `--no-cache`.
2. Un-redirected console stdout raises `UnicodeEncodeError` (cp1252) on the pre-existing emoji
   progress prints in the Post-Processor. This is the same condition recorded by P12-09
   (`wp04_cp1252_reconfirm.json`); Program D code paths do not print, and evidence generation
   redirects stdout.
3. `mmdc` is absent and Chromium cannot be spawned (`spawn EPERM`), so diagram documents use the
   documented Mermaid fallback path; figure fitting still delivers content-box-compliant images.

## 13. Deferred items (explicit, with reason)

| Item | Reason | Required authority |
| --- | --- | --- |
| Intrinsic-size no-upscale for small raster figures (Product Specification §7.2, §11.2) | would change the FROZEN `SPEC-FUNC-023` "insert at target width" rule; the freezing program listed "upscaling small images" as out of scope | ADR → Spec Update → SPEC_CHANGELOG → Re-freeze (G2) |
| Tall-figure height fitting refinements | currently already implemented from section geometry and verified; no further bounded change identified | none needed |
| `image_width` configuration wiring defect (`CompilerContext.create` does not pass config into `RenderContext`) | pre-existing defect outside the Program D change plan (`SPEC-INV-012`) | separate authorised change |
| Merged-cell fitting | not reachable: the Markdown parser emits no spanned cells and the renderer has no merge path | separate feature authorisation |
| Landscape-table QA measurement rule (`RenderedQA` measures against `sections[0]`) | pre-existing QA behaviour; changing it would alter a QA semantic contract | G2 if changed |

## 14. Drift matrix (final)

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

Per-row evidence: `Evidence/wp_d07_drift_matrix.json`.

## 15. Definition of Done

| Required item | Status |
| --- | --- |
| D-01 … D-07 independently verified, evidenced and committed | PASS |
| Every work package has an evidence file | PASS (7 × `WP-Dxx_*_EVIDENCE.md`) |
| Table fitting PASS | PASS |
| Figure fitting PASS | PASS |
| Cross-profile PASS | PASS |
| Batch PASS | PASS |
| Deterministic behaviour PASS | PASS |
| Content mutation = 0 | PASS |
| Aspect-ratio distortion = 0 | PASS |
| Readability-floor violations introduced = 0 | PASS |
| Core drift = 0 | PASS |
| Canonical drift = 0 | PASS |
| QA semantic drift = 0 | PASS |
| ConversionService semantic drift = 0 | PASS |
| CLI / public API breaking drift = 0 | PASS |
| Output naming / path drift = 0 | PASS |
| Profile branching = 0 | PASS |
| Introduced failures = 0 | PASS |
| Open blockers = 0 | PASS |

## 16. Final recommendation

Program D delivers the intended presentation improvement inside the existing compiler architecture:
Word tables now arrive with deterministic, content-aware column widths that use the effective page
content width, and figures are fitted through one explicit authority with measured, aspect-preserving
bounds. Document meaning, cell values, image content, image relationships, the frozen theme, the
Canonical specification, the QA contracts, the ConversionService semantics and the CLI/public API are
all unchanged.

The one Product-Specification item that cannot be delivered as G1 — intrinsic-size no-upscale for
small raster figures — is recorded as a G2-class deferral with its Canonical citation rather than
being implemented behind the freeze, and the pre-existing `image_width` wiring defect discovered
during integration is reported for a separately authorised change.

**Program D — Advanced Table Fitting + Advanced Figure Fitting: CLOSED / ACCEPTED**

No further roadmap programme is started by this closure.
