# P11 Maintenance Registry

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_A — Maintenance Governance Foundation |
| Work Package | P11-MNT-GOV-01 |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0（§20 / §21 Continuous Model） |
| Status | READY — 初始无已登记 Maintenance Issue |

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

# 3. 初始状态

```text
No maintenance issue registered.
```

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
