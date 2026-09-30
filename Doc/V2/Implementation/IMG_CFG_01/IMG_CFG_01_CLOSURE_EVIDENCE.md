# IMG-CFG-01 — Image Width Configuration Propagation
## Closure Evidence

**Final status:** `IMG-CFG-01 — CLOSED / ACCEPTED / G1 FIXED`

---

## 1. Identity

| Item | Value |
|---|---|
| Starting branch / HEAD | `master` / `0884fbe0bfb5b3b7216b0be8c9b21b1e8cc9beed` (`D-08 close advanced table and figure fitting`) |
| Task type | Release-readiness configuration-contract investigation with conditional bounded remediation |
| Classification | `G1_FIX_ELIGIBLE` → G1 FIXED |
| Pipeline stop rule | never triggered (no G2, no BLOCKED) |

## 2. Six-commit chain (each WP independently verified, evidenced, staged, committed)

| # | Commit | Subject | WP |
|---|---|---|---|
| 1 | `24203fe` | `IC-01 inspect image width configuration authority` | authority & contract inspection |
| 2 | `3eb7e2a` | `IC-02 classify image width propagation behavior` | runtime reproduction & semantic impact |
| 3 | `0baba62` | `IC-03 fix image width configuration propagation` | bounded remediation (G1) |
| 4 | `bd1a818` | `IC-04 guard image width configuration contract` | contract & regression guards |
| 5 | `99b6a95` | `IC-05 verify image width configuration propagation` | integrated verification |
| 6 | *(this commit)* | `IC-06 close image width configuration propagation` | closure |

Exact-file staging only; unrelated dirty/untracked state preserved throughout. No
`git add .` / `git add -A` / `git clean` / `git reset --hard` / `git restore .` was used.

## 3. Authority findings

* `image_width` is a first-class, documented, validated configuration key
  (`config.py` `DEFAULT_CONFIG` / `CompilerConfig` / `known_fields` / `validate_config`;
  `README` documents it as the user-facing "图片宽度（英寸）" key).
* **`SPEC-FUNC-023` (FROZEN)** names it as the sizing input:
  `目标宽度 = min(配置 image_width, 有效宽度)`, `SHALL NOT 放大超过目标宽度`.
* Intended consumer: `WordRenderer._figure_bounds_cm()` → `plan_figure_fit` (the single
  sizing authority).
* **Break:** `CompilerContext.create()` built `RenderContext(theme=…, diag=…)` without the
  resolved configuration, so `RenderContext.config` stayed `{}` and the renderer always read
  the literal fallback `5`.
* `RenderContext` already supported the value (`config` slot + `create(config=…)`): a narrow
  wiring omission, not a missing design element.

## 4. Reproduction

Controlled runtime probe (`wp_ic02_runtime_reproduction.json`) — before the fix the
delivered figure width was `12.70 cm` for **every** requested `image_width`:

| requested | SPEC target | delivered (before) |
|---|---|---|
| default (5 in) | 12.70 cm | 12.70 cm |
| 2 in | 5.08 cm | **12.70 cm** (violates "never exceed the target") |
| 6 in | 15.24 cm | **12.70 cm** |
| 8 in / 20 in | 15.92 cm (page cap) | **12.70 cm** |

## 5. Classification

**`G1_FIX_ELIGIBLE`** — authoritative key, frozen rule requires propagation, receiving slot
already exists, problem is one missing constructor argument, and no frozen semantics need
to change. Not DEFER (key is neither stale nor ambiguous); not G2 (no spec, public-config,
Core, QA, ConversionService, renderer-architecture, authority, dependency or Golden
re-freeze change is required).

## 6. Remediation mode

Minimal G1 wiring at the single call site `md_converter/compiler.py`
(`CompilerContext.create()`):

```python
render_ctx = RenderContext(
    theme=theme,
    diag=diag,
    config={"image_width": config["image_width"]},
)
```

Only the resolved `image_width` is propagated through the **existing** slot. Passing the
whole resolved configuration was deliberately rejected because the same slot is also read
for `page_margins`, `page_width` and `toc_depth`; activating those on this path would be a
public configuration semantic change (a G2 stop condition). `plan_figure_fit` remains the
sole sizing authority — no second authority was created.

## 7. Files changed by the task

