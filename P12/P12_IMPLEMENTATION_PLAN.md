# P12 Implementation Plan

```text
P12 PROPOSAL

NOT YET CANONICAL

NOT YET IMPLEMENTED
```

## Artifact Header

| Field | Value |
| --- | --- |
| Program | MD_Converter |
| Lifecycle | P12 Product Evolution |
| Work item | S/N 118 — implementation, acceptance and regression planning |
| Baseline | branch `master` @ `8ff7aef5ce43a169737bf331e46f7b5db0cdf212` |
| Status | PROPOSED plan — no implementation authority |
| Requirements | `P12/P12_REQUIREMENTS.md` |
| Specification delta | `P12/P12_CANONICAL_SPEC_PROPOSAL.md` |
| ADR | NOT REQUIRED for all three candidates（`P12/P12_REQUIREMENTS.md` §0） |

Nothing in this document has been executed. No source file, test, fixture, Golden baseline,
theme value or frozen authority was modified while producing it.

---

# 1. Shared Execution Rules for the Future Implementation

```text
1. Implementation may start only after Human approval of the P12 specification package and a
   separate Human implementation authorization.
2. Each candidate is implemented as one bounded change package with its own verification and
   rollback; the three packages are not merged.
3. Golden baselines are never updated by the implementation agent. A legitimate delta is reviewed
   and updated only through investigate → approval → authorized baseline update (SPEC-INV-011).
4. The Cycle-01 production corpus remains evidence-only: it is untracked, is never referenced by
   canonical tests, and is never copied wholesale into the repository.
5. Existing tests are extended or added; existing assertions that encode accepted behaviour are not
   weakened to accommodate new behaviour.
```

---

# 2. P12-CAND-002 — Figure Page-Fit / Figure Size Policy

## 2.1 Objective

Make the frozen theme's declared figure size policy effective: every delivered figure fits the
page's text area, aspect ratio preserved, with a reported diagnostic when the fitted size falls
below the declared minimum width, and a real QA measurement behind the declared gate category.

## 2.2 Proposed technical design

```text
Policy source      theme `figure:` block, read-only（max_width, max_height, min_width,
                   preserve_aspect_ratio, overflow_handling). No theme value changes.
Bounds             available text area derived from the section being rendered
                   (page width/height minus the configured margins).
Arithmetic         one pure function: intrinsic size + bounds -> fitted size + floor flag.
Physical sizing    the render path inserts the picture with an explicit width AND height, so Word
                   does not re-derive the size.
Diagnostics        the render path emits RENDER005 when the fitted width is below the floor.
Verification       RenderedQA measures the delivered inline shapes against the text area.
Placement          unchanged and Word-owned: the existing keep-together property remains the
                   mechanism for "move to the next page".
```

## 2.3 Files / modules / functions

| Surface | Change |
| --- | --- |
| `md_converter/renderer/layout/figure_sizing.py` (new, pure) | `fit_figure_size(px_width, px_height, target_width_cm, max_width_cm, max_height_cm, min_width_cm) -> FigureFit` with fields `width_cm`, `height_cm`, `scaled`, `below_min_width`. No I/O, no Word objects. |
| `md_converter/renderer/style_resolver.py` | Add `figure_size_policy() -> dict` reading the theme `figure` block (token interpretation for `content_width` / `available_page_height`); make the existing `figure_style()` read `figure.alignment` / `keep_together` instead of hardcoding them. |
| `md_converter/renderer/word_writer.py` | Extract the existing raster-decoding step of `_add_image_from_data_uri` into one reusable helper; `add_image()` accepts the fitted bounds, measures the raster via `docx.image.Image` (already available through the pinned python-docx — no new dependency), applies `fit_figure_size`, inserts with explicit width and height, and returns a small result (size + floor flag). |
| `md_converter/renderer/word_renderer.py` | `visit_Image`: obtain the bounds from the resolver, call the writer, emit `RENDER005` when the floor flag is set. |
| `md_converter/renderer/layout/rendered_qa.py` | New `_check_figure_geometry(doc, result)`: measure every `inline_shape` against the section text area; `figure_overflow` (error) and `figure_below_min_width` (warning) become real metrics. |
| `md_converter/renderer/layout/section_manager.py` | Add `PageGeometry.portrait_content_height_cm` mirroring the existing width property, so the height bound has one authority. |
| `md_converter/constants/*` | unchanged |

## 2.4 Interface / data-model changes

```text
WordWriter.add_image: additional parameters for the fitted bounds and a return value describing
    the applied size. No other caller depends on the return value today.
StyleResolver: one new accessor.
AST: unchanged. LayoutPlan / BlockPlan: unchanged. RenderContext / CompilerContext: unchanged.
```

## 2.5 Configuration impact

None required. The bounds come from the frozen theme; `config.image_width` keeps its current
meaning as the target width. No new configuration key is introduced.

