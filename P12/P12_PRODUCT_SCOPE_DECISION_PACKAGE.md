# P12 Product Scope Decision Package — S/N 117

## Artifact Header

| Field | Value |
| --- | --- |
| Program | MD_Converter |
| Lifecycle | P12 Product Evolution |
| Roadmap task | S/N 117 — Candidate Consolidation & Product Scope Selection |
| Baseline | branch `master` @ `bc70fd69137ccaf045a0790bfdf1a69470ea0253` |
| Authority | P12 Intake instruction (Human, 2026-09-21); `CANONICAL_SPEC.md` 1.0 FROZEN; `P11/P11_P12_BOUNDARY.md`; `P11/P11_MAINTENANCE_REGISTRY.md` §3 |
| Status | Recommendation complete. Human Product Scope Selection REQUIRED. |
| Product code modification | NOT AUTHORIZED |
| Companion documents | `P12/P12_CANDIDATE_REGISTRY.md`; `P12/P12_INTAKE_ANALYSIS.md` |

Outcome of the Human scope gate (recorded 2026-09-21, S/N 118 master instruction):

```text
P12 S/N 117: COMPLETE / ACCEPTED
P12-CAND-001 / 002 / 003: SELECTED FOR SPECIFICATION
S/N 118: AUTHORIZED TO START（specification and planning only）
Recommended scope in §E was adopted in full (all three candidates);
recommended order 002 → 001 → 003 remains the initial assumption and is
reassessed in P12/P12_IMPLEMENTATION_PLAN.md §6.
```

This package is self-sufficient for the scope decision. It references evidence instead of
duplicating it.

---

# A. Current P12 Lifecycle Status

```text
P0–P10:  CLOSED / COMPLETE
P11:     CLOSED / ACCEPTED（Human Final Closure 2026-09-21）
P12:     INTAKE AUTHORIZED — product-code modification NOT AUTHORIZED
S/N 117: this intake (candidate consolidation + product scope selection)
S/N 118: authorized ONLY if an explicit Human-selected scope is supplied
         (requirements / Canonical Specification proposal / ADR where genuinely needed /
          implementation planning — still no product code)

Working tree at intake start:
    untracked Human work present and untouched:
        Doc/MDC_Roadmap_0920.md, Doc/MDC_Roadmap_0920.docx, Doc/production_soak/,
        Test/, input_test/production_soak/, input_test/mermaid_triangle/
    no tracked file was modified by this intake before the bounded documentation commit

No P0–P11 record was reopened, reinterpreted or altered.
No release review, rebuild or re-verification was performed.
```

---

# B. Candidate Register

| Candidate ID | Title | Source lineage | Source classification | Recommended disposition |
| --- | --- | --- | --- | --- |
| P12-CAND-001 | Whitespace-aligned / simple-table recognition | OBS-04 (Cycle-01) | P12_CANDIDATE / Enhancement | SELECT (RECOMMENDED) |
| P12-CAND-002 | Figure Page-Fit / Figure Size Policy | ISSUE-003 → Human SPEC_GAP ruling 2026-09-21 | SPEC_GAP → P12_CANDIDATE | SELECT (RECOMMENDED) |
| P12-CAND-003 | Empty Heading Behaviour Policy | ISSUE-009 → Human SPEC_GAP ruling 2026-09-21 | SPEC_GAP → P12_CANDIDATE | SELECT (RECOMMENDED) |

Identifier note: the earlier *suggested* pool in `Doc/MDC_Roadmap_0920.md` used
`P12-CAND-002..005` for different subjects; Cycle-01 classification did not adopt that pool,
and this intake assigns 002/003 to the two SPEC_GAP-derived candidates. The suggested-pool
subjects are not registered (see §F). The Human roadmap document was not modified.

---

# C. Candidate-by-Candidate Findings

## P12-CAND-001 — Whitespace-aligned / simple-table recognition

| Question | Finding |
| --- | --- |
| What is the problem | Two-column data written with whitespace alignment has no construct, so it becomes prose and cannot be structured as a table. |
| Why it matters | Recurring authoring pattern; real corpus evidence (3 blocks outside fences in 2 documents; a verified 8-row example with a dashed separator row). |
| Current behaviour | One `Paragraph` with `Text` + `SoftBreak` nodes; columns align only visually under a proportional font. |
| Decision required | Whether to convert, under which recognition rule, and what to do when recognition is ambiguous. |
| Affected subsystem | Parser or Pipeline (recognition + AST construction). Renderer unchanged. |
| How verification would work | Recognition unit tests (positive/negative), a new acceptance case, regression that aligned prose and ordered-list items are not converted, corpus re-audit for 0 unexpected tables. |