| File | Change |
|---|---|
| `md_converter/compiler.py` | +8 (wiring + rationale) |
| `md_converter/tests/test_image_width_configuration.py` | +301 (22 guards) |
| `Doc/V2/Implementation/IMG_CFG_01/IMG_CFG_01_CLOSURE_EVIDENCE.md` | this file |
| `Doc/V2/Implementation/IMG_CFG_01/Evidence/WP-IC01…WP-IC05_*.md` | 5 WP evidence reports |
| `Doc/V2/Implementation/IMG_CFG_01/Evidence/wp_ic02_runtime_reproduction.json` | pre-fix measurements |
| `Doc/V2/Implementation/IMG_CFG_01/Evidence/wp_ic03_postfix_reproduction.json` | post-fix measurements |

`md_converter/cli.py`, `README.md` and `.gitignore` appear in `git status` but are
**pre-existing user-owned dirty state** and were never staged or modified by this task.

## 8. Tests

| Run | Result |
|---|---|
| IMG-CFG focused (`test_image_width_configuration.py`) | 22 passed |
| figure fitting / sizing / cross-profile / config / application / profiles / batch / tables | 752 passed |
| GUI + CLI/public API + acceptance + release evidence | 664 passed |
| **Full suite** (post-change) | **4 failed, 1144 passed, 2 skipped** |
| Full suite (pre-change baseline) | 4 failed, 1122 passed, 2 skipped |

Identical failure set; **introduced failures = 0**.

## 9. Lint / format

`ruff clean`, `black --check` clean, `isort --check-only` clean on both touched files; no
circular imports. (`black` requires `BLACK_CACHE_DIR` in this sandbox — environment
artifact only.)

## 10. Measured output (after fix)

| requested | delivered width | delivered height | note |
|---|---|---|---|
| default | 12.70 cm | 6.35 cm | unchanged baseline |
| 2 in | 5.08 cm | 2.54 cm | honoured (was 12.70) |
| 6 in | 15.24 cm | 3.81 cm | honoured |
| 8 in / 20 in | 15.92 cm | 3.98 cm | capped by effective content width |

Every case satisfies `min(configured image_width, effective width)`, preserves aspect ratio,
and never crops or stretches.

## 11. Drift matrix

| Surface | Drift |
|---|---|
| `SPEC-FUNC-023` | 0 |
| figure authority duplication | 0 |
| profile-ID branching | 0 |
| aspect-ratio distortion | 0 |
| Core semantic | 0 |
| Canonical semantic | 0 |
| QA semantic (Static / Rendered / FinalArtifact) | 0 |
| ConversionService semantic | 0 |
| CLI / public API breaking | 0 |
| output naming / path | 0 |
| introduced failures | 0 |
| open blockers | 0 |

Default-path equivalence: with `image_width = 5` the renderer resolved `5` before (fallback)
and resolves `5` after (explicit); `page_width`, `page_margins` and `toc_depth` resolve
identically. The default render is therefore bit-identical and no Golden re-freeze is
required.

## 12. Known unrelated failures (pre-existing)

1. `test_golden.py::test_golden[sample]` — canonical Golden environment mismatch
   (baseline backend `playwright` vs actual `fallback`; Chromium `spawn EPERM`).
2. `test_golden_environment.py::test_canonical_golden_environment` — same Chromium launch
   limitation.
3. `test_packaging_metadata.py::test_pkg_documented_extras_exist_in_metadata` — reads the
   user-modified uncommitted `README.md` (extras `mermaid`/`windows` no longer documented).
4. `test_packaging_metadata.py::test_pkg_readme_has_no_legacy_packaging_references` — same
   rewritten `README.md`.

All four reproduce on the pre-change baseline and are independent of IMG-CFG-01; they were
reported, not modified (`SPEC-INV-012`).

## 13. Deferred items

| Item | Reason | Required authority |
|---|---|---|
| Wiring the sibling `RenderContext.config` keys (`page_margins`, `page_width`, `toc_depth`) | would change public configuration semantics for legacy `create_theme()` themes | separate authorized change (potential G2) |
| Small-raster no-upscale policy | separately deferred by Program D | separate Program D change |
| Canonical Golden content comparison | Chromium cannot launch in this environment | run in the canonical Golden environment |
| Packaging metadata tests 3 & 4 | depend on the user's in-progress `README.md` rewrite | owner decides README content |

## 14. Final recommendation

**`IMG-CFG-01 — CLOSED / ACCEPTED / G1 FIXED`**

`SPEC-FUNC-023` now holds end to end: the configured `image_width` reaches
`plan_figure_fit` through the existing `RenderContext.config` slot, with zero drift on every
frozen surface, zero introduced failures, and no open blockers. R2 integrated verification
is not started by this task (per the master instruction).
