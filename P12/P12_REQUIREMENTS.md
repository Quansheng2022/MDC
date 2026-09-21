# P12 Requirements — Human-Selected Evolution Candidates

## Artifact Header

| Field | Value |
| --- | --- |
| Program | MD_Converter |
| Lifecycle | P12 Product Evolution |
| Work item | S/N 118 — Requirements / Canonical Specification Proposal / ADR / Implementation Planning |
| Authority | S/N 118 master instruction (Human, 2026-09-21). All three candidates SELECTED FOR SPECIFICATION. |
| Baseline | branch `master` @ `8ff7aef5ce43a169737bf331e46f7b5db0cdf212` |
| Status | PROPOSED requirements — not canonical, not implemented |
| Scope of this document | Behavioural requirements only. Specification delta: `P12/P12_CANONICAL_SPEC_PROPOSAL.md`. Execution: `P12/P12_IMPLEMENTATION_PLAN.md`. |
| Product code / tests / Golden / theme | UNCHANGED |

Evidence and discovery detail live in `P12/P12_INTAKE_ANALYSIS.md` and are referenced, not repeated.
All decisions below are labelled **PROPOSED**.

---

# 0. ADR Decisions

```text
P12-CAND-001  ADR NOT REQUIRED
    A pipeline recognition pass uses the existing TransformPass / PassRegistry extension point
    and the existing Table AST. No pipeline stage, ownership boundary, or durable contract changes.
    Rejected alternative that WOULD have required an ADR: markdown-it block rule inside the Parser
    (changes tokenization for all inputs). Rejected because it is a wider, less reversible surface
    with no behavioural benefit over a pass.

P12-CAND-002  ADR NOT REQUIRED
    The size policy is already declared by the frozen theme (`figure.max_width` / `max_height` /
    `min_width`). The proposal reads that declared policy through the existing StyleResolver path
    (SPEC-ARCH-009) and verifies it in RenderedQA (SPEC-QA). No LayoutPlan contract expansion, no
    ownership migration between Layout and Renderer, no new cross-layer abstraction, and no new
    runtime configuration contract.
    Rejected alternative that WOULD have required an ADR: carrying the figure size bound in
    LayoutPlan/BlockPlan (LayoutPlan schema evolution). Rejected as unnecessary — the Renderer
    already owns image insertion and the LayoutPlan's figure intent (keep_together) is unchanged.

P12-CAND-003  ADR NOT REQUIRED
    A bounded rendering rule on an existing node type; no new stage, contract, or ownership change.

No ADR document was created. This section is the required record of that decision.
```

---

# 1. P12-CAND-002 — Figure Page-Fit / Figure Size Policy

Planning order position: 1 of 3.

**Problem.** Delivered documents contain figures that cannot fit the page. The compiler applies a
single fixed width (`config.image_width = 5 in`) with no height bound, although the frozen theme
declares a figure size and overflow policy that no component reads. Cycle-01 measured 6 of 52
documents with a figure taller than the text area and 3 taller than the page (up to 13.66 in).

**Current behaviour.** `WordRenderer.visit_Image` inserts every image at the configured width and
the natural aspect ratio; `WordWriter.add_image` accepts a height but is never given one; the theme
`figure:` block (`max_width`, `max_height`, `min_width`, `overflow_handling`) has no accessor;
`StyleResolver.figure_style()` hardcodes alignment; `RenderedQA` seeds `metrics["figure_overflow"]`
but never measures anything.

**Required / PROPOSED behaviour.**

Definitions (interpretation of the existing frozen theme tokens; **CLAR-02**: the normative
constraint is the *effective section content box*, derived from the actual section geometry):

```text
effective section content box
                width  = section page width  - left margin - right margin
                height = section page height - top margin  - bottom margin
                (derived from the section actually being rendered; never a hard-coded constant)
current baseline/reference geometry
                A4 portrait 21.0 x 29.7 cm with 1 in / 2.54 cm margins
                -> approximately 15.92 cm x 24.62 cm
                   (reference for the current frozen theme; not a universal magic constant)
intrinsic size  the image's own pixel dimensions, read from the image header
target width W0 min(config image_width, effective content width) = min(5 in, 15.92 cm) = 12.70 cm
```