## 2.6 Implementation steps

```text
1. Add `fit_figure_size` + unit tests (pure arithmetic, no Word objects).
2. Add `PageGeometry.portrait_content_height_cm`.
3. Add `StyleResolver.figure_size_policy()`; make `figure_style()` theme-driven.
4. Extract the raster-decoding helper in `word_writer.py`; add measurement + fitted insertion.
5. Wire `visit_Image` and emit RENDER005.
6. Make `RenderedQA._check_figure_geometry` real.
7. Add the acceptance fixture and manifest entry; run targeted tests.
8. Run the affected acceptance cases, then the existing Golden, then full regression at the
   package closure point.
```

## 2.7 Test additions required

```text
md_converter/tests/test_figure_sizing.py        (new) pure fitting rule: normal fit, scale-down,
                                                aspect preservation, floor flag, no upscaling,
                                                rounding determinism
RenderedQA geometry test                        figure_overflow > 0 -> error/FAIL;
                                                figure_below_min_width counted as warning
RenderedQA regression                           metric keys keep their existing contract
acceptance fixture AC016_figure_fit.md + manifest entry
```

## 2.8 Existing tests potentially affected

```text
md_converter/tests/test_layout_plan.py（RenderedQA metric-key assertion — keys must remain）
md_converter/tests/test_renderer_v15.py（page margins / styles — margins unchanged）
md_converter/tests/test_page_geometry.py（A4 geometry — unchanged）
md_converter/tests/test_acceptance.py（AC007/AC008/AC009 figures — size-only changes）
```

## 2.9 Golden impact

```text
Predicted: NONE. The Golden comparison uses paragraphs, tables, inline-shape count, metadata and
diagnostics; no figure in the Golden sample needs clamping (its figures are wide and short), so no
size or diagnostic change is expected. Confirmation is required by running the existing Golden at
implementation time. Any legitimate delta goes through the approved baseline path — never an
automatic update.
```

## 2.10 Acceptance verification

Cases FIG-1..FIG-7 in §4.

## 2.11 Regression scope

Targeted figure tests → affected acceptance cases (figures/images and any geometry-sensitive case)
→ Golden → full regression at package closure.

## 2.12 Rollback boundary

```text
Revert the five touched files（figure_sizing.py, style_resolver.py, word_writer.py,
word_renderer.py, rendered_qa.py）; behaviour returns to fixed-width insertion. No data migration,
no persisted state, no configuration change to undo.
```

## 2.13 Explicit non-goals

```text
rotation or landscape sections for figures; splitting figures across pages; a minimum-height floor
for extremely wide figures; upscaling small images; DPI normalization; SVG -> DrawingML conversion;
diagram layout quality; changing any frozen theme value.
```

---

# 3. P12-CAND-001 — Whitespace-aligned / Simple-Table Recognition

## 3.1 Objective

Convert a conservatively recognised two-column whitespace-aligned block into a real table, without
changing the behaviour of any input that does not satisfy every recognition condition.

## 3.2 Proposed technical design

```text
Ownership        a new Pipeline recognition pass（AST → AST）. The Parser keeps its current
                 semantics for every input; no markdown-it rule is added.
Recognition      one pure function over reconstructed lines（Text segments split at SoftBreak）,
                 applying requirements R1..R7 of P12/P12_REQUIREMENTS.md §2.
Output           one Table node with 2 columns, header row = the line before the ruler, body rows
                 = the lines after it, cells = plain Text.
Emission         the document is rebuilt immutably; the matched Paragraph is replaced in place.
Ambiguity        ruler present but rules unsatisfied -> paragraph kept unchanged + INFO SIMPLE001.
Configuration    simple_tables.enabled（default true）gates registration of the pass.
Ordering         registered after NormalizePass so it sees normalised inline text; the diagram
                 passes operate on CodeBlock/Diagram nodes and cannot interact.
```

Rationale for a pass over a Parser rule: a markdown-it block rule changes tokenization for every
input (fence, indentation and lazy-continuation interactions), which is a wider and less reversible
surface; the pass reuses the existing `TransformPass` / `PassRegistry` extension point that
`AGENTS.md` defines for exactly this purpose, keeps the Parser contract intact, and is
deterministically testable in isolation.

## 3.3 Files / modules / functions

| Surface | Change |
| --- | --- |
| `md_converter/pipeline/passes/simple_table_pass.py` (new) | `SimpleTablePass(TransformPass)` with `run(document, diag) -> PassResult`; pure helpers `_recognize(lines) -> RecognizedBlock \| RejectReason` and `_lines_of(paragraph)`. |
| `md_converter/compiler.py` | Register the pass when `simple_tables.enabled` is true, using the existing registration call style. |
| `md_converter/config.py` | Add the `simple_tables` section（`enabled`）plus validation and inclusion in the resolved-config contract. |
| `pyproject.toml` | Optional entry-point declaration; not required because the compiler registers built-in passes directly. Decide during implementation; no packaging change is needed for the behaviour. |
| AST / Renderer / Layout | unchanged（the existing Table rendering path is reused, including first-row header repeat and column type inference） |

