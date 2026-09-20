# P11-MNT-007 Closure Record

| Field | Value |
| --- | --- |
| Work Package | P11-MNT-007 |
| Title | Preserve Hyperlink Targets and Enforce AC010 |
| Issue Source | ISSUE-001 (DEFECT / P2) + ISSUE-002 (TEST_DEFECT / P3) — Production Usage Validation Cycle 01 |
| Authority | `CANONICAL_SPEC.md` SPEC-FUNC-008, SPEC-INV-001; AC010 requirement text |
| Status | CLOSED / ACCEPTED |

## 1. Root cause

`WordRenderer._render_link` pushed colour/underline into `InlineState` and rendered the
link children as ordinary runs. No `w:hyperlink` element and no hyperlink relationship
were ever created, so the URL of every Markdown link was unrecoverable from the DOCX
(`word/_rels/document.xml.rels` contained 0 external targets across the whole Cycle-01
corpus). AC010 states that link text **and** target must be preserved, but the
acceptance signature did not assert targets, so the defect passed the gate.

## 2. Implementation

```text
md_converter/renderer/word_writer.py   wrap_runs_as_hyperlink(): wraps the runs created for
                                       a link into w:hyperlink; uses w:anchor for "#..."
                                       targets and an external relationship
                                       (TargetMode="External") otherwise
md_converter/renderer/word_renderer.py _render_link(): renders children as before, then
                                       wraps the new runs; styling/visible text unchanged
md_converter/tests/test_hyperlink_targets.py  UT-RENDER-LINK-001/002, IT-LINK-001 (new)
md_converter/tests/test_acceptance.py  signature now carries hyperlink_targets;
                                       AC010 positive assertion + negative proof test
```

Degenerate empty targets keep the text and create no relationship (UT-RENDER-LINK-002).

## 3. Targeted verification

```text
UT-RENDER-LINK-001  Link → w:hyperlink + external relationship + blue/underline styling   PASS
IT-LINK-001         http / https / mailto / relative / anchor targets all recoverable      PASS
UT-RENDER-LINK-002  empty target → text kept, no relationship                              PASS
AC010 (positive)    https://openai.com, https://example.com/architecture,
                    mailto:support@example.com all present in the artifact                  PASS
AC010 (negative)    with the pre-patch _render_link behaviour the AC010 assertion fails    PASS
Acceptance suite    35 tests, 0 failed, 0 skipped                                          PASS
Real document       QCFP_季度多维「筹码—资金—价格」联合分析框架.md → 3/3 targets preserved  PASS
```

## 4. Shared canonical regression

See `P11/maintenance/P11_CANONICAL_REGRESSION_MNT-007-008-009.md` (308/308, 0 failed,
0 errors, 0 required skip). Implementation SHA: `aae73de99734bb8598442b6f88d84438808e4f0d`.

## 5. Result

```text
P11-MNT-007: CLOSED / ACCEPTED
Patch Release: NOT AUTHORIZED (unchanged by this package)
Next Action: HUMAN REVIEW ONLY
```
