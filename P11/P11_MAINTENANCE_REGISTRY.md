# P11 Maintenance Registry

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_B — Maintenance Change Package Execution |
| Work Package | P11-MNT-001..006（CLOSED / ACCEPTED） |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0（§20 / §21 Continuous Model） |
| Status | ACTIVE — P11 Program; P11-MNT-001..006 CLOSED / ACCEPTED |

---

# 1. Purpose

集中登记全部 P11 Maintenance Issue 与 Maintenance Change Package 的状态，确保
每个 issue / package 可追溯。

---

# 2. Registry Fields

| ID | Title | Classification | Severity | Version | Component | Package | Status | Closure SHA | Release |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

字段说明：

```text
ID:             P11-ISSUE-NNN 或 P11-MNT-NNN
Classification: DEFECT / TEST_DEFECT / SPEC_GAP / ARCH_CHANGE / OPTIONAL_IMPROVEMENT
Severity:       P1 / P2 / P3 / P4 / Enhancement
Version:        v1.0.0 / v1.0.x
Component:      受影响编译阶段 / 模块
Package:        关联 Maintenance Change Package ID
Status:         NEW / UNCLASSIFIED / OPEN / APPROVED / IMPLEMENTED / VERIFIED /
                CLOSED / REJECTED / SPEC_GAP / ARCH_CHANGE / P12_CANDIDATE /
                ROOT_CAUSE_UNVERIFIED
Closure SHA:    Git closure commit SHA
Release:        关联 patch release（如有）
```

---

# 3. Registered Issues

```text
P11-MNT-001 | Word COM collection-time availability probe | TEST_DEFECT | P2 |
v1.0.0 | test_word_com_final_artifact.py | P11-MNT-001 | CLOSED |
ebcd4f948a3eee16476eb7b15c45b2b81ea67ac8 | <blank>

P11-MNT-002 | Generated Review Snapshot Nesting | DEFECT | P3 |
v1.0.x | tools/review/merge_project_for_phase11_review.py | P11-MNT-002 |
CLOSED | cf8460604e5e5adebb5882d3c2dc77f2762b05ac | <blank>

P11-MNT-003 | Explicit text fenced block auto-conversion | DEFECT | P2 |
v1.0.x | md_converter/pipeline/passes/ascii_mermaid_pass.py | P11-MNT-003 |
CLOSED | 83f7117a295d72df8001feaaa2ae673e463c58b0 | <blank>

P11-MNT-004 | Required Pipeline Pass Failure Does Not Fail Closed | DEFECT | P2 |
v1.0.x | md_converter/pipeline/pipeline.py | P11-MNT-004 |
CLOSED | fe0bcc0d1aa045e177846658de4bf00f2c3de614 | <blank>

P11-MNT-005 | Top-Level convert() Uses Stale Parallel Compiler Construction | DEFECT | P3 |
v1.0.x | md_converter/__init__.py | P11-MNT-005 |
APPROVED | <blank> | <blank>

P11-MNT-006 | Optional Word COM Import Must Degrade Gracefully | DEFECT | P2 |
v1.0.x | md_converter/renderer/post_processor.py | P11-MNT-006 |
CLOSED | <blank> | <blank>
```

Registry Table:

| ID | Title | Classification | Severity | Version | Component | Package | Status | Closure SHA | Release |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P11-MNT-001 | Word COM collection-time availability probe | TEST_DEFECT | P2 | v1.0.0 | test_word_com_final_artifact.py | P11-MNT-001 | CLOSED | ebcd4f948a3eee16476eb7b15c45b2b81ea67ac8 | — |
| P11-MNT-002 | Generated Review Snapshot Nesting | DEFECT | P3 | v1.0.x | tools/review/merge_project_for_phase11_review.py | P11-MNT-002 | CLOSED | cf8460604e5e5adebb5882d3c2dc77f2762b05ac | — |
| P11-MNT-003 | Explicit text fenced block auto-conversion | DEFECT | P2 | v1.0.x | md_converter/pipeline/passes/ascii_mermaid_pass.py | P11-MNT-003 | CLOSED | 83f7117a295d72df8001feaaa2ae673e463c58b0 | — |
| P11-MNT-004 | Required Pipeline Pass Failure Does Not Fail Closed | DEFECT | P2 | v1.0.x | md_converter/pipeline/pipeline.py | P11-MNT-004 | CLOSED | fe0bcc0d1aa045e177846658de4bf00f2c3de614 | — |
| P11-MNT-005 | Top-Level convert() Uses Stale Parallel Compiler Construction | DEFECT | P3 | v1.0.x | md_converter/__init__.py | P11-MNT-005 | CLOSED | 1b29bfd373e9000568244b9e940a65234af8d666 | — |
| P11-MNT-006 | Optional Word COM Import Must Degrade Gracefully | DEFECT | P2 | v1.0.x | md_converter/renderer/post_processor.py | P11-MNT-006 | CLOSED | 32f235ea9629ba3c40b24db03a8b6a67e9eeacc8 | — |

首个真实 issue 已登记（来源：PLAN_A final validation）。Package 证据：

```text
P11/maintenance/P11-MNT-001/ISSUE_INTAKE.md
P11/maintenance/P11-MNT-001/REPRODUCTION.md
P11/maintenance/P11-MNT-001/ROOT_CAUSE_ANALYSIS.md
P11/maintenance/P11-MNT-001/CHANGE_PACKAGE.md
```

P11-MNT-001 状态轨迹：

```text
OPEN（登记）
    ↓
VERIFIED（Targeted COM 3/3 + Full Regression 277/277 + B-12 merger strict PASS）
    ↓
WAITING_REVIEWER_ACCEPTANCE
    ↓
CLOSED / ACCEPTED（Reviewer + Human Final Acceptance，2026-09-04）
```

Reviewer Final Acceptance:
APPROVED

Human Final Acceptance:
APPROVED

Acceptance Basis Validation HEAD:
a315444d499c76ac60a2da96f0ad177ab7678aec

Git Closure Evidence Commit:

```text
ebcd4f948a3eee16476eb7b15c45b2b81ea67ac8
（governance(p11): close P11-MNT-001 test defect）
```

P11-MNT-002 状态轨迹：

```text
OPEN（Human 授权 Batch A / 登记）
    ↓
VERIFIED（targeted 4/4 + merger double-run no-nesting + Full Regression 281/281）
    ↓
WAITING_REVIEWER_ACCEPTANCE
    ↓
CLOSED / ACCEPTED（Reviewer + Human Final Acceptance，2026-09-19）
```

Reviewer Final Acceptance:
APPROVED

Human Final Acceptance:
APPROVED

Acceptance Basis Validation HEAD:
ace26d7a5e1a3ef4f0db2e1a5ef94a9ec1ae202f

P11-MNT-002 Closure Evidence:

```text
P11/maintenance/P11-MNT-002/CLOSURE.md
P11/maintenance/P11-MNT-002/GIT_CLOSURE.md
```

P11-MNT-002 Git Closure Evidence Commit:

```text
cf8460604e5e5adebb5882d3c2dc77f2762b05ac
（governance(p11): close P11-MNT-002 review infrastructure defect）
```

P11-MNT-002 Package 证据：

```text
P11/maintenance/P11-MNT-002/ISSUE_INTAKE.md
P11/maintenance/P11-MNT-002/REPRODUCTION.md
P11/maintenance/P11-MNT-002/ROOT_CAUSE_ANALYSIS.md
P11/maintenance/P11-MNT-002/CHANGE_PACKAGE.md
P11/maintenance/P11-MNT-002/TARGET_VERIFICATION.md
P11/maintenance/P11-MNT-002/REGRESSION_EVIDENCE.md
P11/maintenance/P11-MNT-002/SCOPE_AUDIT.md
P11/maintenance/P11-MNT-002/IMPLEMENTATION_COMMIT.md
P11/maintenance/P11-MNT-002/CLOSURE.md
P11/maintenance/P11-MNT-002/GIT_CLOSURE.md
```

