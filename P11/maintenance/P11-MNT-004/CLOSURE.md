# P11 Maintenance Package Closure — P11-MNT-004

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_B — Maintenance Change Package Execution |
| Work Package | P11-MNT-004 |
| Authority | `P11_CLOSURE_TEMPLATE.md` / `Doc/Phase_11_Maintenance_Specification.md` v1.0（§16 / §17） |
| Date | 2026-09-19 |
| Status | **CLOSED / ACCEPTED** |

---

# 1. Closure Record

```text
Change Package ID:
P11-MNT-004

Classification:
DEFECT

Severity:
P2 Major

Root Cause:
Required pass failures were incorrectly treated as recoverable at two
pipeline orchestration layers. Pipeline.run swallowed a pass execution
failure and continued to later passes; PassRegistry.get_passes swallowed an
enabled-pass construction failure and returned a partial pass list. The
compiler already had a propagation boundary, so the fix was to re-raise at
both swallow sites.

Authorized Files:
md_converter/pipeline/pipeline.py
md_converter/pipeline/pass_registry.py
md_converter/tests/test_pipeline_fail_closed.py
P11/P11_MAINTENANCE_REGISTRY.md
P11/maintenance/P11-MNT-004/**

Actual Changed Files:
md_converter/pipeline/pipeline.py
md_converter/pipeline/pass_registry.py
md_converter/tests/test_pipeline_fail_closed.py
P11/P11_MAINTENANCE_REGISTRY.md
P11/maintenance/P11-MNT-004/ISSUE_INTAKE.md
P11/maintenance/P11-MNT-004/REPRODUCTION.md
P11/maintenance/P11-MNT-004/ROOT_CAUSE_ANALYSIS.md
P11/maintenance/P11-MNT-004/CHANGE_PACKAGE.md
P11/maintenance/P11-MNT-004/TARGET_VERIFICATION.md
P11/maintenance/P11-MNT-004/REGRESSION_EVIDENCE.md
P11/maintenance/P11-MNT-004/SCOPE_AUDIT.md
P11/maintenance/P11-MNT-004/REVIEW_RECOVERY.md
P11/maintenance/P11-MNT-004/CLOSURE.md
P11/maintenance/P11-MNT-004/GIT_CLOSURE.md

Unauthorized Files:
0

Targeted Tests:
PASS — 5/5（test_pipeline_fail_closed.py）

Full Regression:
PASS — 289/289（exit code 0；failed 0；unexpected skip 0）

Conditional Gates:
COM = NOT REQUIRED（no COM lifecycle change）
DOCX / FinalArtifactQA = NOT REQUIRED（failure-path repair; regression covered）
Packaging = NOT REQUIRED
Fresh Install = NOT REQUIRED

Golden Drift:
0

Acceptance Drift:
0

Canonical Drift:
0

Architecture Drift:
0

Release Tag Drift:
0

P10 History Drift:
0

Fatal COM:
0

Required Skip:
0

git diff --cached --check:
PASS

Closure Commit:
PENDING_POST_COMMIT

Working Tree:
CLEAN

Maintenance Merger（post-recovery strict gate）:
PASS（RESULT: PASS；HEAD 798a65809f7ebc6367e7a9f058b8c40f09ca29a0；
merged files 197；generated nesting 0；
FILE: md_converter/py.typed count 1）

Review Evidence Recovery:
P11-RECOVERY-PYTYPED
recovery commit 798a65809f7ebc6367e7a9f058b8c40f09ca29a0
review-tool focused tests 5/5 PASS
289/289 regression evidence retained unchanged

Rollback:
revert implementation commit 17b74e13ad5599f08dbdeddf9486c7ac74be4dcc
and recovery commit 798a65809f7ebc6367e7a9f058b8c40f09ca29a0, plus this
bounded closure record set. No Canonical, Architecture, Acceptance, Golden,
tag, or P10 history is affected.

Residual Risk:
Pre-existing Ruff debt remains in review tooling scripts and is reported
without broad cleanup. No known product runtime residual risk remains in the
authorized fail-closed boundary.

Patch Release:
NOT REQUESTED / NOT TRIGGERED

Reviewer Final Acceptance:
APPROVED — TECHNICAL ACCEPTANCE

Human Final Acceptance:
APPROVED

Human Authorization Basis:
Human Final Acceptance message dated 2026-09-19 accepting the P11-MNT-004
implementation, verification evidence, Reviewer technical acceptance, and
P11-RECOVERY-PYTYPED recovery evidence, and authorizing Final Git Closure
and CLOSED / ACCEPTED.

Acceptance Date:
2026-09-19

Acceptance Basis Validation HEAD:
17b74e13ad5599f08dbdeddf9486c7ac74be4dcc

Recovery Evidence HEAD:
798a65809f7ebc6367e7a9f058b8c40f09ca29a0

P11 Program:
ACTIVE

Closure Decision:
CLOSED / ACCEPTED
```
