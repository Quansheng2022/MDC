# WP-IC04 — Contract & Regression Guards Evidence

**Task:** IMG-CFG-01 — Image Width Configuration Propagation
**WP:** IC-04 (Contract & Regression Guards)
**Status:** GREEN
**Parent commit:** `0baba62` (IC-03, G1 fixed)

---

## 1. Purpose

Lock the IC-03 repair with focused, deterministic guards so the propagation cannot
regress silently and so the zero-drift claims are enforced by tests rather than prose.

## 2. New guard module

`md_converter/tests/test_image_width_configuration.py` — 22 tests.

Reuses the existing PNG-fixture technique from `test_figure_fitting_integration.py`
(pure-Python PNG writer, no new dependency) and the `ConversionService` batch-worker path
from `tests/application/test_conversion_service.py`.

## 3. Required coverage

| Required guard | Test(s) |
|---|---|
| default behaviour | `test_default_width_behaviour_is_unchanged` (12.70 cm / 6.35 cm) |
| smaller configured width | `test_smaller_configured_width_is_honoured` (2 in → 5.08 cm) |
| smaller width on a small raster | `test_smaller_configured_width_shrinks_a_small_raster` |
| larger configured width | `test_larger_configured_width_within_bounds_is_honoured` (6 in → 15.24 cm) |
| effective page cap | `test_configured_width_is_capped_by_the_effective_page_width` (8 in, 20 in → 15.92 cm) |
| aspect ratio | `test_aspect_ratio_is_preserved_for_any_configured_width` (2/5/6/8 in) |
| sole `plan_figure_fit` authority | `test_delivered_geometry_equals_the_single_sizing_authority` (5 sizes), `test_figure_sizing_module_exposes_one_plan_entry_point` |
| no profile-ID branching | `test_no_profile_id_branching_on_the_image_path`, `test_profiles_with_equal_geometry_deliver_equal_widths` |
| batch / single-file parity | `test_batch_path_and_single_file_path_agree` |
| propagation wiring | `test_render_context_receives_exactly_the_resolved_image_width` |
| zero drift (other keys dormant) | `test_other_latent_render_context_keys_stay_dormant` |

### Notable assertions

* **Single authority, checked behaviourally.** For every configured width the delivered
  DOCX geometry equals `plan_figure_fit(..., target=min(configured, content_width))`
  exactly (`abs=0.02`). The artifact cannot come from any second sizing path.
* **Wiring guard.** `CompilerContext.create({"image_width": 3}).render_ctx.config`
  is exactly `{"image_width": 3}` — the fix propagates the key and nothing else.
* **Zero-drift guard.** `page_margins` / `page_width` / `toc_depth` remain absent from
  `render_ctx.config` and `toc.include_depth` keeps the historical fallback `3`, so the
  repair cannot silently activate an unrelated (and G2-classified) configuration key.
* **No profile-ID branching.** `renderer/word_renderer.py` and
  `renderer/layout/figure_sizing.py` contain no `output_profile` reference and no profile
  identifier literal, and two profiles with identical resolved geometry deliver identical
  figure widths.

## 4. Verification runs

```
md_converter/tests/test_image_width_configuration.py
    22 passed in 23.95s

figure fitting + sizing + cross-profile + config + compiler-configuration +
output profiles + profile rendering + tests/application + tests/gui +
test_image_width_configuration
    752 passed in 109.46s
```

Golden / acceptance: `test_golden.py` is executed in WP-IC05; in this environment it
aborts on the pre-existing canonical-environment mismatch (baseline backend `playwright`
vs actual `fallback`), reproduced unchanged from the WP-IC02 baseline. The default
configuration is unaffected by the repair (`image_width = 5` was already the effective
value), so no Golden baseline semantic change is required
(`SPEC-FUNC-023` / rendering output for the default path is bit-identical by
construction — see IC-05 §drift).

## 5. Lint / format (new + touched files)

| Tool | Result |
|---|---|
| `ruff check` (new test module) | `All checks passed!` |
| `black --check` (new test module) | `1 file would be left unchanged.` |
| `isort --check-only` (new test module) | clean |

## 6. Outcome

The propagation contract is guarded: default unchanged, smaller/larger/capped widths
honoured, aspect ratio preserved, single sizing authority intact, no profile branching,
batch and single-file parity, and no collateral activation of other configuration keys.
Proceed to WP-IC05 (integrated verification).
