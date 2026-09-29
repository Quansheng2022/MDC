# WP-D04 — Figure Fitting Policy

**Program:** D — Advanced Table Fitting + Advanced Figure Fitting
**Work Package:** D-04 (one deterministic figure fitting authority)
**Status:** PASS
**Baseline for this WP:** `81b1594` (`D-03 integrate advanced table fitting`)
**Specification references:** `SPEC-FUNC-008`, `SPEC-FUNC-023`, `SPEC-QA-005`, `SPEC-INV-002`,
`SPEC-INV-003`, `SPEC-INV-006`, `Program_D_Product_Specification.md` §3.2, §7, §9, §11.2.

---

## 1. Deliverable

| Artifact | Path | Nature |
| --- | --- | --- |
| Single figure fitting authority | `md_converter/renderer/layout/figure_sizing.py` (`FigureFitPlan` + `plan_figure_fit`, new) | pure / no I/O / no Word objects / no profile-ID branch |
| Focused policy tests | `md_converter/tests/test_figure_fitting.py` (new) | 17 tests |

`fit_figure_size()` is kept as a thin, backwards-compatible wrapper that now **delegates** to
`plan_figure_fit()`, so there is exactly one implementation of the fitting arithmetic
(Product Specification §9: one authority per concern).

## 2. Policy (frozen SPEC-FUNC-023 semantics, no new upscaling)

```text
aspect          = intrinsic_width_px / intrinsic_height_px        (never changed)
target width    = min(config image_width, effective content width) (resolved by the caller)
width_limited   = target width > effective content width
width           = min(target width, effective content width)
height          = width / aspect
if height > effective content height:
    height         = effective content height                    (height_limited = True)
    width          = height x aspect
below_min_width = min_width_cm is not None and width < min_width_cm - tolerance
```

| Invariant | Where enforced |
| --- | --- |
| aspect ratio preserved (no crop, no distortion) | `height = width / aspect` in every branch |
| never wider/taller than the effective content box | `min(target, content_width)` + height bound |
| never enlarged beyond the target width | `width = min(target, content_width)` |
| scale down oversized figures | `height_limited` / `width_limited` branches |
| no profile-ID branching | the module never sees a profile; it receives resolved geometry |
| deterministic | pure arithmetic; `test_repeated_planning_is_deterministic` |
| fail loudly on invalid measurements/bounds | `FigureMeasurementError` (unchanged behaviour) |
| readability floor never enforced by cropping | `below_min_width` is reported, size is still delivered |

## 3. Explicitly deferred item (G2-class, recorded in D-01)

Program D Product Specification §7.2 asks for *"Do not upscale a raster image merely to fill the
page."* Read strictly (never enlarge above the image's own intrinsic size) this changes the
**frozen** rule in `SPEC-FUNC-023` ("目标宽度 = min(配置 `image_width`, 有效宽度) … 按目标宽度插入")
and the behaviour that the freezing program recorded as out of scope
(`P12/P12_REQUIREMENTS.md` §1 "Out of scope — upscaling small images"), i.e. it needs
`ADR → Spec Update → SPEC_CHANGELOG → Re-freeze`.

**Therefore WP-D04 does not change it.** What is delivered instead:

* one explicit, documented, tested authority for the frozen rule;
* a guarantee that Program D introduces **no new upscaling** — the target width remains a hard
  ceiling (`test_small_raster_is_never_enlarged_beyond_the_target_width`,
  `test_aspect_ratio_is_preserved_within_rounding_tolerance`);
* an explicit `width_limited` / `height_limited` decision record so the *reason* for every size
  change is observable in evidence (and available to the D-05 integration).

Intrinsic-size no-upscale for small raster figures is carried forward as a **deferred Programme
item requiring G2 authority** in D-05, D-07 and the D-08 closure evidence. It is not silently
implemented, and it is not silently dropped.

## 4. Verification run (real output)

```text
$ .venv\Scripts\python.exe -m pytest md_converter/tests/test_figure_fitting.py \
      md_converter/tests/test_figure_sizing.py -p no:cacheprovider -q
.....................................                                    [100%]
37 passed

$ .venv\Scripts\python.exe -m ruff check md_converter/renderer/layout/figure_sizing.py \
      md_converter/tests/test_figure_fitting.py
All checks passed!

$ .venv\Scripts\python.exe -m black --check --no-cache md_converter/renderer/layout/figure_sizing.py \
      md_converter/tests/test_figure_fitting.py
2 files would be left unchanged.

$ .venv\Scripts\python.exe -m isort --check-only --settings-path pyproject.toml \
      md_converter/renderer/layout/figure_sizing.py md_converter/tests/test_figure_fitting.py
(no output -> clean)
```

The 20 pre-existing `test_figure_sizing.py` tests (including the accepted tall/narrow figure
behaviour and the end-to-end compile checks) still pass unchanged, which is the compatibility
proof for the delegation in §1: `fit_figure_size()` returns exactly the values it returned before.

Two defects were found and fixed during this WP (both inside the new code, no behaviour change):
a missing `Dict` import that `ruff` flagged, and one `black` reflow.

## 5. Test coverage against the WP-D04 requirement list

| Required test | Test |
| --- | --- |
| small raster | `test_small_raster_is_never_enlarged_beyond_the_target_width` |
| wide image | `test_target_width_is_capped_by_the_effective_content_width` |
| tall image | `test_tall_figure_is_scaled_to_the_effective_content_height` |
| landscape image | `test_landscape_figure_keeps_aspect_ratio` |
| exact-boundary image | `test_exact_boundary_figure_is_not_shrunk` |
| deterministic repeat | `test_repeated_planning_is_deterministic` |
| no-upscale behaviour | `test_small_raster_is_never_enlarged_beyond_the_target_width` (target as ceiling) |
| aspect-ratio tolerance | `test_aspect_ratio_is_preserved_within_rounding_tolerance` (5 parametrised sizes) |
| profile geometry variation through resolved widths | `test_profile_geometry_only_matters_when_the_target_exceeds_it`, `test_profile_geometry_drives_fitting_through_resolved_values_only` |

## 6. Scope discipline

Only `md_converter/renderer/layout/figure_sizing.py` and the new test file changed. No renderer,
writer, theme, config, post-processor or QA-contract change was made in this WP (integration is
WP-D05 so the policy is verified independently of Word objects).

## 7. WP-D04 conclusion

There is now a single explicit figure fitting authority with a documented decision, reason codes for
every size change, deterministic output, preserved aspect ratio, bounded content-box compliance,
unchanged frozen target-width semantics and 17 focused tests. The intrinsic-size no-upscale question
is recorded as a G2-class deferral instead of being smuggled in as a patch.

**Decision: PASS — next WP is D-05 (figure renderer integration).**
