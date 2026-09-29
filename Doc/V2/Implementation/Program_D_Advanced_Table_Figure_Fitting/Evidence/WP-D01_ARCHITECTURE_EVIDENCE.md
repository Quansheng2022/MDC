# WP-D01 — Architecture Inspection & Fitting Contract Freeze

**Program:** D — Advanced Table Fitting + Advanced Figure Fitting
**Work Package:** D-01 (architecture inspection, no product behaviour change)
**Status:** PASS
**Baseline branch:** `master`
**Baseline HEAD:** `5f8bf2a26702c069d9190f5aa6aa937886f93eb4` (`close TOC heading localization fix`)
**Specification references:** `SPEC-FUNC-004`, `SPEC-FUNC-012`, `SPEC-FUNC-023`, `SPEC-ARCH-005`,
`SPEC-ARCH-009`, `SPEC-ARCH-010`, `SPEC-INV-002`, `SPEC-INV-003`, `SPEC-QA-005`,
`Program_D_Product_Specification.md` §3, §6–§9, §11.

---

## 1. Baseline capture (real, not assumed)

```text
$ git rev-parse --abbrev-ref HEAD   -> master
$ git rev-parse HEAD                -> 5f8bf2a26702c069d9190f5aa6aa937886f93eb4
$ git status --short
 M .gitignore
 M README.md
 M md_converter/cli.py
?? Doc/... (untracked documentation tree, including Program D inputs)
?? tests/ , dist/ , release/ , review_packages/ , MDC_p11_* (untracked artifact trees)
$ git diff --name-status
M   .gitignore
M   README.md
M   md_converter/cli.py
```

The three tracked dirty files are unrelated to Program D and are treated as the documented
pre-existing dirty state (Program D Implementation Plan §2). They are never staged.

### Baseline architecture-related test behaviour

An architecture-focused subset was executed against the untouched baseline
(`-p no:cacheprovider`, project `.venv`). Result: see §7 of this document for the recorded
run output.

---

## 2. Page geometry authority

| Concern | Single authority today | Location |
| --- | --- | --- |
| Effective content box (delivered document) | current `section` geometry: `page_width/height − margins` | `WordRenderer._figure_bounds_cm()` (`md_converter/renderer/word_renderer.py:545`) and `RenderedQA._check_figure_geometry/_check_table_overflow` |
| Section geometry writer | `WordWriter.set_section_orientation()` (A4 portrait/landscape only) | `md_converter/renderer/word_writer.py:356` |
| Page margins writer | `WordRenderer._apply_page_margins()` from the **effective theme** `page_margins_cm` | `md_converter/renderer/word_renderer.py:684` |
| Reference/failsafe geometry | `PageGeometry` (A4, 1 in) used only when section geometry is unavailable | `md_converter/renderer/layout/section_manager.py:20` |
| Effective profile geometry | `theme_presentation_overrides(profile)` → `V15Theme.with_presentation_overrides` → `page.margins` | `md_converter/profiles/theme_overrides.py:74`, `md_converter/renderer/themes/v15_theme.py` |

Conclusion: the effective content box is derived from the **real rendered section**, and the five
Professional Output Profiles reach that geometry only through resolved theme margins
(`SPEC-FUNC-012`, `SPEC-ARCH-009`). No profile-ID branch exists in the geometry path. This is the
geometry authority Program D must consume.

## 3. Table path (current state)

| Concern | Authority today | Detail |
| --- | --- | --- |
| Table structure | `WordRenderer.visit_Table` → `WordWriter.start_table(rows, cols)` | `md_converter/renderer/word_renderer.py:365`, `md_converter/renderer/word_writer.py:435` |
| Table style name | theme `table.style`, applied in the renderer; borders/header fill re-applied by the Post-Processor | `word_renderer.py:381`, `post_processor.py:_style_tables` |
| Table typography | theme `table.font_size` via `WordRenderer._size_for("table")` | `word_renderer.py:648` |
| Column width allocation | **none** — `python-docx add_table` leaves `w:tblW type="auto"` and no `w:tblLayout`; delivery defers to Word autofit | probe: `Table.autofit == True` |
| Width estimation (decision only) | `estimate_table_width_cm()` (`max(min_width, max_cell_chars × char_width)`) used by `DecisionEngine`/`SectionManager` **only** to decide a landscape section | `md_converter/renderer/layout/section_manager.py:33`, `decision_engine.py:108` |
| Table QA | `RenderedQA._check_table_overflow` — **skips tables it classifies as autofit**, therefore today it never measures a rendered table width | `md_converter/renderer/layout/rendered_qa.py:170`, `:213` |
| Style gate | `FinalArtifactQA._check_table_styling` requires a `Grid`-family style, a header row and effective borders | `final_artifact_qa.py:335` |

