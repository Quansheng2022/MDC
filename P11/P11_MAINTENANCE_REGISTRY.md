# P11 Maintenance Registry

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_B — Maintenance Change Package Execution |
| Work Package | P11-MNT-001 |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0（§20 / §21 Continuous Model） |
| Status | ACTIVE — P11-MNT-001 OPEN / WAITING_HUMAN_APPROVAL（HG-B4） |

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
v1.0.0 | test_word_com_final_artifact.py | P11-MNT-001 | OPEN | <blank> | <blank>
```

Registry Table:

| ID | Title | Classification | Severity | Version | Component | Package | Status | Closure SHA | Release |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P11-MNT-001 | Word COM collection-time availability probe | TEST_DEFECT | P2 | v1.0.0 | test_word_com_final_artifact.py | P11-MNT-001 | VERIFIED | — | — |

首个真实 issue 已登记（来源：PLAN_A final validation）。Package 证据：

```text
P11/maintenance/P11-MNT-001/ISSUE_INTAKE.md
P11/maintenance/P11-MNT-001/REPRODUCTION.md
P11/maintenance/P11-MNT-001/ROOT_CAUSE_ANALYSIS.md
P11/maintenance/P11-MNT-001/CHANGE_PACKAGE.md
```

P11-MNT-001 状态轨迹：OPEN（登记）-> VERIFIED（B-16，Targeted 3/3 +
Full Regression 277/277 完成）-> CLOSED（Git Closure 后由 ratification 记录
填入 Closure SHA）。HG-B4（RATIFY）与 HG-B2（Scope Expansion：merger
inclusion policy）均已由 Human 于 2026-09-04 批准。

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
