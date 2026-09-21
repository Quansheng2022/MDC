# P12 Intake Analysis — Bounded Technical Discovery

## Artifact Header

| Field | Value |
| --- | --- |
| Program | MD_Converter |
| Lifecycle | P12 Product Evolution |
| Roadmap task | S/N 117 — Candidate Consolidation & Product Scope Selection |
| Scope | Discovery only. No product code, tests, Golden baseline, theme values or frozen authority changed. |
| Authority | P12 Intake instruction (Human, 2026-09-21); `CANONICAL_SPEC.md` 1.0 FROZEN; `P11/P11_P12_BOUNDARY.md` |
| Baseline | branch `master` @ `bc70fd69137ccaf045a0790bfdf1a69470ea0253` |
| Companion documents | `P12/P12_CANDIDATE_REGISTRY.md`; `P12/P12_PRODUCT_SCOPE_DECISION_PACKAGE.md` |

---

# 1. Method and Evidence Sufficiency

Discovery followed the sufficiency rule: stop when, for each candidate, the problem,
the current behaviour, the required behaviour decision, the likely affected subsystem and
the verification route are known.

Evidence order used: existing specification → existing issue record → existing acceptance
behaviour → relevant implementation location → bounded read-only reproduction.

```text
Read-only reproduction performed in this intake (no writes, no fixture changes):
  - one Markdown sample parsed with the public Parser to confirm the AST shape for a
    whitespace-aligned block and for an empty ATX heading
  - corpus spot-check of the whitespace-aligned block cited by OBS-04
No product regression suite was run: this is a specification/planning task (S/N 117).
```

Out-of-scope observations raised by this intake:

```text
none. No unrelated code-quality or architecture finding was recorded.
```

---

# 2. Candidate-by-Candidate Findings

## 2.1 P12-CAND-001 — Whitespace-aligned / simple-table recognition

**Current behaviour (verified)**

```text
markdown-it-py `default` preset (md_converter/parser/markdown_parser.py) recognises only
pipe/HTML tables. A whitespace-aligned block is parsed as one `paragraph` token and the
Parser builds a single Paragraph whose content is Text + SoftBreak nodes.

Corpus example (outside any fence), input_test/production_soak/cycle_01/Governance_AI_Engineering.md:1779-1787
   普通软件工程关注   Governance Engineering 额外关注
   ------------------ -------------------------------------------------
   代码是否能运行     AI是否有权这样修改
   ... 1 header row + 7 data rows + 1 dashed separator row, 2 spaces of leading indent

Renderer path: visit_Paragraph → soft breaks inside one paragraph. Columns are aligned by
whitespace under a proportional font only.
```

**Desired behaviour question**

Whether an aligned block should become a real `Table` AST node, and under which rule.
The decision is a product-semantics decision, not a rendering defect: Canonical 1.0
contains no such construct (`SPEC-FUNC-004` covers Markdown pipe tables).

**Likely change boundary**

```text
Option A  Pipeline pass (AST → AST): detect Paragraph nodes with a stable whitespace split,
          emit Table/TableRow/TableCell nodes, return PassResult, register in PassRegistry.
          Reuses the existing AST schema and the existing Renderer table path.
Option B  Parser-level block rule + Builder.
The choice is an architecture choice with real alternatives and must be made explicitly
if the candidate is selected (see §4 and the S/N 118 planning note).
```

**Likely acceptance scenario**

An acceptance case containing (a) a 2-column aligned block with a separator row and
(b) an aligned 2-column block without a separator row, asserting the resulting Word table
structure; plus negative cases asserting no conversion for aligned prose, for ordered-list
items such as `1.  **Authority-first**`, and for content inside code fences.

**Regression-sensitive behaviour**

```text
Document interpretation changes for some inputs → paragraph/table counts change.
False positives would silently convert ordinary prose (worst case: SPEC-INV-001 /
SPEC-GOAL-004 semantic regression).
Recognition overlaps conceptually with AsciiToMermaidPass structure detection, so
precedence must be defined and tested.
```

