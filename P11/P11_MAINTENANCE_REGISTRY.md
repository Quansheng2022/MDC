# P11 Maintenance Registry

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_B — Maintenance Change Package Execution |
| Work Package | P11-MNT-001（CLOSED） / P11-MNT-002（CLOSED / ACCEPTED） / P11-MNT-003（CLOSED / ACCEPTED） |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0（§20 / §21 Continuous Model） |
| Status | ACTIVE — P11 Program; P11-MNT-001 CLOSED / ACCEPTED; P11-MNT-002 CLOSED / ACCEPTED; P11-MNT-003 CLOSED / ACCEPTED |

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
VERIFIED | <blank> | <blank>

P11-MNT-003 | Explicit text fenced block auto-conversion | DEFECT | P2 |
v1.0.x | md_converter/pipeline/passes/ascii_mermaid_pass.py | P11-MNT-003 |
OPEN | <blank> | <blank>
```

Registry Table:

| ID | Title | Classification | Severity | Version | Component | Package | Status | Closure SHA | Release |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P11-MNT-001 | Word COM collection-time availability probe | TEST_DEFECT | P2 | v1.0.0 | test_word_com_final_artifact.py | P11-MNT-001 | CLOSED | ebcd4f948a3eee16476eb7b15c45b2b81ea67ac8 | — |
| P11-MNT-002 | Generated Review Snapshot Nesting | DEFECT | P3 | v1.0.x | tools/review/merge_project_for_phase11_review.py | P11-MNT-002 | CLOSED | cf8460604e5e5adebb5882d3c2dc77f2762b05ac | — |
| P11-MNT-003 | Explicit text fenced block auto-conversion | DEFECT | P2 | v1.0.x | md_converter/pipeline/passes/ascii_mermaid_pass.py | P11-MNT-003 | CLOSED | 83f7117a295d72df8001feaaa2ae673e463c58b0 | — |

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