## P12-CAND-002 — Figure Page-Fit / Figure Size Policy

| Question | Finding |
| --- | --- |
| What is the problem | No figure size policy: images are always 5.0 in wide with no height cap, so figures exceed the page and Word cannot lay them out. |
| Why it matters | 6 of 52 documents contain a figure taller than the text area; 3 are taller than the page. This is the difference between a deliverable usable as-is and one needing manual correction (SPEC-GOAL-001). |
| Current behaviour | Fixed width only; the frozen theme's `figure` block (`max_height: available_page_height`, `overflow_handling`) is unreachable — no theme accessor; `RenderedQA` seeds `figure_overflow` but never measures it, although the theme lists `broken_figure` as a gate error. |
| Decision required | Which overflow response is authoritative (scale to fit / move to next page / split / warn), the minimum acceptable size, and whether an unfittable figure is a warning or a FAIL. |
| Affected subsystem | Layout (`DecisionEngine`/`LayoutPlan`) + Renderer image insertion + `RenderedQA` + read-only theme consumption. |
| How verification would work | Clamp/scale/move unit test, a real `figure_overflow` QA assertion, geometry re-measurement on the Cycle-01 figure documents, and a Golden/acceptance integrity check. |

## P12-CAND-003 — Empty Heading Behaviour Policy

| Question | Finding |
| --- | --- |
| What is the problem | An empty heading has no defined behaviour; the renderer injects the literal word `Heading`, which also becomes a TOC entry. |
| Why it matters | The delivered document contains content the author never wrote; visible in body and TOC. |
| Current behaviour | Empty `Heading` node exists in the AST; `StaticQA` emits warning `semantic_empty_heading`; `visit_Heading` substitutes `"Heading"`; the TOC collector includes it. |
| Decision required | Drop / keep empty / treat as error; diagnostic severity; TOC and numbering consequence. |
| Affected subsystem | Renderer (and Parser/Pipeline if "drop" is chosen) + StaticQA severity + TOC consistency. |
| How verification would work | Unit test: no placeholder text and a consistent TOC; severity assertion; acceptance/Golden integrity check. |

---

# D. Cross-Candidate Interaction

| Pair | Relationship | Consequence |
| --- | --- | --- |
| 001 ↔ 002 | Independent | Different stages and acceptance scenarios; no shared interface or schema change. |
| 001 ↔ 003 | Independent | Disjoint constructs; no shared code path. |
| 002 ↔ 003 | Independent | Only common property is "may add a diagnostic"; not a coupling. |

```text
MERGE not recommended for any pair: distinct change and rollback boundaries.
Sequencing is recommended instead of merging.
All three candidates require Golden/acceptance integrity review at implementation time,
because each can change delivered structure or diagnostics.
```

---

# E. Recommended P12 Scope

```text
Recommended: select all three candidates, executed as three independently gated bounded
packages in this order. Each package runs the full S/N 118 chain before any code is written.
```

| Order | Package | Candidate | Why this order | Bounded change surface | ADR expectation |
| --- | --- | --- | --- | --- | --- |
| 1 | P12-PKG-002 | Figure page-fit / size policy | Highest delivery impact; makes already-declared theme behaviour real; verification is measurable geometry | Layout + Renderer + RenderedQA | Possible — only if LayoutPlan must carry the size constraint; otherwise not required |
| 2 | P12-PKG-001 | Whitespace-aligned / simple tables | Real corpus demand for a new capability, but the largest regression surface → benefits from strictest review | Parser or Pipeline + tests | Possible — only if Pipeline-pass vs Parser-rule is judged a genuine architecture decision |
| 3 | P12-PKG-003 | Empty heading behaviour policy | Smallest and most self-contained; one normative decision plus a small bounded change | Renderer (+ Parser/Pipeline if "drop") + QA severity | Not required either way |

Per-selected-candidate S/N 118 deliverables (not produced in this intake):