**Interaction with existing semantics**

`SPEC-FUNC-004`, `SPEC-INV-001`, `SPEC-GOAL-004`, `SPEC-ARCH-001/003`. A new capability
needs a new `SPEC-FUNC-0xx` entry in a P12 Canonical Specification proposal.

## 2.2 P12-CAND-002 — Figure Page-Fit / Figure Size Policy

**Current behaviour (verified)**

```text
md_converter/renderer/word_renderer.py visit_Image:
    width = self.ctx.config.get("image_width", 5)  → Inches(width)
    word_writer.add_image(src, alt, width=width)   → no height argument is ever passed
md_converter/config.py: "image_width": 5 (inches) — one fixed width for every image
md_converter/renderer/word_writer.py add_image/_add_image_from_file:
    height is accepted but never supplied; add_picture(src, width=width) only

Frozen theme already declares the policy that is not honoured:
md_converter/renderer/themes/default_v1_5.yaml (figure:)
    alignment: center
    max_width: content_width
    max_height: available_page_height
    preserve_aspect_ratio: true
    min_width: 8cm
    overflow_handling: [move_to_next_page, scale_down, warn]
md_converter/renderer/themes/default_v1_5.yaml (layout_qa.quality_gate)
    error: [overflow, clipping, broken_table, broken_figure], fail_on_error: true

Theme accessor gap:
    V15Theme.pagination_policy("figure") returns only
    {keep_together, allow_split, move_to_next_page_if_insufficient}
    → no typed accessor consumes the top-level `figure:` block, and a repository search
      confirms no compiler component reads max_width / max_height / overflow_handling
      (they occur only in the theme YAML). The declared values are therefore not applied;
      this is unhonoured declared configuration, not a wrong value.
    Related: StyleResolver.figure_style() hardcodes alignment + keep_together instead of
      reading theme figure.alignment.

QA blind spot:
    md_converter/renderer/layout/rendered_qa.py _finalize() seeds metrics["figure_overflow"] = 0
    and no check ever increments it; no error/warning is raised for a non-fitting figure.
    The only existing assertion is md_converter/tests/test_layout_plan.py, which checks that
    the metric *key* exists — it never asserts a non-zero value.
```

**Measured impact (Cycle-01 evidence, `evidence/figure_geometry.json`)**

```text
6 of 52 documents contain a figure taller than the 9.0 in text area;
3 exceed the page height itself (13.66 in / 12.68 in / 12.14 in);
offline fallback images show the opposite extreme (5.0 in x 0.32 in).
```

**Desired behaviour question**

Which declared overflow response is authoritative for this product, and what is the
minimum acceptable rendered size. The candidate is therefore narrower than "invent a
layout capability": the theme already declares the intent, and Canonical 1.0 is silent on
the maximum (`SPEC-INV-002` covers only readability *minimums*).

**Likely change boundary**

```text
DecisionEngine/LayoutPlan: compute and carry the size constraint for ContentType.FIGURE.
Renderer: apply the constraint when inserting the picture.
RenderedQA: make figure_overflow a real measurement feeding the declared gate category.
Theme: read the existing `figure` block; do NOT change frozen theme values.
A new BlockPlan/LayoutPlan field = LayoutPlan schema evolution (explicit P12 boundary item).
```

**Likely acceptance scenario**

Unit test: a very tall figure is scaled to fit or moved to the next page while keeping its
aspect ratio; a figure within the text area is unchanged. QA test: a deliberately
non-fitting figure yields a non-zero `figure_overflow` metric with a documented status.
Geometry re-measurement of the Cycle-01 figure documents after implementation.

**Regression-sensitive behaviour**

```text
Image extents change → geometry-based checks and any extent assertions change.
New diagnostics (e.g. a figure-overflow warning) enter DiagnosticCollector output, and the
Golden expectation includes the full diagnostics list → Golden impact must be assessed.
Acceptance signature uses min_inline_shapes, not extents, so signature impact may be none.
Golden baseline updates require investigate → ADR/Spec approval → approve baseline
(SPEC-INV-011; AGENTS.md §Golden Baseline).
```

