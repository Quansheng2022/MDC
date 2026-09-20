# P11 v1.0.1 Patch Release Candidate — Evidence

| Field | Value |
| --- | --- |
| Target Patch Version | **1.0.1** |
| Previous Release Tag | `v1.0.0` |
| RC_PAYLOAD_SOURCE_SHA (RC Source SHA) | `48efc925bfcee0695457168ebcd7c7a0c6d408b5` |
| Included MNT Packages | P11-MNT-006, P11-MNT-007, P11-MNT-008, P11-MNT-009 |
| Fixed ISSUEs | ISSUE-001, ISSUE-002, ISSUE-004, ISSUE-007, ISSUE-008 |
| Canonical Spec / Architecture / Theme | 1.0 (FROZEN) / 2.0 / QS-Word-Default-V1.5 — unchanged |
| Status | RELEASE_READY_FOR_HUMAN_APPROVAL |

## 1. Environment

```text
Python (canonical):            3.12.14 (.venv)
Canonical environment:         PASS — playwright installed, Chromium launchable,
                               backend = playwright, canonical = true
Word COM required path:        PASS — exercised by the canonical regression
                               (test_word_com_final_artifact, executed not skipped)
Known Limitations update:      NOT REQUIRED / unchanged (no statement became stale)
```

## 2. Release artifacts (built from RC Source SHA, outside the source tree)

```text
wheel:  md_converter-1.0.1-py3-none-any.whl
        size   318052 bytes
        SHA256 D535057AE09BD52B1BDE218633F1FC61497C5C4F98C8C20C8259E5C004861F25
sdist:  md_converter-1.0.1.tar.gz
        size   266885 bytes
        SHA256 116967BDE5550ED9964A1CF72D0FBF89F89292F8274E7E72F6C4557EAF09B71E

build exit = 0 (python -m build --no-isolation, outdir outside the repository)
wheel metadata: Name md_converter, Version 1.0.1, py.typed included, 121 members,
                console_scripts + passes + themes entry points present
sdist metadata: PKG-INFO Version 1.0.1
```

## 3. Fresh install (§12)

```text
dedicated venv outside the repository, non-editable install of the built wheel
pip exit = 0; resolved from PyPI: click 8.5.0, markdown-it-py 4.2.0, mdurl 0.1.2,
python-docx 1.2.0, lxml 6.1.3, pyyaml 6.0.3, typing_extensions 4.16.0
import OK; installed version = 1.0.1 (Python 3.12.14)
(pywin32 intentionally absent: the optional Word COM path is not part of the
 required runtime dependencies)
```

## 4. CLI smoke (§13)

```text
md-converter --help              exit 0, usage printed
md-converter-check               exit 0, "All required dependencies are available."
Markdown → DOCX conversion       exit 0, DOCX produced (44719 bytes), no traceback
CLI version output               NOT SUPPORTED (the frozen CLI has no --version option)
```

## 5. Representative patch verification (§14, §15)

```text
MNT-006  fresh install, service-like minimal env (PATH + UTF-8 only)
         exit 0 · DOCX produced (44721 bytes) · no traceback · POST002 present   PASS
MNT-007  QCFP_季度多维「筹码—资金—价格」联合分析框架.md (fresh install)
         3/3 external hyperlink targets preserved, link text present             PASS
MNT-008  MPC_Roadmap.md (fresh install)
         w:pgSz 11906 × 16838 (A4 portrait), left margin 1440 twips              PASS
MNT-009  QCFP-MTF_P1_使用手册.md
         fresh install (structural): 4 tables, 0 adjacent pairs, QA metric 0     PASS
         canonical env (real Word COM TOC refresh round trip):
             4 tables after Word save, 0 adjacent pairs,
             FinalArtifactQA = PASS, adjacent_tables metric = 0                  PASS

FinalArtifactQA:  PASS
COM gate:         PASS (executed, not skipped)

raw detail: representative_verification.json (this directory)
```

## 6. Canonical verification (§16)

```text
Command:  python -m pytest md_converter/tests -rs
          --junitxml=RC_EVIDENCE/P11_v1.0.1/canonical_full_regression.xml
Run from RC Source SHA (tracked diff clean during the run)

Collected:      308
Passed:         308
Failed:         0
Errors:         0
Required Skip:  0
Duration:       514.4 s

Acceptance:     PASS (35 acceptance cases, 0 failures)
Golden:         PASS (baseline NOT modified)
Word COM gate:  PASS

raw detail: canonical_full_regression_summary.json,
            canonical_full_regression.xml, canonical_full_regression.txt
```

## 7. Version consistency (§18)

```text
pyproject.toml [project].version                 1.0.1
md_converter.__version__ (source)                1.0.1
fresh installed md_converter.__version__         1.0.1
installed distribution metadata                  1.0.1
wheel METADATA Version                           1.0.1
sdist PKG-INFO Version                           1.0.1
RELEASE_MANIFEST_v1.0.1.json release             v1.0.1
RELEASE_NOTES_v1.0.1.md                          references v1.0.1
CLI version output                               not supported

mismatch = 0
(raw detail: version_and_git_consistency.json)
```

## 8. Git / source cleanliness (§20)

```text
HEAD                     = 48efc925bfcee0695457168ebcd7c7a0c6d408b5 (= RC Source SHA)
git diff --stat          = (clean)
tracked tree             = CLEAN
untracked (pre-existing) = Doc/MDC_Roadmap_0920.*, Doc/production_soak/, Test/,
                           input_test/mermaid_triangle/, input_test/production_soak/
untracked (this release) = RC_EVIDENCE/P11_v1.0.1/  (evidence only; not committed)
```

## 9. Scope statement

```text
Product behaviour changed during PLAN_C:   NO
Canonical Spec changed:                    NO
Architecture changed:                      NO
Golden baseline changed:                   NO
Acceptance source Markdown changed:        NO
Dependencies changed:                      NO
P12 work performed:                        NO
P11-MNT-010 created:                       NO

Release-preparation changes (RC commit 48efc92):
    pyproject.toml, md_converter/__init__.py            (version 1.0.1)
    RELEASE_MANIFEST_v1.0.1.json, RELEASE_NOTES_v1.0.1.md (patch manifest + notes)
    md_converter/tests/test_packaging_metadata.py,
    md_converter/tests/test_release_evidence.py         (version-literal assertions
                                                         in metadata-consistency tests
                                                         only — no behaviour assertion
                                                         relaxed or removed)
```

## 10. Release decision

```text
RELEASE_READY_FOR_HUMAN_APPROVAL

Release tag:  NOT CREATED
Publication:  NOT PERFORMED
P11:          FROZEN / ACTIVE
P11-MNT-010:  NOT CREATED / FREE / UNASSIGNED
Next action:  HUMAN PRODUCTION APPROVAL REQUIRED
```