```text
requirements (problem / expectation / current / required / in scope / out of scope /
              compatibility / failure behaviour / acceptance examples)
Canonical Specification proposal   labeled "P12 PROPOSAL — NOT YET CANONICAL"
ADR   only if a genuine architecture choice exists; otherwise "ADR NOT REQUIRED"
implementation plan (modules, files, interfaces, sequence, tests, Golden impact,
                     regression scope, rollback, explicit non-goals)
then: NEXT GATE = HUMAN IMPLEMENTATION AUTHORIZATION
```

Minimum P12 option, if the Human prefers the smallest scope:

```text
Select P12-PKG-002 only. Candidates 001 and 003 stay registered and DISCOVERY-ONLY,
unsequenced, with no implementation authority. Sequence can be extended later by a
separate Human instruction.
```

This intake does not select anything. The Human decides the scope.

---

# F. Deferred and Not-Registered Candidates

```text
Not registered by this intake (no independent evidence, or previously dispositioned):
    Complex table handling            no merged/rowspan Markdown source in the corpus;
                                      ISSUE-004 gridSpan was a Word COM artefact (already repaired)
    Long-document robustness          no Cycle-01 failure: largest documents converted, 0 content loss
    Image handling refinement         no evidence beyond CAND-002's size policy
    CN/EN typography refinement       no independent evidence
    Mermaid triangle layout           previously dispositioned as content/authoring, not P12
    PDF/HTML backend, footnotes,
    cross references, incremental
    or multi-threaded compilation     explicit non-goals of the current scope

Deferred within this intake: none (no candidate was dismissed).
```

---

# G. Known Uncertainties

```text
Resolution of these belongs to the Human scope decision or to S/N 118 — not to this intake.

1. CAND-001 recognition rule: minimum rows/columns; whether a dashed separator row is
   required; whether blocks inside lists or blockquotes are eligible; default-on vs opt-in;
   how to keep ordered-list items such as `1.  **Authority-first**` out of detection.
2. CAND-001 ownership: Pipeline pass vs Parser rule, and whether that is an architectural
   decision requiring an ADR.
3. CAND-002 authoritative overflow response when the declared responses conflict
   (scale_down vs move_to_next_page), and the interaction with SPEC-INV-002 minimums when a
   figure cannot satisfy both the cap and the floor.
4. CAND-002 carrier: whether the size constraint extends LayoutPlan (schema evolution,
   possible ADR) or reuses an existing carrier.
5. CAND-002 width overflow: whether a figure wider than the text area is in scope together
   with height overflow.
6. CAND-003 policy choice and its TOC/numbering consequences; whether the existing
   diagnostic stays a warning or becomes an error.
7. Golden baseline impact: the Golden expectation includes the full diagnostics list, so any
   new diagnostic is Golden-visible and must follow the approved baseline-update path
   (SPEC-INV-011). Whether the Golden sample actually triggers such a diagnostic must be
   confirmed during implementation, not assumed here.
8. Cycle-01 corpus availability: input_test/production_soak/cycle_01 (52 documents) is
   present but UNTRACKED, so it can support analysis but cannot be the canonical regression
   gate; a tracked acceptance/Golden case is required for verification.
```

---

# H. Proposed Next Action

```text
1. Human Product Scope Selection:
       select the P12 execution scope from {P12-CAND-001, P12-CAND-002, P12-CAND-003}
       (recommended: all three, sequenced 002 → 001 → 003; minimum option: 002 only)
2. If a scope is selected, S/N 118 may proceed for the selected candidates:
       requirements → Canonical Specification proposal → ADR if genuinely required →
       implementation plan → acceptance / regression / rollback planning
3. Product code modification remains NOT AUTHORIZED.
   A separate Human Implementation Authorization is the next gate after S/N 118.
4. If the Human wants to change the candidate set, that is a new instruction; this intake
   does not add or remove candidates on its own.
```

---

# Required Status

```text
P12 S/N 117 TECHNICAL INTAKE:
COMPLETE

CANDIDATE CONSOLIDATION:
COMPLETE

AGENT SCOPE RECOMMENDATION:
READY

HUMAN PRODUCT SCOPE SELECTION:
REQUIRED

PRODUCT CODE MODIFICATION:
NOT AUTHORIZED

IMPLEMENTATION:
NOT STARTED
```