**Interaction with existing semantics**

`SPEC-GOAL-001`, `SPEC-INV-002`, `SPEC-ARCH-010` (layout decisions belong to the
DecisionEngine; the Renderer only executes the plan) — this is why a Renderer-only fix
would violate the architecture and why the layout carrier must be decided explicitly.

## 2.3 P12-CAND-003 — Empty Heading Behaviour Policy

**Current behaviour (verified)**

```text
Parser:  HeadingBuilder accepts an empty heading; a source containing `## ` produces
         Heading(level=2, content=[]) — the empty heading is present in the AST.
StaticQA: emits warning semantic_empty_heading "Empty heading detected"
          (md_converter/renderer/layout/static_qa.py) → surfaces as QA_STATIC_WARN.
Renderer: visit_Heading substitutes the literal text "Heading" when the heading text is empty
          (md_converter/renderer/word_renderer.py).
TOC:     DocxPostProcessor._collect_headings collects paragraphs with Heading 1..3 styles, so
         the placeholder becomes a table-of-contents entry as well.
Spec:    no SPEC-ID defines empty-heading behaviour. Adjacent authority only:
         SPEC-FUNC-001 (headings 1–6), SPEC-GOAL-004 / SPEC-INV-001 (no silent semantic loss).
```

**Desired behaviour question**

Drop the empty heading, keep it as an empty heading, or treat it as a content error — and
with which diagnostic severity, TOC consequence and numbering consequence.

**Likely change boundary**

```text
If "keep empty":  Renderer-only change (never inject placeholder text); TOC entry remains.
If "drop":        the filter belongs before rendering (Parser/Pipeline), otherwise the TOC
                  and heading counts are computed from a structure that no longer matches.
If "error":       StaticQA severity change from warning to error.
Plus one normative statement in a P12 Canonical Specification proposal.
```

**Likely acceptance scenario**

A source containing `## ` (and the formatting-only variant) asserting: no injected
`Heading` text, TOC entries consistent with the delivered headings, and the agreed
diagnostic severity.

**Regression-sensitive behaviour**

```text
Heading counts and TOC entry counts change if the heading is dropped.
The acceptance corpus contains no empty heading, so corpus regression risk is low.
If the diagnostic severity changes, Structured QA output changes; the Golden sample has no
empty heading, so no Golden impact is expected — this must still be confirmed during
implementation.
```

**Interaction with existing semantics**

`SPEC-FUNC-001`, `SPEC-GOAL-004`, `SPEC-INV-001`, `SPEC-FUNC-016` (diagnostics) and the
existing `semantic_empty_heading` warning.

---

# 3. Evidence Index

| Candidate | Specification | Evidence record | Implementation touchpoint |
| --- | --- | --- | --- |
| P12-CAND-001 | no SPEC-ID (new construct); adjacent `SPEC-FUNC-004`, `SPEC-INV-001`, `SPEC-GOAL-004` | OBS-04; `P12_CANDIDATE_BACKLOG.md`; corpus `Governance_AI_Engineering.md:1779-1787` | `md_converter/parser/markdown_parser.py`, `md_converter/parser/builders/table.py`, `md_converter/pipeline/pass_registry.py` |
| P12-CAND-002 | no SPEC-ID for maximum figure size (`SPEC-INV-002` = minimum only) | ISSUE-003; `evidence/figure_geometry.json`; theme `figure:` and `layout_qa` blocks | `md_converter/renderer/layout/decision_engine.py`, `md_converter/renderer/word_renderer.py`, `md_converter/renderer/word_writer.py`, `md_converter/renderer/layout/rendered_qa.py` |
| P12-CAND-003 | no SPEC-ID (SPEC_GAP note 3) | ISSUE-009; `evidence/audit.json` (`headings_extra = ['Heading']`) | `md_converter/renderer/word_renderer.py`, `md_converter/renderer/layout/static_qa.py`, `md_converter/renderer/post_processor.py` |

