# WP-IC01 — Authority & Contract Inspection Evidence

**Task:** IMG-CFG-01 — Image Width Configuration Propagation
**WP:** IC-01 (Authority & Contract Inspection)
**Status:** GREEN
**Branch / starting HEAD:** `master` / `0884fbe0bfb5b3b7216b0be8c9b21b1e8cc9beed`

---

## 1. Purpose

Establish the authoritative contract for `image_width` and identify the exact
propagation break, without modifying anything. WP-IC01 is inspection only — no
source file is changed by this WP.

## 2. Method

Static inspection of the canonical spec, configuration module, compiler context
factory, render context, renderer image path, figure-sizing authority, released
documentation, Program D evidence, and the test suite; cross-checked by a
read-only runtime probe (see WP-IC02 for the measured reproduction).

Repository safety snapshot captured before any action:

| Item | Value |
|---|---|
| branch | `master` |
| HEAD | `0884fbe0bfb5b3b7216b0be8c9b21b1e8cc9beed` (`D-08 close advanced table and figure fitting`) |
| Dirty (tracked, modified) | `.gitignore`, `README.md`, `md_converter/cli.py` |
| Dirty (untracked) | `Doc/V2/**` additions, `tests/`, `release/`, `dist/`, `review_packages/`, `packaging/windows/*`, etc. |

Unrelated dirty/untracked state is preserved and never staged (exact-file staging only).

---

## 3. Required Findings

### Q1. Authoritative definition

`image_width` is a **first-class configuration key**, not a vestigial field:

* `md_converter/config.py:47` — declared in `DEFAULT_CONFIG` as `"image_width": 5,  # inches`.
* `md_converter/config.py:127` — typed field `image_width: int = 5` on `CompilerConfig`.
* `md_converter/config.py:157` — listed among `known_fields` (so it is a *known* key, not
  swept into `extra`).
* `md_converter/config.py:181` — round-tripped by `CompilerConfig.from_dict`.
* `md_converter/config.py:205` — round-tripped by `CompilerConfig.to_dict`.
* `md_converter/config.py:480-483` — validated: must be a positive number, else
  `resolve_config` raises `ValueError`.

The canonical spec names it as the sizing input:

`CANONICAL_SPEC.md:98-102` (**SPEC-FUNC-023**, FROZEN):

> 目标宽度 = min(配置 `image_width`, 有效宽度) … 尺寸 SHALL 保持宽高比、
> SHALL NOT 放大超过目标宽度、SHALL NOT 超出有效内容区宽高。

### Q2. Documented meaning

* `README_bck.md:300-301` — `# 图片宽度（英寸）` / `image_width: 5` (a user-facing
  YAML key, in inches).
* `MD_Converter_v1.1.0_payload/README.md:301` — same key in the released payload docs.
* Released release notes restate the rule as `min(配置 image_width, 有效内容区宽度)`.

So the key is documented as user-facing and as *the* configured figure width.

### Q3. Default value

`5` inches (`DEFAULT_CONFIG["image_width"]`, `CompilerConfig.image_width`).
At the frozen reference geometry this resolves to `min(5in, 15.92cm) = 12.70 cm`.

### Q4. Intended consumer

The **renderer** consumes it, on the single figure path:

* `md_converter/renderer/word_renderer.py:663`
  `configured = self.ctx.config.get("image_width", 5)` inside `_figure_bounds_cm()`.
* `md_converter/renderer/word_renderer.py:95` — `self.ctx = ctx` (the `RenderContext`).
* `md_converter/compiler.py:274` — `renderer = WordRenderer(self.render_ctx, writer)`.

`_figure_bounds_cm()` feeds `target_width_cm` into the frozen sizing authority
`plan_figure_fit` (`md_converter/renderer/layout/figure_sizing.py:223-233`), which remains
the sole decision point.

### Q5. Exact propagation break

`CompilerContext.create()` constructs the render context **without** the resolved
configuration:

```
md_converter/compiler.py:155-158
    render_ctx = RenderContext(
        theme=theme,
        diag=diag,
    )
```

`RenderContext.config` therefore stays at its dataclass default
`field(default_factory=dict)` (`md_converter/renderer/render_context.py:218`), i.e. `{}`.
Consequently `self.ctx.config.get("image_width", 5)` at `word_renderer.py:663` **always**
returns the literal fallback `5`, regardless of the resolved configuration.

Verified by exhaustive search: the only production instantiation of `RenderContext` is
`compiler.py:155`; the only other construction site is `RenderContext.copy()`
(`render_context.py:425`), which already propagates `config`.

### Q6. Does `RenderContext` already support the value?

**Yes, unmodified.** The receiving slot pre-exists:

* `render_context.py:218` — `config: Dict[str, Any] = field(default_factory=dict)`.
* `render_context.py:244-245` — `__post_init__` already reads `self.config.get("toc_depth", 3)`.
* `render_context.py:247-275` — `RenderContext.create(theme, config, diag)` already accepts
  and stores `config`.

No new slot, field, or API is required to carry `image_width` to the renderer.

### Q7. Is the fallback intentional?

No. The `5` at `word_renderer.py:663` is a defensive default that happens to equal the
documented default, which is exactly why the defect is invisible: every existing test and
golden uses the default width, so `fallback == configured == 5` and the two are
indistinguishable. SPEC-FUNC-023 requires `min(配置 image_width, 有效宽度)`; a hard-coded
`5` can only satisfy that rule when the configured value is also `5`. The spec text
explicitly forbids degradation to hard-coded constants (`CANONICAL_SPEC.md:100-101`,
CLAR-02).

Program D already recorded this as a pre-existing, out-of-scope observation:

* `Doc/V2/Implementation/Program_D_Advanced_Table_Figure_Fitting/Evidence/WP-D05_FIGURE_INTEGRATION_EVIDENCE.md:121-143`.
* `Doc/V2/Implementation/Program_D_Advanced_Table_Figure_Fitting/PROGRAM_D_CLOSURE_EVIDENCE.md:262`
  — "`image_width` configuration wiring defect (`CompilerContext.create` does not pass config
  into `RenderContext`) … separate authorised change".

### Q8. G1 feasibility

**G1_FIX_ELIGIBLE.** All G1 preconditions hold:

| G1 precondition | Evidence |
|---|---|
| `image_width` is an authoritative supported key | config.py:47/127/157/181/205/480 |
| frozen docs require it to affect rendering | CANONICAL_SPEC.md:98-102 (SPEC-FUNC-023) |
| the architecture already has an intended receiving slot | render_context.py:218/247-275 |
| the problem is a narrow wiring omission | compiler.py:155-158 (one constructor call) |
| no frozen semantic contract needs modification | SPEC-FUNC-023 unchanged; no API change |

No G2 trigger is present: no `SPEC-FUNC-023` change, no target-width semantic redefinition,
no public config semantic change, no Canonical/Core/QA/ConversionService change, no renderer
redesign, no new authority, no new user setting, no Golden re-freeze, no new dependency.

## 4. Contract summary

| Aspect | Authoritative answer |
|---|---|
| Definition | `DEFAULT_CONFIG["image_width"]` / `CompilerConfig.image_width` (config.py) |
| Meaning | configured figure target width, inches, user-facing YAML key |
| Default | `5` in ⇒ `12.70 cm` at the frozen reference geometry |
| Intended consumer | `WordRenderer._figure_bounds_cm()` → `plan_figure_fit` |
| Propagation break | `CompilerContext.create()` builds `RenderContext` without `config` |
| RenderContext support | already present (`config` slot + `create(config=...)`) |
| Fallback intentional? | no — equals the default and masks the defect |
| Disposition | **G1_FIX_ELIGIBLE** |

## 5. Outcome

Authority and contract are explicit; the break is a single missing constructor argument.
No source change is made by WP-IC01. Proceed to WP-IC02 (runtime reproduction & impact).
