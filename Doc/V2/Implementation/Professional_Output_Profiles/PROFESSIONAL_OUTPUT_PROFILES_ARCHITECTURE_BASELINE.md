# MD Converter - Professional Output Profiles Architecture Baseline

**Document Type:** Architecture Baseline (WP-POP-01 freeze)
**Program:** Program C - Professional Output Profiles
**Source Product Specification:** `Doc/V2/Product/Professional_Output_Profiles_Product_Specification.md`
**Source Implementation Plan:** `Doc/V2/Implementation/Professional_Output_Profiles/Professional_Output_Profiles_Implementation_Plan.md`
**Canonical Authority:** `CANONICAL_SPEC.md` (FROZEN 1.0) - this baseline adds no canonical behaviour.
**Status:** FROZEN (Program C)

---

## 1. Canonical SPEC references

`CANONICAL_SPEC.md` (FROZEN 1.0) is the single authority. It does not mention
output profiles, so this program adds a bounded presentation layer and opens no
canonical entry. The entries that constrain it:

| Reference | How it constrains this program |
|---|---|
| SPEC-FUNC-012 | The theme system (QS-Word-Default-V1.5) is frozen. Profiles are bounded presentation configuration layered *on* that theme; the frozen YAML is never edited. |
| SPEC-GOAL-003 / SPEC-INV-003 | Determinism: registry order, fallback and overlay are pure functions of the identifier. |
| SPEC-GOAL-004 / SPEC-INV-001 | Semantic fidelity: the profile touches presentation only; document meaning (tokens, headings, tables) is unchanged. |
| SPEC-ARCH-004 / SPEC-ARCH-009 | The renderer only renders and obtains formatting through StyleResolver/theme. No renderer branch, no profile logic in the renderer. |
| SPEC-ARCH-007 | One-directional dependencies: `md_converter.profiles` imports no parser/pipeline/renderer/compiler/application/GUI module. |
| SPEC-ARCH-011 | Fonts are set through `set_style_font`; the overlay therefore always carries all four slots (`ascii`/`hAnsi`/`eastAsia`/`cs`). |
| SPEC-ARCH-013 / SPEC-QA-001 / SPEC-QA-002 | The quality-gate stages and their FAIL semantics are unchanged: every profile passes StaticQA/RenderedQA/FinalArtifactQA on the representative corpus. |
| SPEC-QA-004 / SPEC-INV-010 | Final-artifact sha256 semantics and the release-evidence gate are untouched. |
| SPEC-INV-002 | Readability minimums (body ≥ 10pt, table ≥ 8.5pt, code ≥ 8pt, margin ≥ 0.5in) are enforced by the profile model at construction time. |
| SPEC-INV-005 | No stage is bypassed: profiles still flow Markdown → Parser → AST → Pipeline → LayoutPlan → Renderer → Post-Processor. |
| SPEC-INV-006 | Fail loudly: an unresolvable identifier produces a structured diagnostic (`PROFILE001`), not a silent ignore. |
| SPEC-INV-011 | No Golden baseline is updated by this program. |
| SPEC-INV-012 | Only the modules named in §6 of this baseline were modified. |
| SPEC-AC-002 / SPEC-AC-003 | Acceptance evidence: StaticQA = PASS, RenderedQA ≠ FAIL, FinalArtifactQA = PASS, token coverage = 1.0 for every profile. |

**Change classification:** G1 — controlled feature work. No G2 item is opened
(no Core/Canonical change, no ConversionService semantic change, no QA semantic
change, no naming/path change, no CLI/public-API break, no new renderer
architecture).

---

## 2. Purpose

Freeze the smallest profile integration boundary before any code is written.
A profile is **bounded presentation configuration**. It never changes parsing,
AST, pipeline, canonical decisions, QA semantics or output naming.

---

## 3. Inspected Authority (evidence of the boundary)