The frozen theme already declares the intent Program D implements:

```yaml
table:
  width: {mode: fit_content_width}
  constraints: {min_width: 1.2cm, max_width: content_width}
  overflow: {long_text: wrap, url: break, code: shrink_or_break}
  landscape_candidate: true
```

`CANONICAL_SPEC.md` contains **no** frozen requirement on table width fitting
(`SPEC-FUNC-004` covers only header repetition and numeric-column alignment; `SPEC-ARCH-005`
assigns table *styling* to the Post-Processor; `SPEC-ARCH-009` assigns *structure* to the
Renderer via themes). Table fitting is therefore unconstrained → available as G1.

## 4. Figure path (current state)

| Concern | Authority today | Detail |
| --- | --- | --- |
| Fit decision (pure) | `fit_figure_size()` | `md_converter/renderer/layout/figure_sizing.py:170` |
| Theme policy parsing | `figure_policy_from_data/from_theme` | `figure_sizing.py:86`, `:128` |
| Bounds assembly | `WordRenderer._figure_bounds_cm()` → `FigureBounds` | `word_renderer.py:545`; `target = min(config image_width, max_width)` |
| Pixel→DOCX placement | `WordWriter._add_fitted_picture()` | `word_writer.py:676` |
| Delivered-extent QA | `RenderedQA._check_figure_geometry` (real inline-shape measurement) | `rendered_qa.py:78` |
| Diagnostic | `RENDER005` when the fitted width falls below theme `figure.min_width` | `word_renderer.py:511` |

Frozen contract: **`SPEC-FUNC-023`** — effective width/height from the real section,
`target width = min(config image_width, effective width)`, aspect ratio preserved, never enlarged
beyond the target width, never outside the content box, `move_to_next_page → scale_down → warn`,
bounded by `figure.min_width` (8 cm) with a structured warning.

## 5. Integration boundaries that already exist and are reused

* `CLI / GUI / Batch → ConversionService → CompilerCore → Renderer → RenderedQA → PostProcessor →
  FinalArtifactQA` is the single conversion path; table and figure presentation is reached from
  `WordRenderer`, so any fitting authority wired there is automatically shared by single-file,
  batch and CLI conversion (Program D §3.3) with **no** duplicate integration code.
* `RenderedQA` runs after render and before the Post-Processor, and `FinalArtifactQA` re-runs the
  same measurement on the published artifact (`SPEC-QA-004`/`SPEC-QA-005`). A fitting decision
  applied in the renderer is therefore measured twice by existing gate infrastructure.
* `StyleResolver` is the only formatting authority (`SPEC-ARCH-009`); the fitting policies must stay
  pure and receive resolved values rather than reading profiles or documents themselves.

## 6. Required Decision Record

| Decision | Value |
| --- | --- |
| Current table layout authority | none (Word autofit) — no explicit column widths, no `tblLayout` |
| Current figure sizing authority | `fit_figure_size()` + `_figure_bounds_cm()` (split, but single decision function) |
| Effective page geometry authority | rendered `section` box via `section.page_* − margins`; `PageGeometry` only as failsafe |
| Proposed single table fitting authority | new pure policy `md_converter/renderer/layout/table_fitting.py::plan_table_fit` |
| Proposed single figure fitting authority | `md_converter/renderer/layout/figure_sizing.py::plan_figure_fit` (same module as today) |
| Proposed integration point | thin adapters in the **Renderer** (`visit_Table`, `visit_Image`) plus the existing `WordWriter` primitives — matching Program D §9 ("renderer/postprocessor integration: thin adapters that consume those decisions") and the existing figure path |
| G1 path available | **YES** |
| G2 trigger discovered | **NO for the program as scoped in §7 below** |