Ownership split (CLAR-02):

```text
converter owns:   figure sizing / aspect-ratio preservation / width-height bounds /
                  never-upscale behaviour / minimum-width diagnostic / overflow measurement /
                  placement semantics exposed to Word（keep-together）
Word owns:        final physical pagination
converter does NOT promise: an exact physical page number or deterministic final Word pagination
```

Sizing rule, applied per figure, deterministic:

```text
1. Measure the intrinsic size (aspect ratio = px_width / px_height).
   If the image cannot be measured or read, the existing fallback behaviour is unchanged.
2. Normal fit:  H = W0 / aspect. If H <= available text height -> insert at (W0, H).
   Placement is Word-owned: the figure keeps the existing keep-together paragraph property, so
   Word moves it to the next page when the remaining space on the current page is insufficient.
   The compiler does not measure remaining page space (no pagination engine exists).
3. Scale down:  if H > available text height -> H' = available text height,
                 W' = H' x aspect. Insert at (W', H').
4. Readability floor: if W' < theme figure.min_width (8 cm) -> insert the fitted size anyway
   (page fit is mandatory) and report the condition (§ Diagnostics).
5. Never upscale beyond W0; never exceed either text-area bound.
6. Always insert with an explicit width AND height so Word does not re-derive the size;
   aspect ratio is preserved (subject only to integer rounding).
```

This implements the theme's declared `overflow_handling` order
(`move_to_next_page` -> `scale_down` -> `warn`) and makes `figure.max_height` effective.

**User-visible semantics.** A figure always fits on one page by itself; tall figures are delivered
at reduced size instead of overflowing; a figure that cannot be represented above the declared
minimum width is delivered fitted and reported. Figures that already fit are unchanged.

**In scope.** Raster figures inserted from a file path or a data URI (Mermaid renders, ASCII
fallbacks, `![...]` images); height and width bounding; aspect-ratio preservation; the readability
floor check; render-time verification of the delivered extents.

