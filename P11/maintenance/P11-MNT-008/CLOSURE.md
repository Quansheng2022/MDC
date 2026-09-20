# P11-MNT-008 Closure Record

| Field | Value |
| --- | --- |
| Work Package | P11-MNT-008 |
| Title | Apply Frozen A4 Page Size to Portrait Documents |
| Issue Source | ISSUE-007 (DEFECT / P2) — Production Usage Validation Cycle 01 |
| Authority | `CANONICAL_SPEC.md` SPEC-FUNC-012; frozen theme `page.size = A4`; `config.page_width = A4` |
| Status | CLOSED / ACCEPTED |

## 1. Root cause

Portrait document initialisation applied page *margins* only
(`WordRenderer._apply_page_margins`). Page size was written exclusively by
`word_writer.set_section_orientation()`, which `visit_Table` reaches only for
`plan.landscape` tables. With no landscape table in a document, the python-docx
template default (US Letter, 12240 × 15840 twips) survived — 52/52 Cycle-01 artifacts.

## 2. Implementation

```text
md_converter/renderer/word_renderer.py  _apply_page_size(): reads the frozen authority
                                       (theme page.size, fallback config page_width) and
                                       applies it through the existing single A4 geometry
                                       definition (word_writer.set_section_orientation);
                                       called once from visit_Document before margins
md_converter/tests/test_page_geometry.py  UT-PAGE-001, representative document geometry,
                                       landscape regression check (new)
```

Margins, theme values, landscape switching and the DecisionEngine are unchanged; no second
page-size authority was introduced.

## 3. Targeted verification

```text
UT-PAGE-001                        minimal document → w:pgSz 11906 × 16838 (A4 portrait),
                                   margins unchanged (1440 twips)                           PASS
Representative DOCX geometry       AC011_long_document.md → A4 portrait, no landscape       PASS
Landscape regression check         15-column table → A4 landscape 16838 × 11906, other
                                   sections remain A4 portrait                              PASS
Real corpus document               MPC_Roadmap.md → w:pgSz 11906 × 16838, margins 1440      PASS
Page/layout regression suite       test_page_geometry + test_layout_plan + test_renderer_v15
                                   (27 tests)                                               PASS
```

## 4. Shared canonical regression

See `P11/maintenance/P11_CANONICAL_REGRESSION_MNT-007-008-009.md` (308/308, 0 failed,
0 errors, 0 required skip; Golden baseline unchanged).
Implementation SHA: `91bc0092ed4965e657e08cabe7ae4ab88ee88aeb`.

## 5. Result

```text
P11-MNT-008: CLOSED / ACCEPTED
Patch Release: NOT AUTHORIZED (unchanged by this package)
Next Action: HUMAN REVIEW ONLY
```