## 3.4 Interface / data-model changes

```text
No AST change: Table / TableRow / TableCell already exist.
No LayoutPlan / RenderContext change.
New configuration key only（simple_tables.enabled）.
```

## 3.5 Configuration impact

```text
simple_tables:
  enabled: true     # default; set false to disable recognition entirely
```

## 3.6 Implementation steps

```text
1. Implement `_recognize` as a pure function with unit tests derived from the measured corpus
   evidence（the ruler is decorative and need not align with the data columns — this is the
   behaviour the real evidence requires）.
2. Implement the pass and immutable document rebuild.
3. Register the pass behind the configuration flag.
4. Add the acceptance fixture and manifest entry.
5. Run targeted tests, the table-related acceptance cases, the existing Golden, then full
   regression at package closure.
```

## 3.7 Test additions required

```text
md_converter/tests/test_simple_table_pass.py   (new) positive conversion, every negative class,
                                               determinism, idempotence（a produced Table is never
                                               re-processed）, in-place replacement
acceptance fixture AC017_simple_table.md + manifest entry
```

## 3.8 Existing tests potentially affected

```text
md_converter/tests/test_parser.py（paragraph/table parsing — unchanged）
md_converter/tests/test_acceptance.py（AC004 / AC011 / AC012 / AC015 tables — must stay green）
md_converter/tests/test_config.py（resolved-config contract if a new key is added）
md_converter/tests/test_layout_plan.py（table layout path — unchanged）
```

## 3.9 Golden impact

```text
Predicted: NONE. Scanning of 85 documents (52 corpus, 15 acceptance fixtures, the Golden sample,
2 fixture files, 17 input_test documents）found exactly 2 blocks satisfying the rule, both in one
corpus document, and none in any tracked fixture. Confirmation is required by running the existing
Golden at implementation time.
```

## 3.10 Acceptance verification

Cases SIMPLE-1..SIMPLE-7 in §4.

## 3.11 Regression scope

Targeted pass tests → table-related acceptance cases → Golden → full regression at package closure.
Additionally, a bounded re-run of the Cycle-01 corpus as evidence (not as a canonical test) to
confirm the expected 2 conversions and 0 unexpected conversions.

## 3.12 Rollback boundary

```text
Set simple_tables.enabled: false（immediate, no code change）or revert the pass file plus the
registration and configuration hunks. Because the pass only replaces paragraphs that satisfy every
rule, disabling it restores the previous document structure exactly.
```

## 3.13 Explicit non-goals

```text
3+ column blocks; formatted/rich cells; multi-line cells; blocks inside lists or blockquotes;
separator-free blocks; automatic table styling beyond the existing table path; heuristics that
"best-effort" convert ambiguous text; changes to pipe/HTML table handling.
```

---

# 4. Acceptance and Regression Plan

Planning only — no test file is created or modified by S/N 118.

## 4.1 CAND-002 cases

| Case | Fixture | Expected |
| --- | --- | --- |
| FIG-1 normal figure | small wide image at target width | inserted unchanged; explicit width and height present |
| FIG-2 fits available area | image shorter than the text area | size unchanged; keep-together property present |
| FIG-3 requires next page | image that fits the text area but is tall | size unchanged; keep-together/keep-with-next on the figure paragraph (Word-side placement, not compiler-verified) |
| FIG-4 requires scaling | image taller than the text area | scaled to exactly the text-area height, aspect ratio preserved; `figure_overflow == 0` |
| FIG-5 extreme oversize | image equivalent to the measured 5.0 x 13.66 in case | fitted to the text area; no overflow; fitted width above the 8 cm floor in the realistic case |
| FIG-6 readability floor | synthetic very tall, very narrow image | fitted size still used; `RENDER005` warning emitted; `figure_below_min_width` counted |
| FIG-7 gate failure | document containing a figure that exceeds the text area (bypassing fitting) | `figure_overflow` error; gate FAIL under `fail_on_error` |

## 4.2 CAND-001 cases

| Case | Fixture | Expected |
| --- | --- | --- |
| SIMPLE-1 valid simple table | ruler + 2 columns | Table with 1 header row + body rows; no ruler row |
| SIMPLE-2 production-derived | minimal reduction of the corpus block (3-4 rows, ruler decorative or aligned) | converted; cell text preserved |
| SIMPLE-3 normal prose | multi-line paragraph | unchanged paragraph |
| SIMPLE-4 aligned prose | wrapped field list with shifting gaps | unchanged paragraph (no conversion, no diagnostic) |
| SIMPLE-5 fenced text | aligned block inside a code fence | CodeBlock unchanged |
| SIMPLE-6 ambiguous block | ruler present, inconsistent columns / empty cell | unchanged paragraph + `SIMPLE001` INFO |
| SIMPLE-7 existing pipe table | existing Markdown table | unchanged table (AC004 / AC012 unaffected) |

