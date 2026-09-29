# WP-D05 — Figure Renderer Integration

**Program:** D — Advanced Table Fitting + Advanced Figure Fitting
**Work Package:** D-05 (single figure fitting authority wired into the existing image path)
**Status:** PASS
**Baseline for this WP:** `d059de1` (`D-04 implement deterministic figure fitting policy`)
**Specification references:** `SPEC-FUNC-008`, `SPEC-FUNC-013`, `SPEC-FUNC-023`, `SPEC-QA-005`,
`SPEC-INV-002`, `SPEC-INV-003`, `SPEC-ARCH-009`, `SPEC-ARCH-012`, Product Specification
§3.2, §7, §9, §11.2, §12.

---

## 1. Integration point

```text
CompilerContext.compile
  -> WordRenderer.visit_Image                     (adapter: bounds + reporting)
       -> WordWriter.add_image(bounds=...)
            -> _add_fitted_picture                (measure + atomic write only)
                 -> plan_figure_fit(...)          (WP-D04 single authority)
```

| File | Change |
| --- | --- |
| `md_converter/renderer/word_writer.py` | `ImagePlacement` now carries `aspect_ratio`, `height_limited`, `width_limited`; `_add_fitted_picture` consumes `plan_figure_fit` instead of its own arithmetic (`fit_figure_size` import removed from the writer) |
| `md_converter/renderer/word_renderer.py` | `RENDER005` payload extended with the aspect ratio and the two reduction reasons (no new diagnostic code) |
| `md_converter/tests/test_figure_fitting_integration.py` | new end-to-end regression (12 tests) |

Consequences:

* **no duplicated fitting logic** — the writer no longer re-implements the shrink arithmetic; the
  decision provenance (why a figure got smaller) is now observable;
* **no new diagnostic codes** — deliberately: the Golden baseline compares the whole diagnostics
  array, and adding an informational diagnostic could silently drift an accepted baseline
  (`SPEC-INV-011`). The existing `RENDER005` channel is enriched instead;
* **vector/diagram path untouched** — `DiagramPass`, the Mermaid/Playwright path and the
  `data:image/svg+xml` fallback are unchanged (`SPEC-ARCH-012`);
* **measurement infrastructure unchanged** — `RenderedQA`/`FinalArtifactQA` continue to measure the
  delivered inline shapes (`SPEC-QA-005`).

## 2. Measured artifacts (real output)

Generator: `CompilerContext.compile` with `word_com=False, enable_cover=False, toc=False`,
default profile unless stated. Raw data: `Evidence/wp_d05_figure_measurements.json`;
artifacts: `Evidence/samples/figure_*.docx` (page geometry is the default A4 + 1 in box
15.92 × 24.62 cm, or the 5.0 cm-margin variant 11.00 × 24.62 cm).

```text
figure_small           px=82x41    box=15.92    rendered=12.7000 x 6.3500   ar_ok=True  within=True  QA=PASS  overflow=0
figure_wide            px=400x100  box=15.92    rendered=12.7000 x 3.1750   ar_ok=True  within=True  QA=PASS  overflow=0
figure_tall            px=30x70    box=15.92    rendered=10.5516 x 24.6204  ar_ok=True  within=True  QA=PASS  overflow=0
figure_landscape       px=200x80   box=15.92    rendered=12.7000 x 5.0800   ar_ok=True  within=True  QA=PASS  overflow=0
figure_diagram         px=600x100  box=15.92    rendered=12.7000 x 2.1167   ar_ok=True  within=True  QA=PASS  overflow=0
figure_wide_narrow_box px=400x100  box=11.00    rendered=10.9996 x 2.7499   ar_ok=True  within=True  QA=PASS  overflow=0
```

Five-profile matrix for one representative wide figure (`px=400x100`):

```text
professional_report  content_width=15.9209  rendered=12.7000 x 3.1750  within=True  QA=PASS  codes=[]
business_report      content_width=17.0004  rendered=12.7000 x 3.1750  within=True  QA=PASS  codes=[]
academic             content_width=15.0001  rendered=12.7000 x 3.1750  within=True  QA=PASS  codes=[]
technical            content_width=16.6017  rendered=12.7000 x 3.1750  within=True  QA=PASS  codes=[]
clean_minimal        content_width=15.9209  rendered=12.7000 x 3.1750  within=True  QA=PASS  codes=[]
```

Reading of the measurements:

* aspect ratio is preserved in every case (`ar_ok=True`, computed from the embedded PNG's own
  IHDR dimensions, not from the requested size);
* every delivered figure is inside its content box, `figure_overflow = 0`, and the gate is `PASS`;
* the tall figure is height-bounded (`10.5516 = 24.6204 × 30/70`) — the P12-CAND-002 behaviour is
  preserved unchanged;
* the 11.00 cm content box caps the frozen 12.7 cm target (`width_limited`), proving the geometry
  path drives the decision without any profile or theme *name* branching;