### 6.1 G2 boundary discovered during inspection (recorded, not worked around)

Program D Product Specification §7.2 states the default policy *"Do not upscale a raster image
merely to fill the page."* Inspection shows this stricter reading (never enlarge above the image's
own intrinsic size) is **not** available as G1:

* `SPEC-FUNC-023` is FROZEN and normative: *"目标宽度 = min(配置 `image_width`, 有效宽度) … 先
  `move_to_next_page`（**按目标宽度插入**）"* — figures are inserted **at the target width**, and
  only "never enlarge beyond the target width" is asserted as a bound.
* The program that froze that rule explicitly listed *"upscaling small images"* under **Out of
  scope** (`P12/P12_REQUIREMENTS.md`, §1 "Out of scope"), i.e. the current target-width
  enlargement is intentional accepted behaviour, not an oversight.
* Program D Product Specification §3.2 itself permits this: *"avoid unintended enlargement of
  small raster images **unless existing behavior explicitly requires enlargement**"*. The frozen
  target-width insertion rule is exactly such an explicitly required behaviour.

Changing the default to intrinsic-size no-upscale would require
`ADR → Spec Update → SPEC_CHANGELOG → Re-freeze` (AGENTS.md Governance Rule 2) and therefore
triggers **G2**. Program D therefore:

1. keeps the frozen target-width insertion behaviour (no Canonical, Core, QA-semantic, API or
   output-naming drift);
2. implements a *single, explicit, tested* figure fitting authority that documents and enforces the
   frozen bounds (content box, target width as ceiling, aspect ratio, height bound, readability
   floor) and introduces no new/page-filling upscaling;
3. records **intrinsic-size no-upscale of small raster figures as DEFERRED (G2-class)** in D-04,
   D-05, D-07 and the D-08 closure evidence.

This keeps the Program D pipeline inside the G0/G1 authority grant of the Master Instruction §2/§16
while remaining truthful about what the frozen contract makes unavailable.

* Landscape sections already exist (`DecisionEngine` → `BlockPlan.landscape` → `visit_Table`) for
  tables that exceed portrait width. Program D **preserves** this existing behaviour; it adds no new
  orientation or section logic (Product Spec §4 non-goals, §6.3).
* Column-width allocation is a *structure* concern (`SPEC-ARCH-009`: "Renderer controls structure",
  theme YAML: "YAML 定义 WHAT，Python 决定 HOW"); borders, header fill and font normalisation stay
  with the Post-Processor (`SPEC-ARCH-005`). No ownership is moved.

## 7. Baseline verification run (architecture-related subset)

```text
.venv\Scripts\python.exe -m pytest md_converter/tests/test_figure_sizing.py
    md_converter/tests/test_layout_plan.py md_converter/tests/test_page_geometry.py
    md_converter/tests/test_quality_gate.py md_converter/tests/test_post_processor.py
    md_converter/tests/test_simple_table_pass.py md_converter/tests/test_adjacent_tables.py
    md_converter/tests/test_output_profile_rendering.py -p no:cacheprovider -q
```

Recorded result (baseline, before any Program D product code):

```text
90 passed, 1 skipped in 22.06s
SKIPPED md_converter/tests/test_adjacent_tables.py:130
   Requires Windows + installed Word + pywin32 (Windows Release Gate)
   Probe detail: WORD_COM_UNAVAILABLE|dispatch|com_error|(-2147023584, 'A specified logon
   session does not exist. It may already have been terminated.', None, None)
```

The single skip is the pre-existing Windows/Word COM release-gate test, unrelated to Program D.

## 8. WP-D01 conclusion

* Program D is implementable as a bounded G1 presentation/layout enhancement.
* Single table fitting authority: `table_fitting.py::plan_table_fit` (new, pure).
* Single figure fitting authority: `figure_sizing.py::plan_figure_fit` (extends existing pure module).
* Integration: thin Renderer adapters over the existing `WordWriter` primitives.
* No Canonical/Core/QA redesign, no parser/AST redesign, no pagination engine, no new dependency.
* Open G2-class item: intrinsic-size no-upscale for small raster figures — deferred with evidence.

**Decision: G1 path available — proceed to WP-D02.**