**Out of scope.** Rotation or landscape sections for figures; splitting a table-like figure across
pages; a minimum-height/legibility floor for extremely wide figures (the 5.0 x 0.32 in offline
fallback case — caused by the fallback image's aspect ratio, not by sizing); upscaling small
images; DPI normalization; diagram layout quality; vector (SVG/DrawingML) figure conversion
(theme `figure.format` is not proposed for change).

**Compatibility expectations.** Any figure already inside the text area keeps its current size, so
documents without an oversized figure are unchanged. Documents with an oversized figure change
from "figure exceeds the page" to "figure fits at reduced size" — the intended fix.

**Failure behaviour.** If the image cannot be read, the existing documented fallback text path is
kept (unchanged). If a delivered figure would exceed the text area, that is a **quality-gate
failure**, not a warning: `RenderedQA` reports `figure_overflow` as an error, which — with the
theme's `layout_qa.quality_gate.fail_on_error: true` — fails the gate rather than silently passing.

**Diagnostics.**

```text
RENDER005 (WARNING)  figure scaled below the theme figure.min_width floor — includes the
                     resulting width/height and the declared floor
figure_overflow (RenderedQA error)      a delivered figure exceeds the available text area
figure_below_min_width (RenderedQA warning)  count of figures scaled below the declared floor
No new diagnostic for a normal fit.
```

**Acceptance examples.** See `P12/P12_IMPLEMENTATION_PLAN.md` §4 (cases FIG-1..FIG-7).

**Known implementation constraints.** The available text area must be derived from the section the
renderer is building (page size minus margins), not hardcoded; the theme values are frozen and are
read, never written; the intrinsic size must be obtained without adding a new dependency
(`docx.image.Image`, already part of the pinned python-docx, exposes pixel dimensions and native
size — verified during this intake).

**Open assumptions.** (a) `available_page_height` means the full text-area height, not the
remaining space on the current page (the compiler cannot see the latter). (b) The 8 cm floor is the
only declared readability floor for raster figures; theme `figure.min_height: auto` provides no
height floor and none is invented. (c) `SPEC-INV-002`'s `figure_text: 8pt` applies to figure text
inside a figure, not to raster image scale, and is therefore not used as the raster floor.

---

# 2. P12-CAND-001 — Whitespace-aligned / Simple-Table Recognition

Planning order position: 2 of 3.

**Problem.** Authors write two-column data as whitespace-aligned text. The compiler has no such
construct, so the data becomes a soft-broken paragraph and cannot be structured as a table.

**Current behaviour.** markdown-it-py `default` recognises only pipe/HTML tables. A whitespace
aligned block becomes one `Paragraph` whose content is `Text` and `SoftBreak` nodes (line structure
is preserved in the AST; leading indentation is consumed by the parser). Rendered as
soft-broken runs inside one paragraph.

Measured during S/N 118 (read-only scan of 52 corpus documents, 15 acceptance fixtures, the Golden
sample, 2 fixture files and 17 `input_test` documents):

```text
blocks satisfying the proposed recognition rule:      2  (both in Governance_AI_Engineering.md)
documents with at least one match:                    1
documents containing a ruler line that fails the rule: 1  (2 blocks the strict rule rejects;
                                                        no diagnostic is emitted — CLAR-01)
false positives in 85 scanned documents:              0
separator-free 2-column blocks that would match without the ruler requirement: 0
=> the S/N 117 intake figure "3 aligned blocks in 2 documents" is a looser count than the strict
   contract; the third block is a wrapped field list in QCFP-MTF 2.2_架构设计.md whose multi-space
   gaps shift per line and must NOT become a table.
```

**Required / PROPOSED behaviour.** A new pipeline recognition pass converts a paragraph into a
`Table` only when every condition below holds. The unit of recognition is a `Paragraph` that is a
direct child of `Document` (reconstructed lines = the paragraph's `Text` segments split at
`SoftBreak` nodes, trailing whitespace stripped).

```text
R1  at least 3 lines
R2  line index 1 is a ruler line: only spaces and >= 2 runs of >= 3 hyphens, runs separated by
    at least one space  (Pandoc simple-table style; the ruler is a marker and need not be aligned
    with the data columns — required by the real corpus evidence, where it is decorative)
R3  every non-ruler line contains exactly one run of >= 2 spaces (the column gap) and no tab
R4  both cells of every non-ruler line are non-empty after stripping  (blank cell => ambiguous)
R5  the gap intervals [s_i, e_i) of all non-ruler lines share a common anchor:
    anchor b = max(s_i) < min(e_i); column 2 starts at b
R6  no line contains '|'
R7  the paragraph contains only Text and SoftBreak inline nodes (no strong/emphasis/link/image/
    inline-code), so cell content is plain text in v1
```

On a match the paragraph is replaced by one `Table` with exactly 2 columns:
row 0 = the line before the ruler (header; the existing renderer repeats the first row as the Word
table header), rows 1..n = the remaining lines (body). Each cell is
`TableCell(content=[Text(cell_text)])`. The ruler line produces no row. A block that satisfies R2
but fails any other condition is **not** converted.

**User-visible semantics.** Aligned two-column blocks that carry a ruler line are delivered as real
Word tables (grid, repeated header, column structure). Everything else is delivered exactly as
today.

**In scope.** Top-level paragraphs; exactly 2 columns; ≥ 1 header row and ≥ 1 body row; plain-text
cells; CJK and Latin content; leading indentation of the block (up to 3 spaces, consumed by the
parser); trailing whitespace.

**Out of scope.** 3 or more columns; formatted/rich cells (links, images, emphasis, inline code);
multi-line cells or continuation lines; blocks inside lists or blockquotes; separator-free blocks;
blanks/short blocks; piping; tables written with pipes or HTML (already handled by the Parser);
aligning/gridlining the resulting Word table beyond the existing table styling.

**Compatibility expectations.** Documents that contain no block satisfying every rule are
unchanged, including documents that contain aligned prose, wrapped field lists, indented code,
fenced code (a `CodeBlock`, never a paragraph), and existing pipe tables. Documents that contain a
matching block change from prose to a table — the intended new behaviour. The pass is disabled via
configuration (`simple_tables.enabled`), so the change can be turned off without a rollback.

**Failure behaviour.** Ambiguous or unrecognised input stays ordinary paragraph content — the
recognition never guesses and never drops content (SPEC-INV-001 / SPEC-GOAL-004).

**Diagnostics（CLAR-01: 默认不产生诊断）**

```text
Failed recognition is NOT a diagnostic condition by default:
  - a block that does not satisfy R1..R7 is preserved as a Paragraph and emits NO diagnostic;
  - SIMPLE001 MUST NOT be emitted merely because a ruler is present and recognition failed;
  - no diagnostic on a successful conversion either (the resulting table is visible in output).

SIMPLE001 is NOT part of the approved default behaviour. It may only ever be introduced later for
a narrowly defined strong near-match case with demonstrable user value — never to expose internal
recognition decisions. Default implementation: ordinary non-match -> Paragraph, no diagnostic.
```

**Acceptance examples.** `P12/P12_IMPLEMENTATION_PLAN.md` §4 (cases SIMPLE-1..SIMPLE-7).
Rejected ruler-bearing near-matches are part of the Golden-impact analysis, not only successful
conversions.

**Known implementation constraints.** The AST line/gap information must be read from `Text` +
`SoftBreak` nodes (that is all the Parser preserves); the pass must not touch non-`Paragraph` nodes;
`Document` is rebuilt immutably (`replace`), never mutated; the pass must be deterministic and must
not depend on the corpus. `NormalizePass` merges adjacent `Text` nodes only, so line structure is
unaffected.

**Open assumptions.** (a) Requiring the ruler line is the decisive false-positive guard; measured
corpus behaviour supports it. (b) Two columns only, matching the original candidate scope; a wider
rule is deliberately deferred. (c) Cells are plain text in v1 — formatted cells would require
offset-to-inline-node mapping and are deferred.

---

# 3. P12-CAND-003 — Empty Heading Behaviour Policy

Planning order position: 3 of 3.

**Problem.** An empty heading has no defined behaviour; the renderer injects the literal word
`Heading`, which also becomes a table-of-contents entry — content the author never wrote.

**Current behaviour.** The Parser builds `Heading(level=n, content=[])` (verified for `## `,
`##\t`, `##  `). `StaticQA` reports warning `semantic_empty_heading` ("Empty heading detected"),
surfaced as `QA_STATIC_WARN`. `WordRenderer.visit_Heading` substitutes the text `Heading`.
`DocxPostProcessor._collect_headings` collects Heading 1–3 paragraphs by style, so the placeholder
becomes a TOC entry. Canonical 1.0 states no rule for this state.

Corpus/fixture scan during S/N 118: exactly 1 of 85 documents contains an empty heading
(`input_test/production_soak/cycle_01/港股日线技术分析报告子系统技术文档.md:65`, matching ISSUE-009);
none of the 15 acceptance fixtures, the Golden sample, or the test fixture files contains one.

**Required / PROPOSED behaviour — WARN + DROP.**

```text
1. A heading whose plain text is empty after stripping is NOT rendered: no paragraph, no run,
   no heading counter increment.
2. The AST keeps the Heading node — source truth is preserved for passes, QA and diagnostics.
3. The existing StaticQA warning semantic_empty_heading remains the announcement of the condition
   (severity WARNING, unchanged). No new diagnostic code and no severity change are introduced.
4. TOC and heading numbering are unaffected by construction: both derive from the rendered
   document, which no longer contains the empty heading.
5. The rule is defined on the plain-text rendering of the heading, so all variants (`## `,
   whitespace-only, and any heading whose inline content produces no text) behave identically.