* profile differences appear as resolved content widths only; the delivered figure is identical
  because the frozen 12.7 cm target fits every profile box;
* `figure_diagram` (ASCII → Mermaid → sandbox fallback SVG → raster) still renders inside the box;
  its `ASCI004/ASCI001/DIAG002` codes are the pre-existing sandbox conditions (no `mmdc`, Chromium
  cannot spawn), not Program D behaviour.

## 3. Requirement mapping

| WP-D05 requirement | Status | Evidence |
| --- | --- | --- |
| source image unchanged | PASS | writer re-reads the original part; no re-encode/crop path exists |
| image relationship preserved | PASS | `test_image_relationship_and_package_integrity` (package parts + `word/media` + `zipfile.testzip()`) |
| image order preserved | PASS | single-figure artifacts; multi-figure order untouched by the change |
| alignment untouched unless already owned by existing rules | PASS | `figure_style()` alignment logic unchanged |
| captions / cross references untouched | PASS | not part of Program D; no caption code touched |
| document meaning preserved | PASS | only extent attributes are written |
| baseline small-image behaviour | PASS | `test_baseline_small_image_behaviour_is_unchanged` (12.7 × 6.35 cm) |
| profile geometry variation | PASS | 5-profile matrix + `test_resolved_geometry_variation_changes_the_delivered_figure` |
| diagram / vector behaviour | PASS | `test_generated_diagram_figure_keeps_the_existing_behaviour` + `figure_diagram` artifact |
| readable-size warning unchanged | PASS | `test_narrow_figure_below_min_width_still_reports_render005` |
| deterministic repeated conversion | PASS | `test_repeated_conversion_is_deterministic` |

## 4. Regression evidence

```text
$ .venv\Scripts\python.exe -m pytest md_converter/tests/test_figure_fitting.py \
      md_converter/tests/test_figure_sizing.py md_converter/tests/test_figure_fitting_integration.py \
      md_converter/tests/test_table_fitting.py md_converter/tests/test_table_fitting_integration.py \
      md_converter/tests/test_acceptance.py md_converter/tests/test_ascii_mermaid_pass.py \
      md_converter/tests/test_ascii_mermaid_service.py md_converter/tests/test_output_profile_rendering.py \
      md_converter/tests/test_page_geometry.py -p no:cacheprovider
188 passed in 52.86s
```

Quality checks on the touched files:

```text
ruff check         -> All checks passed!
black --check      -> 3 files would be left unchanged (after one reflow inside the new test file)
isort --check-only -> clean
```

## 5. Defect discovered during D-05 and deliberately **not** fixed (outside Program D scope)

`WordRenderer._figure_bounds_cm()` reads the configured target width from
`self.ctx.config.get("image_width", 5)`, but `CompilerContext.create()` builds the
`RenderContext` **without** a `config` argument (`compiler.py:155`), so `WordRenderer.ctx.config`
is always `{}`. The user-facing `image_width` configuration key is therefore never honoured by the
renderer; every figure uses the built-in 5 in / 12.7 cm fallback.

Verified during this WP:

```text
CompilerContext.create({"image_width": 10}).config["image_width"]  -> 10   (resolved config is correct)
RenderContext created by CompilerContext.create(...)              -> config == {}
```

This is a pre-existing configuration-wiring defect that predates Program D and is **not** part of
the Program D change plan (`SPEC-INV-012`: report, do not modify). Program D consequently:

* does not change `CompilerContext.create` / `RenderContext` wiring;
* validates the width-capped behaviour through the resolved **theme geometry** instead
  (the 5.0 cm-margin theme variant), which is the same code path a correct `image_width` value
  would take.

Recommendation for a future, separately authorised change: pass the resolved configuration into
`RenderContext` (or read the target width from a render-context value) so that the documented
`image_width` key becomes effective. This is reported here as an open observation, not as a
Program D defect.

## 6. Deferred item carried forward (G2-class)

Intrinsic-size no-upscale for small raster figures is **not** implemented, for the reasons recorded
in WP-D01 §6.1 and WP-D04 §3 (it would change the frozen `SPEC-FUNC-023` target-width insertion
rule and needs `ADR → Spec Update → SPEC_CHANGELOG → Re-freeze`). Program D guarantees that no new
upscaling exists and that the target width remains a hard ceiling.

## 7. Scope discipline

`md_converter/renderer/word_writer.py`, `md_converter/renderer/word_renderer.py` and the new
integration test are the only product/test files touched in this WP. No theme, config, diagram
service, post-processor or QA-contract change was made.

## 8. WP-D05 conclusion

The D-04 authority is now the only figure-fitting decision on the image path, with per-figure
decision provenance, unchanged frozen sizing semantics, preserved image/package integrity,
verified five-profile behaviour and measured artifacts. The discovered `image_width` wiring defect
and the G2-class no-upscale item are both recorded rather than silently changed.

**Decision: PASS — next WP is D-06 (cross-profile / batch / workflow hardening).**
