# P12 Candidate Registry

## Artifact Header

| Field | Value |
| --- | --- |
| Program | MD_Converter |
| Lifecycle | P12 Product Evolution |
| Roadmap task | S/N 117 — Candidate Consolidation & Product Scope Selection |
| Authority | P12 Product Evolution Intake instruction (Human, 2026-09-21); `CANONICAL_SPEC.md` 1.0 FROZEN; `P11/P11_P12_BOUNDARY.md`; `P11/P11_MAINTENANCE_REGISTRY.md` §3 (Human Classification Decision 2026-09-21) |
| Baseline | branch `master` @ `bc70fd69137ccaf045a0790bfdf1a69470ea0253` |
| Status | S/N 117 COMPLETE / ACCEPTED — all three candidates Human-SELECTED for S/N 118 specification and planning |
| Product code modification | NOT AUTHORIZED |

Human Product Scope Selection (recorded 2026-09-21, S/N 118 master instruction):

```text
P12-CAND-001  SELECTED FOR SPECIFICATION
P12-CAND-002  SELECTED FOR SPECIFICATION
P12-CAND-003  SELECTED FOR SPECIFICATION
S/N 117: COMPLETE / ACCEPTED
S/N 118: AUTHORIZED（requirements / Canonical Specification proposal / ADR where
         genuinely necessary / implementation planning）
Product implementation: NOT AUTHORIZED
```

S/N 118 specification surface: `P12/P12_REQUIREMENTS.md`,
`P12/P12_CANONICAL_SPEC_PROPOSAL.md`, `P12/P12_IMPLEMENTATION_PLAN.md`.
ADR: NOT REQUIRED for all three candidates (recorded in `P12/P12_REQUIREMENTS.md`).

---

# 1. Registry Rules

```text
This file is the single authoritative P12 candidate registry for S/N 117.
Candidate IDs are stable once recorded here.
Dispositions are RECOMMENDED — never APPROVED / FINAL / AUTHORIZED.
No P0–P11 frozen record is modified by P12 intake; lineage references existing records.
Candidate records reference source evidence instead of duplicating it.
```

---

# 2. Stable Identifiers and Source Lineage

| Candidate ID | Title | Source record | Source classification | State |
| --- | --- | --- | --- | --- |
| P12-CAND-001 | Whitespace-aligned / simple-table recognition | `Doc/production_soak/cycle_01/CLASSIFIED_ISSUES_CYCLE_01.md` → OBS-04; adopted in `Doc/production_soak/cycle_01/P12_CANDIDATE_BACKLOG.md` | P12_CANDIDATE / Enhancement (new capability, not a v1.0 promise) | DISCOVERY ONLY |
| P12-CAND-002 | Figure Page-Fit / Figure Size Policy | `Doc/production_soak/cycle_01/CLASSIFIED_ISSUES_CYCLE_01.md` → ISSUE-003; `P11/P11_MAINTENANCE_REGISTRY.md` §3 | SPEC_GAP → P12_CANDIDATE (Human, 2026-09-21); P11 patch NOT AUTHORIZED | DISCOVERY ONLY |
| P12-CAND-003 | Empty Heading Behaviour Policy | `Doc/production_soak/cycle_01/CLASSIFIED_ISSUES_CYCLE_01.md` → ISSUE-009; `P11/P11_MAINTENANCE_REGISTRY.md` §3 | SPEC_GAP → P12_CANDIDATE (Human, 2026-09-21); P11 patch NOT AUTHORIZED | DISCOVERY ONLY |

Source evidence indexes (no duplication here):

```text
Doc/production_soak/cycle_01/PRODUCTION_USAGE_CYCLE_01_SUMMARY.md   corpus counts, per-document observations
Doc/production_soak/cycle_01/CLASSIFIED_ISSUES_CYCLE_01.md          REVIEW_TEMPLATE classification + SPEC_GAP notes
Doc/production_soak/cycle_01/evidence/audit.json                    delivered-artifact audit (52 records)
Doc/production_soak/cycle_01/evidence/figure_geometry.json          figure extents vs page text area
P11/P11_MAINTENANCE_REGISTRY.md                                     Human disposition of Cycle-01 issues
```

---

# 3. Identifier Normalization

`P12-CAND-002` and `P12-CAND-003` are assigned here, per the S/N 117 instruction, to
Figure Page-Fit / Figure Size Policy and Empty Heading Behaviour Policy.

`Doc/MDC_Roadmap_0920.md` §"当前我建议的 P12 候选池" contains an earlier *suggested*
pool that used `P12-CAND-002..005` for different subjects (Complex table handling,
Long-document robustness, Image handling refinement, CN/EN typography refinement). That
section is a proposal only:

```text
Doc/production_soak/cycle_01/P12_CANDIDATE_BACKLOG.md, verbatim:
"This cycle did not produce independent evidence that would justify them, and one of them
 is entangled with a defect:"
```

Resolution recorded by this intake:

```text
The suggested pool in Doc/MDC_Roadmap_0920.md was NOT adopted by Cycle-01 classification.
IDs 002/003 are therefore assigned to the two SPEC_GAP-derived candidates listed above.
The suggested-pool subjects are NOT registered as P12 candidates (§6 below).
The Human roadmap document is untracked Human work and was NOT modified by this intake.
```

---

# 4. Candidate Records

## 4.1 P12-CAND-001 — Whitespace-aligned / simple-table recognition

| Field | Value |
| --- | --- |
| Source issue / observation | OBS-04 (Cycle-01), corpus evidence: 3 aligned blocks outside code fences in 2 documents; 89 aligned blocks inside code fences in 26 documents |
| Current classification | P12_CANDIDATE / Enhancement — no Canonical SPEC-ID promises this construct |
| Problem statement | Authors write two-column data using whitespace alignment. Markdown has no construct for it, so the compiler produces prose: the data cannot be sorted, styled, or given a repeating header in Word. |
| User-visible impact | Aligned mapping / definition / before-after blocks render as soft-broken lines whose columns only visually approximate alignment under a proportional body font (Calibri / DengXian); no table object, no header repeat, no column structure. |
| Current known behaviour | markdown-it-py `default` preset emits `table` only for pipe/HTML tables. A whitespace-aligned block becomes one `paragraph` token; the Parser builds a single `Paragraph` whose content is `Text` + `SoftBreak` nodes (verified in this intake). Renderer emits soft-broken runs inside one paragraph. |
| Behaviour decision required | Should whitespace-aligned blocks become `Table` AST nodes at all; if yes, under which recognition rule (column count, presence of a delimiter row, indentation, minimum row count, eligible container); and what happens when recognition is ambiguous (keep as prose + diagnostic, or convert). |
| Probable subsystem | Parser (`md_converter/parser/`) or Pipeline pass (`md_converter/pipeline/passes/`) for recognition + AST construction. Renderer is not implicated — it already renders `Table`. |
| Probable implementation surface | New recognition pass + `PassRegistry` registration, **or** a new Parser block rule + Builder; existing `Table` / `TableRow` / `TableCell` AST nodes reused (`md_converter/constants/node_type.py` unchanged). |
| Probable verification surface | Unit tests for the recognition rule (positive + negative); a new acceptance case containing a whitespace table; regression that ordinary aligned prose and ordered-list items (`1.  **text**`) are NOT converted; re-audit of the 52-document Cycle-01 corpus for 0 unexpected tables. |
| Dependencies | Recognition precedence against `AsciiToMermaidPass` (structure-based detection over non-fenced text) and pass ordering against `NormalizePass`. |
| Interaction with other P12 candidates | None semantically. Shares only the general property "converts some inputs into different node types" with P12-CAND-003. |
| Open uncertainty | Minimum rows/columns; whether a dash separator row is required; eligibility inside lists/blockquotes; default-on vs opt-in. |
| Recommended disposition | **SELECT (RECOMMENDED)** |

## 4.2 P12-CAND-002 — Figure Page-Fit / Figure Size Policy

| Field | Value |
| --- | --- |
| Source issue / observation | ISSUE-003 (DEFECT / P2; 6 of 52 documents contain a figure taller than the text area, 3 taller than the page) |
| Current classification | SPEC_GAP → P12_CANDIDATE — Canonical 1.0 defines no maximum figure size / page-fit rule |
| Problem statement | There is no figure size policy. Every image is inserted at a fixed 5.0 in width with no height cap, so tall figures exceed the page; the opposite extreme (a very wide fallback image scaled to 5.0 in wide) is unreadably small. |
| User-visible impact | Delivered DOCX contains figures that cannot fit one page (up to 13.66 in tall) and require manual correction; offline fallback images can be 0.32 in tall — both below the "directly usable for formal delivery" goal (SPEC-GOAL-001). |
| Current known behaviour | `config.image_width = 5` in is applied to all images; no height cap. The frozen theme already declares a figure policy (`figure.max_width: content_width`, `figure.max_height: available_page_height`, `overflow_handling: [move_to_next_page, scale_down, warn]`), but `V15Theme` exposes no accessor for that block — only `pagination_policy("figure")` = `{keep_together, allow_split, move_to_next_page_if_insufficient}`. `RenderedQA._finalize()` seeds `metrics["figure_overflow"] = 0` and no check ever increments it, although the theme lists `broken_figure` under `layout_qa.quality_gate.error` with `fail_on_error: true`. |
| Behaviour decision required | Which declared overflow response is authoritative (scale to fit vs move to next page vs split vs warn-only); whether aspect ratio is always preserved; the minimum acceptable rendered size and what happens when the floor and the cap conflict (SPEC-INV-002 readability); whether an unfittable figure is a QA warning or a FAIL. |
| Probable subsystem | Layout (`DecisionEngine` / `LayoutPlan`) + Renderer (image insertion) + QA (`RenderedQA`) + theme consumption. |
| Probable implementation surface | `md_converter/renderer/layout/decision_engine.py` (and `layout_plan.py` if a size constraint must be carried), `md_converter/renderer/word_renderer.py` `visit_Image`, `md_converter/renderer/word_writer.py` `add_image`, `md_converter/renderer/layout/rendered_qa.py`, plus read-only consumption of the existing theme `figure` block (theme *values* are frozen). |
| Probable verification surface | Unit test: tall figure is clamped / scaled / moved. QA test: `figure_overflow > 0` yields a documented status. Geometry re-measurement over the Cycle-01 figure documents. Integrity check of Golden / acceptance signatures (`inline_shapes`, diagnostics). |
| Dependencies | Frozen theme values must not change (a new theme key would require RFC/ADR). Any new `LayoutPlan` field is LayoutPlan schema evolution (P12 boundary item) and may require an ADR. Golden baseline changes require the investigate → ADR/Spec approval → approve-baseline path (SPEC-INV-011). |
| Interaction with other P12 candidates | None semantically. Shares only the general property "can add a structured diagnostic" with P12-CAND-003. |
| Open uncertainty | Precedence of scale-down vs move-to-next-page; interaction with the configured readability minimums; whether width overflow (wider than the text area) is in scope; behaviour when only part of a figure fits. |
| Recommended disposition | **SELECT (RECOMMENDED)** |

