# WP-IC03 — Bounded Remediation Evidence

**Task:** IMG-CFG-01 — Image Width Configuration Propagation
**WP:** IC-03 (Bounded Remediation)
**Status:** GREEN
**Parent commit:** `3eb7e2a` (IC-02)
**Disposition from IC-02:** `G1_FIX_ELIGIBLE`

---

## 1. Remediation mode

**G1 bounded propagation repair** — restore the frozen `SPEC-FUNC-023` input
(`目标宽度 = min(配置 image_width, 有效宽度)`) by wiring the resolved configuration into
the pre-existing `RenderContext.config` slot. No new authority, no new key, no
`plan_figure_fit` change, no renderer redesign, no public API change.

## 2. Change

Single call site — `md_converter/compiler.py`, `CompilerContext.create()`:

```diff
@@ -152,9 +152,17 @@ class CompilerContext:
         )

         # 渲染器上下文
+        #
+        # IMG-CFG-01：把已解析配置中的图形目标宽度传入既有 ``RenderContext.config``
+        # 槽（SPEC-FUNC-023：目标宽度 = min(配置 image_width, 有效宽度)）。渲染器在
+        # ``WordRenderer._figure_bounds_cm()`` 中经 ``self.ctx.config`` 读取该键，并交给
+        # ``plan_figure_fit``（唯一尺寸权威）。此处只传播 ``image_width``：整份已解析配置
+        # 传入会顺带激活同槽位上其它此前未在该路径上授权的键（``page_margins`` /
+        # ``page_width`` / ``toc_depth``），构成越界语义变更；因此保持最小、零漂移的传播。
         render_ctx = RenderContext(
             theme=theme,
             diag=diag,
+            config={"image_width": config["image_width"]},
         )
```

`config` is the fully resolved/validated configuration returned by `resolve_config`
(`compiler.py:108`), so `config["image_width"]` is guaranteed present and positive.

## 3. Why the narrow shape (and not the whole config)

`RenderContext.config` is read by exactly three call sites inside the renderer:

| Reader | Key | Behaviour now (config `{}`) | Behaviour if the *whole* resolved config were passed |
|---|---|---|---|
| `word_renderer.py:663` (`_figure_bounds_cm`) | `image_width` | fallback `5` | resolved value — **the intended repair** |
| `word_renderer.py:256` (`_apply_page_size`) | `page_width` | fallback `"A4"` | `"A4"` (same for the default theme; theme `page_size` wins anyway) |
| `word_renderer.py:810` (`_apply_page_margins`) | `page_margins` | fallback `2.54` cm | `2.5` cm for themes without `page_margins_cm` (the legacy `create_theme()` themes) |
| `render_context.py:245` (`__post_init__`) | `toc_depth` | fallback `3` | resolved `toc_depth` |

Passing the whole configuration would therefore *also* activate `page_margins`,
`page_width` and `toc_depth` on this path. For the legacy `create_theme()` themes that
lack `page_margins_cm`, that changes the effective content width
(`15.92 cm → 16.00 cm`) — i.e. a **public configuration semantic change**, which is
explicitly a G2 stop condition (`Master Instruction` §14.3). Propagating only
`image_width` keeps the repair inside the authorized scope and provably zero-drift for
every other key.

The narrow shape does **not** create a second sizing authority: the value still flows
through the existing slot into the existing renderer, and `plan_figure_fit` remains the
single decision point.

## 4. Verification

### 4.1 Before → after (same probe, same fixtures)

Read-only probe: `wp_ic02_runtime_reproduction.json` (IC-02) vs the post-fix run.

| Case | requested (in) | before (cm) | after (cm) | SPEC target (cm) | PROPAGATED |
|---|---|---|---|---|---|
| no explicit `image_width` | – | 12.70 | 12.70 | 12.70 | yes (unchanged) |
| smaller explicit | 2 | 12.70 | **5.08** | 5.08 | **yes** |
| smaller explicit, small raster 82×41 | 2 | 12.70 | **5.08** | 5.08 | **yes** |
| larger explicit, within bounds | 6 | 12.70 | **15.24** | 15.24 | **yes** |
| larger explicit, above content cap | 8 | 12.70 | **15.92** | 15.92 | **yes** |
| larger explicit, above content cap | 20 | 12.70 | **15.92** | 15.92 | **yes** |

`render_ctx.config` is now `{"image_width": <resolved>}` in every case (probe field
`render_ctx_config_keys`), and `propagation_honoured` is `true` for all six cases.

### 4.2 Focused regression set

`.venv\Scripts\python.exe -m pytest -p no:cacheprovider` over figure / fitting / config /
profiles / application / batch / table integration:

```
291 passed in 69.20s
```

Files: `test_figure_fitting.py`, `test_figure_fitting_integration.py`, `test_figure_sizing.py`,
`test_fitting_cross_profile.py`, `test_config.py`, `test_compiler_configuration.py`,
`test_output_profiles.py`, `test_output_profile_rendering.py`, `tests/application`,
`tests/gui/test_batch_execution.py`, `tests/gui/test_batch_model.py`,
`test_table_fitting.py`, `test_table_fitting_integration.py`.

### 4.3 Lint / format (touched file)

| Tool | Result |
|---|---|
| `ruff check md_converter/compiler.py` | `All checks passed!` |
| `black --check md_converter/compiler.py` | `1 file would be left unchanged.` |
| `isort --check-only md_converter/compiler.py` | exit 0, no diff |

Environment note: `black`'s default cache directory is outside the writable sandbox root
and caused the process to block. Running with `BLACK_CACHE_DIR` pointed at a writable temp
directory completes normally and reports the file unchanged. This is an environment
artifact, not a formatting defect.

## 5. Scope check

| Frozen constraint | Status |
|---|---|
| `SPEC-FUNC-023` unchanged | yes (no spec edit) |
| `plan_figure_fit` sole sizing authority | yes (untouched; still the only decision point) |
| no new image-width keys / GUI settings / per-image controls | yes |
| no profile-ID branches introduced | yes |
| no third-party dependency | yes |
| no renderer redesign / no AST or parser change | yes |
| no CLI / public API / output naming change | yes |

## 6. Outcome

`SPEC-FUNC-023` is now satisfied end to end: the configured `image_width` reaches
`plan_figure_fit` through the existing slot. Proceed to WP-IC04 (contract & regression
guards).
