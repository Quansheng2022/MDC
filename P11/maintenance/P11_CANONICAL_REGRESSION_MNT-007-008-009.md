# Shared Canonical Regression Record — P11-MNT-007 / MNT-008 / MNT-009

| Field | Value |
| --- | --- |
| Plan | Master Instruction — P11 Cycle-01 Priority Defect Repair Batch |
| Work Packages | P11-MNT-007, P11-MNT-008, P11-MNT-009 (one shared canonical gate) |
| Authority | `CANONICAL_SPEC.md` 1.0 FROZEN, `GOLDEN_ENVIRONMENT.md`, `P11_GIT_CLOSURE_GATE.md` |
| Environment | Canonical Windows environment (non-sandbox process context: Chromium launchable, Word COM live) |
| Status | PASS — referenced by all three closure records |

## 1. Commit chain

```text
Starting canonical HEAD:          2e9d42b21154f4733ac8701e59e93d86c7a20ca2
MNT-007 implementation SHA:       aae73de99734bb8598442b6f88d84438808e4f0d
MNT-008 implementation SHA:       91bc0092ed4965e657e08cabe7ae4ab88ee88aeb
MNT-009 implementation SHA:       e7ee94308ed6fb3263bc73a03fde2e5ebe1c3139
```

Each package was verified by its own targeted tests before the next package started;
no intermediate full regression was executed (authorized by the Master Instruction §11).

## 2. Canonical gates

```text
Canonical environment recheck:    PASS
    pytest md_converter/tests/test_golden_environment.py -q
    playwright_installed=true, chromium_launchable=true, backend=playwright, canonical=true

Aggregate targeted tests:         PASS — 48 tests, 0 failed, 0 errors, 0 skipped (462.9 s)
    test_golden_environment.py, test_hyperlink_targets.py, test_acceptance.py,
    test_page_geometry.py, test_adjacent_tables.py, test_word_com_final_artifact.py,
    test_golden.py

Bounded real-document verification (canonical, Word COM live):  PASS
    hyperlink : QCFP_季度多维「筹码—资金—价格」联合分析框架.md
                MD targets = DOCX external targets (3/3), preserved = true
    tables    : QCFP-MTF_P1/P3/P4/P5/P6_使用手册.md
                md_tables == docx_tables (4/4, 4/4, 5/5, 5/5, 7/7),
                adjacent table pairs = 0, FinalArtifactQA = PASS (adjacent_tables = 0)
    page size : MPC_Roadmap.md → w:pgSz = 11906 × 16838 twips (A4 portrait)
    (full JSON: %TEMP%\mnt_shared\bounded_real_document_verification.json)

Acceptance:                       PASS — 35 tests, 0 failed, 0 errors, 0 skipped

Golden:                           PASS (test_golden.py) — baseline NOT modified

Full canonical regression:        PASS — pytest md_converter/tests -rs (519.0 s)
    Collected:  308
    Passed:     308
    Failed:     0
    Errors:     0
    Required Skip: 0
```

## 3. Scope

```text
Product/test files changed (all mapped to MNT-007/008/009):
    md_converter/renderer/word_renderer.py             (MNT-007, MNT-008)
    md_converter/renderer/word_writer.py               (MNT-007, MNT-009)
    md_converter/renderer/layout/final_artifact_qa.py  (MNT-009)
    md_converter/tests/test_acceptance.py              (MNT-007)
    md_converter/tests/test_hyperlink_targets.py       (MNT-007, new)
    md_converter/tests/test_page_geometry.py           (MNT-008, new)
    md_converter/tests/test_adjacent_tables.py         (MNT-009, new)

Canonical Spec / Architecture / Golden baseline / Acceptance source Markdown /
theme YAML / dependencies / packaging: unchanged.
P12 work: none.  Other Cycle-01 issues (003/005/006/008/009/010, OBS-01..04): untouched.
```
