# P12 Canonical Specification Proposal

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
| Work item | S/N 118 |
| Base authority | `CANONICAL_SPEC.md` v1.0 (FROZEN) — unchanged by this document |
| Baseline | branch `master` @ `8ff7aef5ce43a169737bf331e46f7b5db0cdf212` |
| Status | PROPOSAL — requires Human approval before it has any authority |
| Requirements basis | `P12/P12_REQUIREMENTS.md` |
| Execution basis | `P12/P12_IMPLEMENTATION_PLAN.md` |

## How this proposal enters the specification

`CANONICAL_SPEC.md` is FROZEN at 1.0. Per `AGENTS.md` §Governance Rules and the specification
lifecycle, this proposal cannot be applied by a patch. If the Human approves it, the authorised
sequence is:

```text
Human approval of this proposal
    ↓
Canonical Specification update（append the approved items below）
    ↓
SPEC_CHANGELOG.md entry（records source = P12 S/N 118 approval）
    ↓
Re-freeze the specification with a new version identity
```

Only the deltas below are proposed. Nothing else in Canonical 1.0 is restated or reworded.
Proposed identifiers continue the existing families (`SPEC-FUNC-*`, `SPEC-INV-*`, `SPEC-QA-*`);
no new identifier framework is introduced.

---

# 1. Proposed Functional Items

## SPEC-FUNC-022 (proposed) — Simple-table recognition

```text
The compiler SHALL recognise a whitespace-aligned two-column block as a table when, and only
when, the block satisfies all of the following:

  (a) it is a top-level paragraph of the document;
  (b) it has at least three lines;
  (c) its second line is a ruler line consisting only of spaces and at least two runs of at
      least three hyphens, the runs being separated by at least one space;
  (d) every other line contains exactly one run of two or more spaces, contains no tab, and
      yields two non-empty cells when split at that run;
  (e) the multi-space runs of all those lines share a common column boundary, defined as the
      largest run start that is smaller than every run end;
  (f) no line contains "|";
  (g) the paragraph consists only of plain text and line breaks.

When the conditions hold, the compiler SHALL produce a two-column Table node whose first row is
the line preceding the ruler line and whose remaining rows are the lines following it. The
ruler line SHALL NOT produce a row. Cell content SHALL be the stripped cell text.

When the ruler line of (c) is present but any other condition fails, the block SHALL remain
ordinary paragraph content and SHALL NOT produce a diagnostic (CLAR-01: failed recognition is not
an error or warning condition, and the compiler SHALL NOT emit diagnostic noise to expose internal
recognition decisions).

Recognition SHALL NOT depend on any external corpus, file path, or author identity, and SHALL be
deterministic for identical input.
```

Related existing items: `SPEC-FUNC-004` (Markdown tables), `SPEC-FUNC-014` (AsciiToMermaidPass),
`SPEC-GOAL-003` / `SPEC-INV-003` (determinism).

## SPEC-FUNC-023 (proposed) — Figure page-fit and size policy

```text
The compiler SHALL size every figure so that the delivered figure fits inside the effective
section content box of the section being rendered, where

    effective content width  = section width  - left margin - right margin
    effective content height = section height - top margin  - bottom margin
    target width             = min(configured image width, effective content width)

The effective content box SHALL be derived from the actual section geometry (CLAR-02). The frozen
A4 / 1-inch-margin geometry (approximately 15.92 cm x 24.62 cm) is the current baseline reference;
it SHALL NOT become a universal constant while the architecture provides section geometry.

The compiler SHALL determine a figure's intrinsic size from the image itself and SHALL preserve
its aspect ratio.

The compiler SHALL apply the following behaviour in the declared order of theme
figure.overflow_handling:

  (a) move_to_next_page: a figure whose height at target width fits the available text height
      SHALL be inserted at target width and natural aspect ratio; it SHALL retain the existing
      keep-together placement property so that page placement is performed by Word when the
      remaining space on the current page is insufficient. The compiler does not measure
      remaining page space.
  (b) scale_down: a figure whose height at target width exceeds the available text height SHALL
      be scaled down, preserving aspect ratio, to exactly the available text height.
  (c) warn: a figure whose fitted width is smaller than theme figure.min_width SHALL be delivered
      at the fitted size and SHALL produce a structured WARNING diagnostic.

A figure SHALL NOT be inserted with a size exceeding either content-box bound, and SHALL NOT be
upscaled beyond target width. When a figure cannot be read at all, the existing documented
fallback behaviour is unchanged.

The converter owns figure sizing, aspect-ratio preservation, width/height bounds, never-upscale
behaviour, the minimum-width diagnostic, overflow measurement, and the placement semantics exposed
to Word. Final physical pagination remains Word-owned: the compiler does not promise an exact
physical page number or deterministic final Word pagination.
```

