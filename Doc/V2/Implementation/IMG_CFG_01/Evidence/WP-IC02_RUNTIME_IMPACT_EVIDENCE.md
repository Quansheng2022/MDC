# WP-IC02 — Runtime Reproduction & Semantic Impact Evidence

**Task:** IMG-CFG-01 — Image Width Configuration Propagation
**WP:** IC-02 (Runtime Reproduction & Impact)
**Status:** GREEN
**Parent commit:** `24203fe` (IC-01)

---

## 1. Purpose

Reproduce the IC-01 propagation break at runtime and measure its semantic impact
against the frozen `SPEC-FUNC-023`, then classify exactly one disposition.

## 2. Method

`CompilerContext.create(config)` → `compile(markdown)` → final DOCX, over six
controlled cases. Each case records the resolved config, the `RenderContext`
state, the renderer-observed value, the `SPEC-FUNC-023` expectation
(`plan_figure_fit` at `min(configured image_width, effective width)`), and the
**actual** delivered inline-shape width.

Raw measurements: `wp_ic02_runtime_reproduction.json` (this directory), produced by a
read-only probe that does not modify the repository.

Environment: project `.venv`, Python 3.12.14, `md_converter` installed editable
(`pip install -e .`), so the repo source under test is the working tree.

Frozen reference geometry (A4 + 1in, `SPEC-FUNC-023` CLAR-02):
content width `15.92 cm`, content height `24.62 cm` (`15.92 cm ≈ 6.268 in`).

## 3. Cases and measurements

| Case | requested (in) | resolved config (in) | `render_ctx.config` | renderer sees (in) | SPEC target (cm) | SPEC expected width (cm) | actual width (cm) | propagated? |
|---|---|---|---|---|---|---|---|---|
| no explicit `image_width` | – | 5 | `{}` | 5 | 12.70 | 12.70 | 12.70 | n/a (degenerate) |
| smaller explicit | 2 | 2 | `{}` | 5 | 5.08 | 5.08 | **12.70** | **NO** |
| smaller explicit, small raster (82×41) | 2 | 2 | `{}` | 5 | 5.08 | 5.08 | **12.70** | **NO** |
| larger explicit, within bounds | 6 | 6 | `{}` | 5 | 15.24 | 15.24 | **12.70** | **NO** |
| larger explicit, above content cap | 8 | 8 | `{}` | 5 | 15.92 | 15.92 | **12.70** | **NO** |
| larger explicit, above content cap | 20 | 20 | `{}` | 5 | 15.92 | 15.92 | **12.70** | **NO** |

Observations:

1. **The resolved config is correct.** `resolve_config` keeps `image_width` on
   `CompilerContext.config` for every requested value (2, 6, 8, 20). The break is not in
   configuration loading or validation.
2. **`RenderContext.config` is always `{}`.** `CompilerContext.create()` never hands the
   resolved configuration to the render context (IC-01 §Q5).
3. **The renderer always observes the fallback `5`.** `word_renderer.py:663`
   (`self.ctx.config.get("image_width", 5)`) can only return the literal default.
4. **The delivered figure width is constant at `12.70 cm`** for every requested value —
   independent of the configured `image_width`.
5. **The delivered figure height is constant at `3.175 cm`** (aspect ratio preserved:
   400×100 → 4:1), so the aspect-ratio contract is not itself violated; only the target
   width is fixed.

## 4. Semantic impact vs SPEC-FUNC-023

`SPEC-FUNC-023` (FROZEN): `目标宽度 = min(配置 image_width, 有效宽度)` and
`SHALL NOT 放大超过目标宽度`.

| Requested | SPEC-compliant delivered width | Actual | Deviation |
|---|---|---|---|
| 2 in (5.08 cm target) | 5.08 cm | 12.70 cm | **+7.62 cm (delivered exceeds the configured target)** |
| 6 in (15.24 cm target) | 15.24 cm | 12.70 cm | −2.54 cm |
| 8 in / 20 in (15.92 cm cap) | 15.92 cm | 12.70 cm | −3.22 cm |

* The **smaller-value case is a spec violation, not merely an inconvenience**: the delivered
  width (12.70 cm) exceeds the frozen target (5.08 cm), directly contradicting
  *"SHALL NOT 放大超过目标宽度"*. This also flips the small-raster no-upscale intent: at a
  2 in target the image should be *downscaled* to 5.08 cm, but it is delivered larger.
* The **larger-value cases are a silent under-honouring**: the configured width is ignored,
  so a user asking for a wider figure gets neither the wider figure nor any diagnostic.

## 5. Effective page cap

The effective page cap is `min(target_width, effective content width) = min(12.70, 15.92)`
for the frozen default geometry, so the `12.70 cm` fallback never reaches the content-width
cap. The cap interaction is therefore **currently unobservable** for larger configured
values: a user configuring `image_width = 8` in expects the figure to grow up to the 15.92 cm
content cap, but it stays pinned at 12.70 cm. The page-cap rule itself is intact
(`plan_figure_fit` still caps by content width); what is broken is the input feeding it.

## 6. Receiver-slot control (narrow-wiring proof)

Constructing the existing `RenderContext` with the configuration already carries the value:

| Injected `image_width` (in) | `render_ctx.config.get("image_width", 5)` | carried? |
|---|---|---|
| 2 | 2 | yes |
| 8 | 8 | yes |

This proves the failure is exactly the single missing `config=` argument on the
`RenderContext(...)` construction at `compiler.py:155`, and that no new slot or API is
needed to receive the value.

## 7. Classification

**`G1_FIX_ELIGIBLE`**

| G1 precondition | Verdict |
|---|---|
| `image_width` is an authoritative supported key | yes (config module + validation + docs) |
| frozen docs require it to affect rendering | yes (`SPEC-FUNC-023` target rule) |
| the architecture already has an intended receiving slot | yes (`RenderContext.config`) |
| the problem is a narrow wiring omission | yes (one missing constructor argument) |
| no frozen semantic contract needs modification | yes (no spec/API/QA/Core change) |

Not `DEFER_KNOWN_LIMITATION`: the key is neither stale nor ambiguous; frozen authority
explicitly requires it, and intent is provable.

Not `G2_AUTHORITY_REQUIRED`: no `SPEC-FUNC-023` change, target-width redefinition, public
config semantic change, Canonical/Core/QA/ConversionService change, renderer redesign, new
authority, or Golden re-freeze is required.

## 8. Outcome

Runtime behaviour reproduced and quantified; disposition is **G1_FIX_ELIGIBLE** with a
single narrow wiring repair. Proceed to WP-IC03 (bounded remediation). No G2 trigger;
pipeline continues.