## 4.3 CAND-003 cases

| Case | Fixture | Expected |
| --- | --- | --- |
| HEAD-1 empty heading | `## ` | no rendered paragraph; no TOC entry |
| HEAD-2 normal heading | ordinary heading | unchanged |
| HEAD-3 TOC interaction | document with mixed headings | TOC entry count equals rendered heading count |
| HEAD-4 diagnostic | `## ` | `semantic_empty_heading` WARNING still reported |
| HEAD-5 adjacent headings | `## ` followed by `### Title` | only the non-empty heading rendered; numbering/TOC consistent |
| HEAD-6 multiple levels | empty heading at H1 among other levels | no section/page-break artefact; only real headings in the TOC |

## 4.4 Production corpus rule

```text
The 52-document Cycle-01 corpus stays evidence-only and untracked. Each acceptance fixture is a
minimal tracked reduction（e.g. 3-4 rows of the corpus alignment block), never a whole production
document. No canonical test may reference input_test/production_soak.
```

## 4.5 Layered regression

```text
candidate-specific targeted tests
    ↓ affected acceptance cases（tables for CAND-001, figures/images for CAND-002,
      headings/TOC for CAND-003）
    ↓ Golden — required for CAND-002 (image extents) and advisable for all three, since each can
      change delivered structure; predicted delta: none
    ↓ full regression at the integration/closure point of each package and at P12 closure
No redundant full-suite run per micro-change.
```

## 4.6 Golden policy

```text
No baseline update is proposed or authorized. Sequence at implementation time:
approved specification → implementation → observed legitimate output change → review the Golden
delta → authorized baseline update. "Golden failed" alone is never a reason to update it.
```

---

# 5. Cross-Candidate Consistency and Boundary Preservation

```text
AST contracts        001 emits existing Table nodes; 002 changes no node; 003 relies on the AST
                     keeping an empty Heading. No conflicting invariant.
Diagnostic registry  001 INFO SIMPLE001; 002 WARNING RENDER005 + two RenderedQA metrics;
                     003 no new code. No collision, no double-reporting of one condition.
Theme/configuration  002 reads the frozen figure policy; 001 adds simple_tables.enabled;
                     003 adds nothing. No frozen value changes.
Layout ownership     002 keeps the layout intent (keep_together) and adds no LayoutPlan field;
                     001 leaves Layout untouched; 003 removes a block from the delivered document
                     only.
Renderer ownership   002 and 003 both touch word_renderer.py but in disjoint methods
                     (visit_Image vs visit_Heading) — independent hunks, independently revertable.
Golden-visible        predicted none for all three; confirmation by running the Golden.
Acceptance            no shared fixture, no ordering dependency between the three case groups.
=> Implementation, verification and rollback boundaries stay independent. No merge is proposed.
```

---

# 6. Proposed Implementation Order

```text
PROPOSED: 002 → 001 → 003（unchanged from the initial assumption）
```

| Step | Package | Reason |
| --- | --- | --- |
| 1 | P12-CAND-002 figure page-fit | Settles delivered figure geometry and the QA measurement path first, so later packages are verified against a stable rendering baseline. It has the largest effect on delivered artifacts and touches shared render/QA surfaces. |
| 2 | P12-CAND-001 simple tables | Fully independent of 002. It carries the largest semantic risk (recognition), so it is scheduled after geometry is settled and receives the strictest negative-case verification. |
| 3 | P12-CAND-003 empty heading | Smallest surface and lowest risk; no dependency on the others, so it is last. |

```text
Alternative considered: 003 first as a low-risk canary. Rejected because no candidate depends on
another, so reordering would only delay the highest-value change without reducing risk elsewhere.
The order remains PROPOSED until Human implementation authorization.
```

---

# 7. Status

```text
REQUIREMENTS:                                  READY
CANONICAL SPECIFICATION PROPOSAL:              READY FOR HUMAN APPROVAL
ADR:                                           NOT REQUIRED（recorded, no document created）
IMPLEMENTATION PLAN:                           READY
ACCEPTANCE / REGRESSION PLAN:                  READY
PRODUCT SOURCE CODE:                           UNCHANGED
TEST CODE:                                     UNCHANGED
GOLDEN BASELINE:                               UNCHANGED
IMPLEMENTATION:                                NOT STARTED
NEXT HUMAN DECISION:                           APPROVE / REVISE P12 SPECIFICATION AND AUTHORIZE
                                               IMPLEMENTATION
```