## 4.3 P12-CAND-003 — Empty Heading Behaviour Policy

| Field | Value |
| --- | --- |
| Source issue / observation | ISSUE-009 (DEFECT / P4; 1 of 52 documents contains an empty ATX heading) |
| Current classification | SPEC_GAP → P12_CANDIDATE — Canonical 1.0 does not state how an empty heading must behave |
| Problem statement | An empty heading has no defined product behaviour. The renderer substitutes the literal English word `Heading`, which then also appears in the table of contents. |
| User-visible impact | A document authored with `## ` gains a spurious `Heading` paragraph and a matching TOC entry — injected content that the author never wrote. |
| Current known behaviour | The Parser builds `Heading(level=2, content=[])` — the empty heading exists in the AST (verified in this intake). `StaticQA` already reports warning `semantic_empty_heading` ("Empty heading detected"). `WordRenderer.visit_Heading` replaces empty text with `"Heading"`. The TOC collector then includes that paragraph as a TOC entry. |
| Behaviour decision required | Drop the empty heading, keep an empty heading, or reject it as a content error; the diagnostic severity (existing warning vs error); the effect on TOC entries and heading numbering; and whether `## ` and a heading whose inline content is only formatting behave the same. |
| Probable subsystem | Renderer (`word_renderer.visit_Heading`) and/or Parser–Pipeline (if "drop" is chosen, filtering must occur before rendering) + StaticQA severity + TOC consistency in the Post-Processor. |
| Probable implementation surface | `md_converter/renderer/word_renderer.py` (heading rendering), `md_converter/renderer/layout/static_qa.py` (severity), optionally a normalization/semantic pass, plus TOC-collection consistency in `md_converter/renderer/post_processor.py`. |
| Probable verification surface | Unit test: empty heading produces no placeholder text and a consistent TOC. StaticQA severity assertion. Acceptance / Golden integrity check. |
| Dependencies | None. |
| Interaction with other P12 candidates | None. Independent of P12-CAND-001 and P12-CAND-002. |
| Open uncertainty | The policy choice itself; whether "drop" also removes the numbering/TOC entry; whether an empty H1 still triggers page-break behaviour. |
| Recommended disposition | **SELECT (RECOMMENDED)** |

---

# 5. Recommended Dispositions (Summary)

| Candidate ID | Recommended disposition | Basis |
| --- | --- | --- |
| P12-CAND-001 | SELECT (RECOMMENDED) | Real, recurring corpus evidence for a missing capability; bounded recognition surface; largest regression surface → needs the strictest verification plan. |
| P12-CAND-002 | SELECT (RECOMMENDED) | Affects delivery usability directly (SPEC-GOAL-001); the frozen theme already declares the policy and a gate category that the compiler does not honour; verification is measurable geometry. |
| P12-CAND-003 | SELECT (RECOMMENDED) | Small, well-understood behaviour policy; currently injects content the author did not write; smallest change surface of the three. |

```text
No candidate is recommended for MERGE (see P12/P12_INTAKE_ANALYSIS.md §4).
Dispositions above are RECOMMENDED. They are not approved, and no implementation is authorized.
```

---

# 6. Not Registered by This Intake

```text
Complex table handling                  no independent Cycle-01 evidence (no merged/rowspan
                                        Markdown source; ISSUE-004 gridSpan was a Word artefact)
Long-document robustness                no Cycle-01 failure (largest docs converted, 0 loss)
Image handling refinement               no independent evidence beyond CAND-002's size policy
CN/EN typography refinement             no independent evidence
Mermaid triangle layout                 previously dispositioned as content/authoring, not P12
PDF / HTML backend, footnotes, cross references, incremental or multi-threaded compilation
                                        explicit non-goals of the current scope
```

These subjects remain unregistered. Registering any of them requires a separate Human
instruction; this intake does not create work packages for them.