P11-MNT-003 状态轨迹：

```text
OPEN（Human 授权 Batch B / 登记）
    ↓
VERIFIED（targeted 15/15 + behavior matrix + strict maintenance gate）
    ↓
WAITING_REVIEWER_ACCEPTANCE
    ↓
CLOSED / ACCEPTED（Reviewer + Human Final Acceptance，2026-09-19）
```

Reviewer Final Acceptance:
APPROVED

Human Final Acceptance:
APPROVED

Acceptance Basis Validation HEAD:
473c99eb5789b3e47cca5bb63c81f51a98109d37

P11-MNT-003 Closure Evidence:

```text
P11/maintenance/P11-MNT-003/CLOSURE.md
P11/maintenance/P11-MNT-003/GIT_CLOSURE.md
```

P11-MNT-003 Git Closure Evidence Commit:

```text
83f7117a295d72df8001feaaa2ae673e463c58b0
（governance(p11): close P11-MNT-003 explicit text fence defect）
```

P11-MNT-004 状态轨迹：

```text
OPEN（Human 授权 Batch C / 登记）
    ↓
VERIFIED（targeted 5/5 + behavior matrix + Full Regression 289/289）
    ↓
WAITING_REVIEWER_ACCEPTANCE
    ↓
REVIEW RECOVERY（P11-RECOVERY-PYTYPED；strict snapshot 含 py.typed）
    ↓
CLOSED / ACCEPTED（Reviewer + Human Final Acceptance，2026-09-19）
```

Reviewer Final Acceptance:
APPROVED — TECHNICAL ACCEPTANCE

Human Final Acceptance:
APPROVED

Acceptance Basis Validation HEAD:
17b74e13ad5599f08dbdeddf9486c7ac74be4dcc

Recovery Evidence HEAD:
798a65809f7ebc6367e7a9f058b8c40f09ca29a0

P11-MNT-004 Closure Evidence:

```text
P11/maintenance/P11-MNT-004/CLOSURE.md
P11/maintenance/P11-MNT-004/GIT_CLOSURE.md
```

P11-MNT-004 Git Closure Evidence Commit:

```text
fe0bcc0d1aa045e177846658de4bf00f2c3de614
（chore(p11): close P11-MNT-004）
```

P11-MNT-004 Package 证据：

```text
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
```

P11-MNT-003 Package 证据：

```text
P11/maintenance/P11-MNT-003/ISSUE_INTAKE.md
P11/maintenance/P11-MNT-003/REPRODUCTION.md
P11/maintenance/P11-MNT-003/ROOT_CAUSE_ANALYSIS.md
P11/maintenance/P11-MNT-003/CHANGE_PACKAGE.md
P11/maintenance/P11-MNT-003/TARGET_VERIFICATION.md
P11/maintenance/P11-MNT-003/REGRESSION_EVIDENCE.md
P11/maintenance/P11-MNT-003/SCOPE_AUDIT.md
P11/maintenance/P11-MNT-003/CLOSURE.md
P11/maintenance/P11-MNT-003/GIT_CLOSURE.md
```

P11-MNT-005 状态轨迹：

```text
APPROVED（Human 授权 bounded implementation / 登记）
    ↓
VERIFIED（targeted 2/2 + manual smoke + Full Regression 292/292）
    ↓
WAITING_REVIEWER_ACCEPTANCE
    ↓
CLOSED / ACCEPTED（Reviewer + Human Final Acceptance，2026-09-19）
```

Reviewer Final Acceptance:
APPROVED — TECHNICAL ACCEPTANCE

Human Final Acceptance:
APPROVED

Acceptance Basis Validation HEAD:
c433d10c2859c57cc97f32d25d6442f5d363f79e

P11-MNT-005 Closure Evidence:

```text
P11/maintenance/P11-MNT-005/CLOSURE.md
P11/maintenance/P11-MNT-005/GIT_CLOSURE.md
```