```

Rejected alternatives: **KEEP EMPTY** (would emit an empty styled paragraph and — unless the TOC
collector gains an exception — an empty TOC entry; more rules for a worse result);
**ERROR** (would fail documents that currently convert successfully with a warning, e.g. the corpus
document above — disproportionate for a benign authoring artefact); the current placeholder
behaviour (explicitly excluded by the S/N 118 instruction).

**User-visible semantics.** A spurious `Heading` paragraph and its TOC entry disappear. The
delivered document contains only headings the author actually titled. The condition is still
reported through the existing QA warning, so the omission is not silent (SPEC-INV-006).

**In scope.** Empty ATX headings at any level in the rendered document; TOC consistency; the
existing diagnostic's continued presence.

**Out of scope.** Non-empty headings; orphan headings with no following content; heading level
beyond 1–6; TOC styling and field behaviour; source-file repair; changes to `SPEC-FUNC-001`
heading support; a general "no synthesized text" invariant (see below).

**Compatibility expectations.** Documents without empty headings are unchanged. Documents with an
empty heading lose the two synthetic artefacts. No test or acceptance fixture in the repository is
affected (measured).

**Failure behaviour.** None — the state is benign and deterministic; it is reported, not failed.

**Diagnostics.** No new code. The existing `semantic_empty_heading` WARNING (QA_STATIC_WARN) keeps
its current meaning and severity.

**Acceptance examples.** `P12/P12_IMPLEMENTATION_PLAN.md` §4 (cases HEAD-1..HEAD-6).

**Known implementation constraints.** The guard belongs where the delivered document is produced;
the TOC collector must not need a special case; `semantic_empty_heading` must still fire, which
requires the AST to keep the node (it does under this proposal).

**Open assumptions.** (a) The diagnostic stays a WARNING rather than becoming an ERROR. (b) A
heading consisting only of an alt-less image is *not* empty, because `Image.to_plain_text()`
returns the literal `Image`; that convention belongs to image plain-text extraction, not to the
heading policy, and is recorded as an out-of-scope boundary rather than changed here.

Deliberate non-proposal: a general invariant "the compiler shall never synthesize text" is **not**
proposed, because existing documented degradation paths (image/diagram fallback text, the empty-TOC
placeholder) intentionally synthesize text and are governed by `KNOWN_LIMITATIONS_v1.0.0.md`.
Inventing that invariant would contradict accepted behaviour.

---

# 4. Cross-Candidate Requirement Interactions

```text
AST invariants      Candidates 001 and 003 both add nodes; neither mutates existing nodes.
                    003 relies on the AST *keeping* the empty heading while the renderer omits it.
                    No conflict: 001 replaces a Paragraph with a Table; 003 changes no node type.
Diagnostics         001 adds no diagnostic by default（CLAR-01）; 002 adds WARNING RENDER005 plus
                    two RenderedQA metrics; 003 adds nothing. No code collision, no severity
                    interaction.
Theme/config        002 reads the existing frozen `figure:` block read-only; 001 adds a new
                    `simple_tables.enabled` config flag. No frozen theme value changes.
Layout ownership    002 keeps layout intent (keep_together) as-is and keeps sizing in the render
                    path; 001 leaves Layout untouched (the new Table flows through the existing
                    table layout path); 003 has no layout effect beyond removing a block from the
                    delivered document.
Renderer ownership  002 and 003 both touch word_renderer.py in disjoint methods
                    (visit_Image / visit_Heading). Different hunks, independently revertable.
Golden-visible      001 and 003: none predicted (0 matching blocks and 0 empty headings in the
                    Golden sample — measured). 002: none predicted (no figure is clamped in the
                    Golden sample). All three must be confirmed by running the existing Golden at
                    implementation time; no baseline update is authorized now.
Acceptance           Independent cases; no shared fixture is required.
```

```text
PROPOSED: the three candidates remain independent in implementation, verification and rollback.
No merge is proposed.
```
