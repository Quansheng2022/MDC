# WP-IC05 — Integrated Verification Evidence

**Task:** IMG-CFG-01 — Image Width Configuration Propagation
**WP:** IC-05 (Integrated Verification)
**Status:** GREEN (zero introduced failures, zero drift)
**Parent commit:** `bd1a818` (IC-04)

---

## 1. Environment

| Item | Value |
|---|---|
| Project venv | `.venv` (Python 3.12.14) |
| Install mode | editable — `pip install -e . --no-build-isolation --no-deps` (AGENTS.md requirement; the venv previously held a stale non-editable 1.1.0 copy without `plan_figure_fit`) |
| pytest | `-p no:cacheprovider` (`--strict-markers`, `--tb=short`) |
| Test root | `md_converter/tests` (1128 pre-existing + 22 new = 1150 tests) |

## 2. Verification runs

| Run | Command (abridged) | Result |
|---|---|---|
| IMG-CFG focused | `test_image_width_configuration.py` | **22 passed** in 23.95s |
| Program D figure + sizing + cross-profile | `test_figure_fitting*.py`, `test_figure_sizing.py`, `test_fitting_cross_profile.py` | included below |
| config + application | `test_config.py`, `test_compiler_configuration.py`, `tests/application` | included below |
| profiles | `test_output_profiles.py`, `test_output_profile_rendering.py` | included below |
| Serial Batch (GUI worker path) | `tests/gui/test_batch_execution.py`, `test_batch_model.py` | included below |
| table fitting | `test_table_fitting*.py` | included below |
| **combined figure/config/profile/application/batch** | (all of the above + IMG-CFG) | **752 passed** in 109.46s |
| GUI + CLI/public API + acceptance + release-evidence | `test_acceptance.py`, `test_public_api_convert.py`, `test_release_evidence.py`, `tests/gui` | **664 passed** in 90.84s |
| Golden / canonical environment | `test_golden.py`, `test_golden_environment.py` | 2 failed — pre-existing environment (see §4) |
| **full suite once** | `pytest -p no:cacheprovider -rf` | **4 failed, 1144 passed, 2 skipped** in 170.63s |

Baseline (pre-change, starting HEAD `0884fbe`): **4 failed, 1122 passed, 2 skipped**.
Identical failure set; the +22 passed are exactly the new IC-04 guards.

## 3. Drift matrix

| Surface | Drift | Evidence |
|---|---|---|
| **SPEC-FUNC-023** | **0** | `CANONICAL_SPEC.md` untouched; `test_delivered_geometry_equals_the_single_sizing_authority` asserts the artifact equals the frozen rule `min(configured, content_width)` |
| Figure authority duplication | **0** | `plan_figure_fit` remains the sole decision point (`test_figure_sizing_module_exposes_one_plan_entry_point`); `_add_fitted_picture` still calls it |
| Profile-ID branching | **0** | `test_no_profile_id_branching_on_the_image_path` (no `output_profile`/id literals in renderer or sizing module) |
| Aspect-ratio distortion | **0** | `test_aspect_ratio_is_preserved_for_any_configured_width` (2/5/6/8 in, ratio preserved) |
| Core (compiler) semantic | **0** | change is one constructor argument; the default path (`image_width = 5`) yields the same value the renderer already used |
| Canonical semantic | **0** | no canonical/spec document edited |
| QA semantic (StaticQA / RenderedQA / FinalArtifactQA) | **0** | QA modules untouched; `test_release_evidence.py`, `test_acceptance.py`, RenderedQA figure metrics unchanged (`figure_overflow == 0`) |
| ConversionService semantic | **0** | service untouched; `test_batch_path_and_single_file_path_agree` proves it now simply honours the documented key |
| CLI / public API breaking | **0** | `md_converter/cli.py` untouched by this task (`git diff 0884fbe -- md_converter` lists only `compiler.py` + the new test module as task changes); `test_public_api_convert.py`, `test_acceptance.py` pass |
| Output naming / path | **0** | untouched; `tests/application` naming assertions pass |
| Introduced failures | **0** | failure set identical to baseline |
| Open blockers | **0** | — |

### Default-path equivalence (why the Golden baseline needs no re-freeze)

The repair only changes `RenderContext.config` from `{}` to `{"image_width": 5}` for the
default configuration. The three readers therefore resolve identically:

| Reader | Before (`{}`) | After (`{"image_width": 5}`) |
|---|---|---|
| `image_width` (`word_renderer.py:663`) | `5` (fallback) | `5` (resolved) |
| `page_width` (`word_renderer.py:256`) | `"A4"` | `"A4"` (theme `page_size` wins anyway) |
| `page_margins` (`word_renderer.py:810`) | theme `page_margins_cm` | theme `page_margins_cm` (unchanged) |
| `toc_depth` (`render_context.py:245`) | `3` (fallback) | `3` (resolved) |

The default render is consequently bit-identical, and `SPEC-FUNC-023` requires no
semantic Golden re-freeze.

## 4. Known unrelated failures (pre-existing, reproduced at baseline)

| Test | Cause |
|---|---|
| `test_golden.py::test_golden[sample]` | Canonical Golden environment mismatch — baseline `renderer_backend='playwright'`, actual `'fallback'` because Chromium cannot launch in this environment (`BrowserType.launch: spawn EPERM`). Fails before any artifact comparison. |
| `test_golden_environment.py::test_canonical_golden_environment` | Same Chromium `spawn EPERM`. |
| `test_packaging_metadata.py::test_pkg_documented_extras_exist_in_metadata` | Reads the user-modified, uncommitted `README.md`; the rewritten README no longer documents `.[mermaid]` / `.[windows]`. |
| `test_packaging_metadata.py::test_pkg_readme_has_no_legacy_packaging_references` | Same rewritten `README.md` lacks `[project.entry-points`. |

None is caused by IMG-CFG-01; all four are reproduced on the pre-change baseline and are
independent of the `image_width` repair. They are outside this task's change plan and are
not modified here (`SPEC-INV-012` reporting-only discipline).

## 5. Lint / format (touched files)

`md_converter/compiler.py`, `md_converter/tests/test_image_width_configuration.py`:

| Tool | Result |
|---|---|
| `ruff check` | `All checks passed!` |
| `black --check` | `2 files would be left unchanged.` |
| `isort --check-only` | exit 0, no diff |
| circular-import probe (`import md_converter.compiler` + renderer/application/cli/gui.batch) | `import-ok` |

`black` requires `BLACK_CACHE_DIR` to point at a writable directory in this sandbox
(its default cache path is outside the writable root and blocks); this is an environment
artifact, not a formatting issue.

## 6. Measured output

Post-fix runtime measurements are recorded in `wp_ic03_postfix_reproduction.json`
(committed with IC-03). Delivered widths: default `12.70 cm`; `2 in` → `5.08 cm`;
`6 in` → `15.24 cm`; `8 in` / `20 in` → `15.92 cm` (effective content cap). Every case
satisfies `min(configured image_width, effective width)` and preserves aspect ratio.

## 7. Outcome

Integrated verification is green: focused, cross-cutting, GUI/CLI/API/acceptance and full
suite all behave as the baseline except for the intended repair; zero drift on every frozen
surface; zero introduced failures. Proceed to WP-IC06 (closure).
