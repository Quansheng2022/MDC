# P11 Maintenance Package Closure — P11-MNT-005

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_B — Maintenance Change Package Execution |
| Work Package | P11-MNT-005 |
| Authority | `P11_CLOSURE_TEMPLATE.md` / `Doc/Phase_11_Maintenance_Specification.md` v1.0（§16 / §17） |
| Date | 2026-09-19 |
| Status | **CLOSED / ACCEPTED** |

---

# 1. Closure Record

```text
Change Package ID:
P11-MNT-005

Classification:
DEFECT

Severity:
P3 Normal

Root Cause:
md_converter.convert() owned a stale duplicated compiler-construction path.
It manually assembled DiagnosticCollector / ParserContext / RenderContext /
PassRegistry / CompilerContext instead of delegating to the existing canonical
compile_markdown() path. In a normal installed environment this raised
AttributeError because PassRegistry has no _pass_classes attribute. With
plugin discovery bypassed, the same stale path reached compile() with
unresolved config and raised KeyError: 'enable_cover'.

Authorized Files:
md_converter/__init__.py
md_converter/tests/test_public_api_convert.py
P11/P11_MAINTENANCE_REGISTRY.md
P11/maintenance/P11-MNT-005/**

Actual Changed Files:
md_converter/__init__.py
md_converter/tests/test_public_api_convert.py
P11/P11_MAINTENANCE_REGISTRY.md
P11/maintenance/P11-MNT-005/ISSUE_INTAKE.md
P11/maintenance/P11-MNT-005/REPRODUCTION.md
P11/maintenance/P11-MNT-005/ROOT_CAUSE_ANALYSIS.md
P11/maintenance/P11-MNT-005/CHANGE_PACKAGE.md
P11/maintenance/P11-MNT-005/TARGET_VERIFICATION.md
P11/maintenance/P11-MNT-005/REGRESSION_EVIDENCE.md
P11/maintenance/P11-MNT-005/SCOPE_AUDIT.md
P11/maintenance/P11-MNT-005/CLOSURE.md
P11/maintenance/P11-MNT-005/GIT_CLOSURE.md

Unauthorized Files:
0

Targeted Tests:
PASS — 2/2（test_public_api_convert.py）

Full Regression:
PASS — 292/292（exit code 0；failed 0；unexpected skip 0）

Conditional Gates:
COM = NOT REQUIRED（no COM lifecycle change）
DOCX / FinalArtifactQA = NOT REQUIRED（public API construction repair；regression covered）
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

Maintenance Merger（post-implementation strict gate）:
PASS（RESULT: PASS；HEAD c433d10c2859c57cc97f32d25d6442f5d363f79e；
merged files 207；generated nesting 0；
FILE: md_converter/py.typed count 1）

Rollback:
revert implementation commit c433d10c2859c57cc97f32d25d6442f5d363f79e
and this bounded closure record set. No Canonical, Architecture, Acceptance,
Golden, tag, or P10 history is affected.

Residual Risk:
The observed pre-existing cp1252 console encoding issue is outside
P11-MNT-005 and is not authorized for repair by this acceptance. No known
residual risk remains in the authorized convert() public API boundary.

Patch Release:
NOT REQUESTED / NOT TRIGGERED

Reviewer Final Acceptance:
APPROVED — TECHNICAL ACCEPTANCE

Human Final Acceptance:
APPROVED

Human Authorization Basis:
Human Final Acceptance message dated 2026-09-19 accepting the P11-MNT-005
classification, implementation SHA, bounded convert() repair, focused and full
verification evidence, strict gate, nesting result, py.typed inclusion,
clean-tree result, and Reviewer technical acceptance, and authorizing Final
Git Closure and CLOSED / ACCEPTED.

Acceptance Date:
2026-09-19

Acceptance Basis Validation HEAD:
c433d10c2859c57cc97f32d25d6442f5d363f79e

P11 Program:
ACTIVE

Closure Decision:
CLOSED / ACCEPTED
```