| Concern | Authoritative location | Observed fact |
|---|---|---|
| Presentation configuration | `md_converter/renderer/themes/v15_theme.py` + `renderer/themes/default_v1_5.yaml` | The frozen V1.5 theme (status `frozen`) is the single presentation authority. |
| Style decisions | `md_converter/renderer/style_resolver.py` | Renderer obtains formatting only through `StyleResolver`; no style literals in the GUI. |
| Theme selection | `md_converter/compiler.py` (`CompilerContext.create`) | `theme` config key selects the theme object once per compile. |
| Rendering | `md_converter/renderer/word_renderer.py` | Reads presentation through `ctx.theme` (fonts, sizes, spacing, margins, table style, table font). |
| Post processing | `md_converter/renderer/post_processor.py` | Cover page, TOC, table borders/header and Word COM refresh - presentation owned outside the renderer. |
| Quality gates | `renderer/layout/{static_qa,rendered_qa,final_artifact_qa}.py` | Readability minimums, table-style acceptance (`"Grid"` required) and layout geometry are enforced on every compile. |
| Golden / Canonical guards | `md_converter/tests/test_golden.py`, `tests/golden/*` | Golden compares document structure + diagnostics + Mermaid backend, not presentation bytes. |
| Application boundary | `application/conversion_service.py`, `application/conversion_request.py` | The service passes `config_overrides` to `CompilerContext.create`; it owns no presentation decision. |
| GUI boundary | `gui/main_window.py`, `gui/request_builder.py`, `gui/preferences.py`, `gui/state.py` | The GUI never imports compiler/renderer internals; it carries configuration *intent* only. |
| Batch boundary | `gui/batch.py`, `gui/main_window.py` (`start_conversion`, `_on_worker_idle`) | One `BatchRun` drives the existing single-file path; sources are handed out serially. |

---

## 4. Frozen Decisions

### 4.1 Authoritative profile registry location (F1)

```text
md_converter/profiles/            # new, dependency-free presentation-configuration package
├── __init__.py                  # public re-exports
├── model.py                     # OutputProfile / PresentationSettings (frozen dataclasses)
├── registry.py                  # ProfileRegistry, stable IDs, default, safe fallback
└── theme_overrides.py           # bounded profile -> V1.5 theme overlay mapping
```

Rationale: the registry must be importable by **both** the GUI (for IDs and
display names) and the compiler (for resolution) while the GUI guard
(`tests/gui/test_main_window.py::test_gui_layer_imports_no_conversion_core`)
forbids the GUI from importing `md_converter.renderer`. A renderer-owned
registry would therefore be illegal by construction. `md_converter/profiles`
imports nothing from the compiler, renderer, pipeline, parser or GUI.

The GUI imports only profile **IDs and display names**; it never imports a
renderer type, never builds a theme and never applies an overlay.

### 4.2 Stable profile identifier format (F2)

* lowercase snake_case, `^[a-z][a-z0-9_]*$`;
* part of the public vocabulary; renaming is a breaking change (requires ADR);
* frozen IDs: `professional_report`, `business_report`, `academic`,
  `technical`, `clean_minimal`.

### 4.3 Initial profile set (F3)

| Order | ID | Display name |
|---|---|---|
| 1 | `professional_report` | Professional Report |
| 2 | `business_report` | Business Report |
| 3 | `academic` | Academic |
| 4 | `technical` | Technical |
| 5 | `clean_minimal` | Clean / Minimal |

Declaration order in the registry is the presentation order (deterministic).

### 4.4 Default profile (F4)

`professional_report`. Its declared presentation values are **identical to the
frozen V1.5 baseline**, so selecting the default profile produces a
presentation-identical document. This satisfies Product Specification §7
("no silent output-wide restyling").

### 4.5 Presentation properties a profile may control (F5)

Only properties that provably reach the artifact through the existing
`ctx.theme` path:

| # | Property | Theme path | Reaches the artifact via |
|---|---|---|---|
| 1 | Page margins (cm) | `page.margins.*` | `WordRenderer._apply_page_margins` |
| 2 | Body font family (4 Word slots) | `font_mapping.{ascii,hAnsi,eastAsia,cs}.body` | `set_style_font` / `set_run_font` |
| 3 | Heading font family (4 Word slots) | `font_mapping.*.heading` | `WordRenderer._configure_heading_styles` |
| 4 | Body size (pt) | `typography.body.size` | Normal style + body/table-cell runs |
| 5 | Heading sizes H1-H4 (pt) | `typography.heading.H{1..4}.size` | Heading 1-6 styles (H5/H6 follow H4) |
| 6 | Heading space before/after (pt) | `typography.heading.H{n}.before/after` | Heading style paragraph format |
| 7 | Body line spacing (multiple) | `paragraph.line_spacing.value` | Normal style + every paragraph |
| 8 | Paragraph space after (pt) | `paragraph.spacing.after` | Normal style + every paragraph |
| 9 | Code font + size + line spacing | `typography.code.*`, `code.line_spacing` | Code blocks and inline code |
| 10 | Table style + table font size | `table.style`, `table.font_size` | Table style assignment + cell runs |

### 4.6 Out-of-scope properties (F6)

Not profile-controllable in this release, because each would require a
renderer/post-processor change (i.e. a G2 stop trigger):

* colours (heading/body/table-header/code background) - **not** theme data; fixed
  constants in `V15Theme` and hardcoded in the post processor;
* heading bold/italic - the renderer forces bold runs, so the property would be
  a silent no-op;
* list spacing and list indent - hardcoded in `StyleResolver.list_item_style`
  and `WordRenderer.visit_ListItem`;
* figure sizing defaults - `figure_sizing` reads the frozen `figure` block and
  the real section geometry; `image_width` remains the canonical config key;
* ASCII-diagram presentation - fidelity-critical, frozen;
* table cell padding, vertical alignment, alignment policy - hardcoded;
* cover/TOC presentation - hardcoded in `DocxPostProcessor`;
* page size, page orientation, page-break policy, caption styling;
* document structure and the presence of cover/TOC/table styling
  (`enable_cover`, `toc`, `style_tables` stay canonical configuration).

### 4.7 Renderer integration point (F7)

One integration point only:

```text
config["output_profile"]            (top-level configuration key, string)
        ↓
profiles.registry.resolve_profile() (single authority, safe default fallback)
        ↓
profiles.theme_overrides.theme_presentation_overrides(profile)
        ↓
V15Theme.with_presentation_overrides(overlay)   (renderer-owned deep merge)
        ↓
existing rendering path (StyleResolver / WordRenderer / DocxPostProcessor)
```

* `V15Theme.with_presentation_overrides` knows only its own YAML structure; it
  has no knowledge of profiles.
* `theme_overrides.py` builds data only; it imports no renderer module.
* `CompilerContext.create` is the composition root and the only caller.
* The **default** profile is applied by doing nothing: the compiler's default
  theme *is* the default profile's presentation, so the theme object is left
  untouched (identity). That is the strongest form of "no silent restyling",
  and it also preserves a caller-supplied theme whose values were customised
  deliberately. A non-default profile is the only case that merges an overlay.
* The Renderer contains **no** `if profile == ...` branch: rules 4.1/4.2 of the
  product specification are satisfied by configuration.
* Profiles apply to the frozen V1.5 theme. When an explicitly requested
  non-default profile meets a legacy `theme=` object that cannot accept an
  overlay, the compiler emits a bounded `PROFILE002` warning instead of
  failing or silently ignoring the request.

### 4.8 GUI / settings integration point (F8)

* A single `Output Profile:` combo box beside the existing output-folder row
  (the conversion controls), visible in single-file and batch workflows.
  It is **not** placed in the Settings dialog: `WP-P12-07-02` freezes that
  surface to GUI-local folder preferences and asserts the absence of any
  `QComboBox` there.
* The GUI carries the profile as configuration intent
  (`ConversionRequest.config_overrides["output_profile"]`). It never derives a
  theme, a font or a file name.
* The product default needs no override: the request builder omits
  `output_profile` when the selection equals `DEFAULT_PROFILE_ID`, so the
  accepted request shape for existing behaviour is unchanged.
* Persistence uses the existing GUI-local store only
  (`GuiPreferences`, key `output/profile`); the registry stays the single
  profile authority and the store holds one identifier.
* The selector is locked while a conversion/batch is active through the new
  `StateEffect.profile_enabled` flag (`False` only in `CONVERTING`).

### 4.9 Batch locking behaviour (F9)