Related existing items: `SPEC-GOAL-001` (directly deliverable DOCX), `SPEC-INV-002`
(readability minimums — the figure *maximum* was previously unspecified), `SPEC-ARCH-010`
(layout decisions belong to the DecisionEngine; the declared theme bound is applied at the render
boundary as formatting), `SPEC-FUNC-013` (DiagramPass) and `SPEC-FUNC-008` (images).

Proposed specification note (interpretation, not new behaviour): the theme tokens
`content_width` and `available_page_height` denote the text area derived from the page size and
margins — see `SPEC-FUNC-023` above. No frozen theme value changes.

## SPEC-FUNC-024 (proposed) — Empty heading behaviour

```text
A heading whose plain text is empty after stripping SHALL NOT be rendered. The heading SHALL
remain present in the AST, and the existing StaticQA warning for an empty heading SHALL continue
to be reported with WARNING severity. The compiler SHALL NOT substitute placeholder text for an
empty heading, and SHALL NOT include an empty heading in the table of contents or in heading
numbering.
```

Related existing items: `SPEC-FUNC-001` (headings 1–6), `SPEC-GOAL-004` and `SPEC-INV-001`
(no silent semantic loss — there is no semantic content to lose, and the condition is reported),
`SPEC-INV-006` (recoverable problems produce a Diagnostic), `SPEC-FUNC-016` (diagnostics).

---

# 2. Proposed Invariant Items

## SPEC-INV-013 (proposed) — Conservative simple-table recognition

```text
Ambiguous whitespace-aligned input SHALL remain paragraph content. Simple-table recognition SHALL
never convert input that does not satisfy every recognition condition, and SHALL never drop,
reorder, or reword source text as part of a conversion decision.
```

## SPEC-INV-014 (proposed) — Delivered figures fit the page

```text
No delivered figure SHALL exceed the available text area of its page. A build in which a delivered
figure exceeds that area SHALL NOT pass the quality gates.
```

---

# 3. Proposed Quality-Gate Item

## SPEC-QA-005 (proposed) — Figure geometry verification

```text
RenderedQA SHALL measure the delivered extent of every figure against the available text area and
SHALL report the result as a real metric rather than a placeholder value.

  - a figure exceeding either text-area bound SHALL be an error, and SHALL fail the gate under the
    existing fail_on_error policy;
  - a figure delivered below the declared minimum figure width SHALL be counted and reported as a
    warning;
  - the measurements SHALL be deterministic and derived from the produced document, not from
    renderer state.

This makes the existing theme gate categories (layout_qa.quality_gate.error: overflow, clipping,
broken_figure) measurable for figures.
```

Related existing items: `SPEC-QA-002` / `SPEC-INV-008` (RenderedQA FAIL cannot silently enter a
Release Candidate), `SPEC-INV-002`, `SPEC-FUNC-017`.

---

# 4. Items Deliberately Not Proposed

```text
No new goal, non-goal, acceptance-family, or architecture item is proposed: none of the three
candidates changes an architecture boundary or the acceptance framework.

No general "never synthesize text" invariant is proposed: existing documented degradation paths
(image and diagram fallback text, empty-TOC placeholder) intentionally synthesize text and are
governed elsewhere; adding the invariant would contradict accepted behaviour.

No change to SPEC-FUNC-001..021, SPEC-ARCH-001..013, SPEC-GOAL-001..006, SPEC-INV-001..012,
SPEC-QA-001..004, SPEC-AC-001..005 or SPEC-NON-001..004 is proposed.

No change to any frozen theme value is proposed.
```

---

# 5. Approval Record

```text
Current state:            PROPOSED — NOT CANONICAL
Human approval:           NOT GIVEN
Implementation authority: NOT GIVEN
Specification version:    unchanged（Canonical 1.0 FROZEN）
Approval entry point:     Human review of this file plus P12/P12_REQUIREMENTS.md and
                          P12/P12_IMPLEMENTATION_PLAN.md
```