P11-MNT-005 Git Closure Evidence Commit:

```text
1b29bfd373e9000568244b9e940a65234af8d666
（chore(p11): close P11-MNT-005）
```

P11-MNT-005 Package 证据：

```text
P11/maintenance/P11-MNT-005/ISSUE_INTAKE.md
P11/maintenance/P11-MNT-005/REPRODUCTION.md
P11/maintenance/P11-MNT-005/ROOT_CAUSE_ANALYSIS.md
P11/maintenance/P11-MNT-005/CHANGE_PACKAGE.md
P11/maintenance/P11-MNT-005/TARGET_VERIFICATION.md
P11/maintenance/P11-MNT-005/REGRESSION_EVIDENCE.md
P11/maintenance/P11-MNT-005/SCOPE_AUDIT.md
P11/maintenance/P11-MNT-005/CLOSURE.md
P11/maintenance/P11-MNT-005/GIT_CLOSURE.md
```

P11-MNT-006 状态轨迹（来源：Production Usage Validation Cycle 01 / ISSUE-008）：

```text
CONFIRMED_DEFECT（Batch A reproduction）
    ↓
IMPLEMENTED（optional COM boundary guard；Implementation SHA d6be63e3cdb1ace80f01caafb3c37497c0315a81）
    ↓
TARGET VERIFIED（focused 4/4 + minimal-env smoke + normal-env smoke；sandbox 回归 296
          = 293 passed / 2 Golden-environment failures / 1 release-gate skip — 记录为
          非 canonical 历史证据）
    ↓
CANONICAL RATIFIED（Golden environment PASS + Word COM gate PASS + Golden PASS +
          focused PASS + full regression 296/296，0 failed / 0 errors / 0 skipped）
    ↓
CLOSED / ACCEPTED（Canonical closure ratification，2026-09-20）
```

Closure Evidence:

```text
P11/maintenance/P11-MNT-006/CLOSURE.md（含 §9 Canonical Closure Ratification）
```

P11-MNT-006 Scope:

```text
md_converter/renderer/post_processor.py   (optional COM import boundary + POST002)
md_converter/cli.py                       (structured diagnostic presentation)
md_converter/tests/test_com_optional_import.py
```

Issue source:

```text
Doc/production_soak/cycle_01/CLASSIFIED_ISSUES_CYCLE_01.md → ISSUE-008 (DEFECT / P2)
```

HG-B4（RATIFY EXISTING BOUNDED PATCH）与 HG-B2（merger inclusion-policy
scope expansion）均已由 Human 于 2026-09-04 批准。

P11 Program:
ACTIVE

Patch Release:
NOT REQUESTED / NOT AUTHORIZED BY PLAN_B

Final Acceptance Record Commit SHA 按 P11_AGENT_PLAN_B §22 在 post-commit
final report 中记录（同一 commit 不得自引用自身尚不存在的 SHA）。

不得人为创建虚假 defect 只是为了测试流程。

---

# 4. 登记规则

Agent 收到真实 issue 时：

```text
1. 复制 P11/templates/P11_ISSUE_INTAKE_TEMPLATE.md
2. 登记到本 Registry
3. 先分类，再定级，再 Repro / RCA
4. 未分类 / ROOT CAUSE UNVERIFIED 不得实施产品修改
```

---

# 5. Change Package 生命周期状态机

```text
OPEN
    ↓
REVIEW
    ↓
APPROVED
    ↓
IMPLEMENTED
    ↓
VERIFIED
    ↓
CLOSED
```

旁路状态：

```text
REJECTED
SPEC_GAP
ARCH_CHANGE
P12_CANDIDATE
ROOT_CAUSE_UNVERIFIED
```

关键权限：

```text
OPEN:      no code modification
REVIEW:    no code modification
APPROVED:  bounded modification permitted
IMPLEMENTED: tests pending
VERIFIED:  closure pending
CLOSED:    immutable maintenance record
```