* The window captures the selected profile **once** in `start_conversion` and
  reuses it for every item of that `BatchRun` (`_start_batch_job`).
* No per-file profile selection exists; the selector is disabled during the run
  and `set_output_profile` refuses changes while input is locked.
* A profile chosen after the run applies only to the next batch; the captured
  value is released when the batch finishes (no leakage across runs).

### 4.10 Golden comparison policy (F10)

* No Golden baseline is updated by this program.
* The Golden suite compares document structure (paragraph texts, table cells,
  inline-shape count), frontmatter metadata, diagnostics and the Mermaid
  backend. Those are profile-invariant, and the default profile is
  presentation-identical to the frozen baseline, so Golden must stay green
  unchanged.
* An unexpected Golden change is a STOP/investigate trigger.

### 4.11 G2 stop triggers confirmed for this program (F11)

Profiles must not, and do not, need to: change document semantics; touch
Core/Canonical behaviour; change `ConversionService` semantics; change QA
semantics; change output naming/paths; break the CLI or public API; require a
new renderer architecture, a custom Word template system or a user-defined
profile DSL; or spread profile logic as duplicated conditionals.

Two concrete G2-adjacent constraints discovered during inspection and frozen
here as hard profile validation rules:

1. `FinalArtifactQA._check_table_styling` requires the effective table style
   name to contain `Grid` whenever `style_tables` is on and tables exist.
   Therefore every profile's `table_style` must be a member of the built-in
   *Grid* family (`Table Grid`, `Light Grid`, `Light Grid Accent 1`,
   `Medium Grid 1`, ...). A non-Grid style would fail the quality gate.
2. `StaticQA` fails when a profile drops the body font below 10pt or the table
   font below 8.5pt, and `RenderedQA` fails any run below 8pt. Profile values
   are validated against these gates at construction time.

---

## 5. Allowed / Forbidden Scope (module change plan)

Allowed (modified or added by this program):

```text
md_converter/profiles/                                  (new: model, registry, overlay, exports)
md_converter/config.py                                  (+ output_profile key, validation)
md_converter/compiler.py                                (one integration point)
md_converter/renderer/themes/v15_theme.py               (+ with_presentation_overrides)
md_converter/gui/main_window.py                         (+ selector, capture, locking)
md_converter/gui/preferences.py                         (+ output/profile key)
md_converter/gui/request_builder.py                     (+ optional profile intent)
md_converter/gui/state.py                               (+ StateEffect.profile_enabled)
md_converter/tests/test_output_profiles.py               (new)
md_converter/tests/test_output_profile_rendering.py      (new)
md_converter/tests/gui/test_output_profile_selection.py  (new)
md_converter/tests/gui/test_accessibility_window.py       (tab-order expectation extended)
Doc/V2/Implementation/Professional_Output_Profiles/*     (baseline, evidence, closure)
```

Forbidden (untouched by design):

```text
CANONICAL_SPEC.md / SPEC_CHANGELOG.md / ADRs   (no canonical change)
md_converter/renderer/** (other than the theme merge point)
md_converter/parser/**, md_converter/pipeline/**, md_converter/ast/**
md_converter/application/conversion_service.py (no semantic change)
md_converter/quality_gate.py, renderer/layout/**
md_converter/renderer/themes/default_v1_5.yaml  (frozen baseline)
md_converter/tests/golden/**                    (no baseline update)
README.md / pyproject.toml / packaging/**
```

---

## 6. Exit Criteria

| Criterion | Status |
|---|---|
| Single profile authority identified | PASS (`md_converter/profiles/registry.py`) |
| Configuration boundary identified | PASS (top-level `output_profile` config key) |
| No Core semantic change required | PASS (presentation theme data only) |
| Renderer integration bounded | PASS (one merge point, no profile branching) |
| Default compatibility strategy frozen | PASS (default = frozen V1.5 values) |
| Batch behaviour frozen | PASS (one profile captured per run) |
| GUI boundary respected | PASS (IDs/names only, no renderer import) |
| Golden policy frozen | PASS (no baseline update) |

---

## 7. Commit

`POP-01 freeze professional output profile architecture`