---

# 4. Cross-Candidate Interaction

| Pair | Relationship | Finding |
| --- | --- | --- |
| 001 ↔ 002 | Independent | Different stages (recognition/AST construction vs layout sizing) and different acceptance scenarios. No shared interface, no shared schema change. |
| 001 ↔ 003 | Independent | Both can change node/heading counts for some inputs, but on disjoint constructs (aligned blocks vs empty headings) with no shared code path. |
| 002 ↔ 003 | Independent | Only shared property is that either can add a structured diagnostic; that is not a coupling and does not justify a combined package. |

```text
MERGE not recommended for any pair.
Reason: each candidate has a distinct change boundary and a distinct rollback boundary.
Combining them would make scope, verification and rollback less precise without reducing
total work. Sequencing (not merging) is the recommendation — see the decision package §E.
```

---

# 5. Product Scope Evaluation

Qualitative findings only; no scoring system and no manufactured precision.

| Dimension | P12-CAND-001 | P12-CAND-002 | P12-CAND-003 |
| --- | --- | --- | --- |
| 1. User value | High — recurring authoring pattern (aligned mapping blocks) | High — affects whether delivered documents are usable as-is | Medium — visible spurious content, single construct |
| 2. Problem clarity | Medium — a recognition rule must be chosen and bounded | High — the theme already declares the intent; the gap is which response is authoritative | High — the options are enumerable |
| 3. Specification readiness | Medium — needs a new SPEC-FUNC entry (new Markdown behaviour) | Medium-High — needs a normative maximum/page-fit statement; may need a LayoutPlan carrier decision | Medium — needs one normative sentence |
| 4. Change Surface | Medium (Parser or Pipeline; Renderer untouched) | Medium (DecisionEngine/LayoutPlan + Renderer + RenderedQA) | Small (Renderer, maybe Parser/Pipeline, QA severity) |
| 5. Regression Risk | High — false positives change the interpretation of existing prose | Medium — geometry and diagnostics change; Golden baseline path applies | Low — no corpus case changes except the empty-heading construct |
| 6. Interaction / Dependency | Medium — precedence vs AsciiToMermaidPass; pass ordering | Low — must not change frozen theme values; possible ADR if LayoutPlan evolves | Low — none |

---

# 6. Architectural Questions to Carry Into S/N 118

Recorded now, resolved only if the candidate is selected by the Human.

```text
CAND-001  Recognition ownership: Pipeline pass (AST → AST, reuses Table) vs Parser block rule.
          Default recommendation: Pipeline pass, so Parser semantics for existing Markdown stay
          unchanged and the change is expressible as PassResult. Confirm whether this is a
          genuine architecture decision requiring an ADR, or a bounded recognition rule.

CAND-002  Size-policy carrier: extend LayoutPlan/BlockPlan with a figure size constraint
          (LayoutPlan schema evolution, P12 boundary) vs reuse an existing carrier such as
          BlockPlan.metadata. SPEC-ARCH-010 requires the DecisionEngine to own layout decisions
          and the Renderer to execute them, so a Renderer-only fix is not acceptable.
          If LayoutPlan evolves, an ADR is likely genuinely required.

CAND-003  Behaviour placement: Renderer-only (keep empty) vs Parser/Pipeline (drop)
          vs QA severity (error). No new architecture is implied by any option.
```

```text
ADR decision is deferred to S/N 118 and will be stated explicitly per candidate
("ADR REQUIRED" or "ADR NOT REQUIRED"). No ADR is created during intake.
```

---

# 7. Sufficiency Statement

For all three candidates the intake can state: what the problem is, why it matters, the
current behaviour, the behaviour decision required, in-scope and out-of-scope behaviour,
the likely affected subsystem, and how a future implementation would be verified.

```text
Discovery STOPPED per the sufficiency rule. No further edge-case expansion performed.
No product code, test, Golden baseline, theme value or frozen authority was modified.
```
