# P11-MNT-009 Closure Record

| Field | Value |
| --- | --- |
| Work Package | P11-MNT-009 |
| Title | Preserve Adjacent Markdown Tables Across Word COM |
| Issue Source | ISSUE-004 (DEFECT / P2) — Production Usage Validation Cycle 01 |
| Authority | `CANONICAL_SPEC.md` SPEC-INV-001, SPEC-ARCH-005, SPEC-QA-002 |
| Status | CLOSED / ACCEPTED |

## 1. Root cause

Two Markdown tables separated by a blank line produce two independent `Table` AST nodes
with no `Paragraph` between them, so the renderer emitted two **immediately adjacent**
`w:tbl` elements (minimal reproduction: body sequence `["p","tbl","tbl","sectPr"]`).
Word merges directly adjacent tables on open/save; because the production path always
performs a Word COM TOC refresh, five Cycle-01 artifacts lost the table boundary
(table count 4 → 3, second header row no longer repeating, `gridSpan` re-grid).

## 2. Implementation

```text
md_converter/renderer/word_writer.py              ensure_table_separator(): called from
                                                 start_table(); inserts one empty paragraph
                                                 when the last body content element before
                                                 sectPr is a w:tbl
md_converter/renderer/layout/final_artifact_qa.py _check_adjacent_tables(): metric
                                                 adjacent_tables + non-silent table_adjacent
                                                 warning on the published artifact
md_converter/tests/test_adjacent_tables.py       UT-TABLE-ADJ-001/002, QA negative proof,
                                                 IT-WORDCOM-001 (new)
```

No table rendering redesign: the separator (an ordinary empty paragraph, mirroring the
source's blank line) is the minimal Word-stable form.

## 3. Targeted verification

```text
UT-TABLE-ADJ-001        two adjacent source tables → two w:tbl with a separating w:p,
                        FinalArtifactQA adjacent_tables = 0                                 PASS
UT-TABLE-ADJ-002        paragraph-separated tables unchanged (no extra paragraph)            PASS
QA negative proof       separator disabled → adjacent_tables = 1 and table_adjacent warning
                        raised (quality gate is not silent)                                  PASS
IT-WORDCOM-001          real production path (Word COM TOC refresh) keeps 2 tables,
                        0 adjacent pairs — executed, not skipped                             PASS
Affected corpus (5)     QCFP-MTF_P1/P3/P4/P5/P6_使用手册.md after the real Word COM path:
                        md_tables == docx_tables (4/4, 4/4, 5/5, 5/5, 7/7), adjacent = 0,
                        FinalArtifactQA = PASS                                               PASS
QA/post-processor suite test_quality_gate + test_post_processor (33 tests)                   PASS
```

## 4. Shared canonical regression

See `P11/maintenance/P11_CANONICAL_REGRESSION_MNT-007-008-009.md` (308/308, 0 failed,
0 errors, 0 required skip).
Implementation SHA: `e7ee94308ed6fb3263bc73a03fde2e5ebe1c3139`.

## 5. Result

```text
P11-MNT-009: CLOSED / ACCEPTED
Patch Release: NOT AUTHORIZED (unchanged by this package)
Next Action: HUMAN REVIEW ONLY
```
