# P11 Governance Baseline

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_A — Maintenance Governance Foundation |
| Work Package | P11-MNT-GOV-01 |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0 — FROZEN / ACTIVE P11 Maintenance Authority |
| Canonical | `CANONICAL_SPEC.md` v1.0 FROZEN（SPEC-GOAL-006 / SPEC-INV-010..012 等） |
| Architecture | ADR-001..ADR-009（`Doc/ARCHITECTURE.md`） |
| Execution Type | Governance / Baseline / Triage Foundation |
| Product Code Modification | FORBIDDEN |
| Canonical Modification | FORBIDDEN |
| Frozen Core Modification | FORBIDDEN |
| Golden / Acceptance Modification | FORBIDDEN |
| Patch Release | NOT AUTHORIZED |

---

# 1. Purpose

本文件记录 Phase 11 Maintenance Program 的 Authority 状态与治理基线，使后续
P11_AGENT_PLAN_B（Change Package 生命周期）、P11_AGENT_PLAN_C（Conditional
Patch Release）、P11_AGENT_PLAN_D（Governance Audit / Final Closure）可以在
明确、可审计、Default-Deny 的规则下执行。

---

# 2. Authority Hierarchy

```text
CANONICAL_SPEC.md
    ↓
ADR / Frozen Architecture Decisions
    ↓
Phase_11_Maintenance_Specification.md
    ↓
IMPLEMENTATION_PLAN.md
    ↓
Approved P11 Maintenance Change Package
    ↓
Implementation
    ↓
Test / Evidence
```

冲突时的权威顺序：

```text
Canonical
>
ADR
>
P11 Maintenance Authority
>
Implementation Plan
>
Change Package
>
Implementation
>
Test Convenience
```

AI Agent 不得使用 test convenience / implementation convenience / refactoring
preference / code quality preference / future extensibility 反向修改更高层
Authority。

---

# 3. Authority State Record

```text
P11 Authority Version:    1.0
P11 Authority Status:     FROZEN / ACTIVE
Human Freeze:             APPROVED
Freeze Date:              2026-09-04
Freeze Commit:            bddf36f0ae5667c485aca7cd7132a38d765eb5cc
```

记录依据：Human 已于 2026-09-04 明确批准
`Doc/Phase_11_Maintenance_Specification.md` v1.0 作为 P11 Maintenance Authority，
Authority Freeze 已由 Git commit `bddf36f0ae5667c485aca7cd7132a38d765eb5cc` 固化。

未知值一律写 `NOT YET AVAILABLE`，不得猜测。

---

# 4. Initial P11 State（Human Freeze 之前）

```text
P11 Status:
DRAFT / NOT YET FROZEN

Product Code Change:
NONE AUTHORIZED

Canonical Change:
NONE AUTHORIZED

Frozen Core Change:
NONE AUTHORIZED

Golden / Acceptance Change:
NONE AUTHORIZED

Patch Release:
NONE AUTHORIZED
```

---

# 5. Human Gate List（AI Agent 无权自动执行）

```text
P11 Maintenance Authority Freeze
SPEC_GAP Canonical clarification
ARCH_CHANGE approval
Patch Release Approval
Release Tag Approval / Ratification
P11 Final Closure
```

执行模式固定为：

```text
AI Agent prepares
AI Agent verifies
AI Agent reports
Human approves
```

而不是：

```text
AI Agent prepares
AI Agent self-approves
```

---

# 6. Maintenance Governance Principles

1. **Canonical Authority**：Maintenance 不得越过 Canonical。
2. **Minimal Change**：只修复已验证问题，不进行顺带重构。
3. **Evidence Before Patch**：没有 reproduction / deviation evidence，不实施产品修复。
4. **Classification Before Implementation**：先判断 DEFECT / TEST_DEFECT /
   SPEC_GAP / ARCH_CHANGE / OPTIONAL_IMPROVEMENT。
5. **Default Deny Scope**：未列入 Allowed Scope 的文件默认禁止修改。
6. **No Silent Baseline Drift**：Golden、Acceptance、Canonical、Release Evidence
   不得为迁就实现而静默变化。
7. **Risk-Based Testing**：测试 Gate 由受影响边界决定，但 required gate 不得静默 skip。
8. **Git Closure Is Mandatory**：每个已实施 Maintenance Package 必须形成 exact、
   clean、可追溯 closure。
9. **Patch Release Is Conditional**：Maintenance commit 不等于必须 release。
10. **Human Release Authority**：Patch Production Approval、Tag、P11 Final Closure
    保留 Human Gate。
11. **Evolution Separation**：Feature / Semantic / Architecture evolution 属于 P12，
    不得借 P11 越权实现。

---

# 7. Freeze / Status Update Rule

本文档仅在以下条件满足时更新 Authority 状态：

```text
Human 明确批准：

APPROVE AND FREEZE
Phase_11_Maintenance_Specification.md
VERSION: 1.0
AS P11 MAINTENANCE AUTHORITY
```

批准后记录：

```text
Spec Version:
1.0

Status:
FROZEN / ACTIVE

Authority:
P11 Maintenance Authority

Human Freeze:
APPROVED

Freeze Date:
<actual approved date>

Freeze Commit:
<recorded Git SHA>
```

本文件随 `P11-MNT-GOV-01` 的 Governance Closure 一并收口，任何后续规则修改必须走
Spec / Governance Change → Human Approval 流程。

---

# 8. Scope Boundaries

- Allowed / Forbidden Maintenance Scope：见 `P11_SCOPE_BASELINE.md`。
- P11 / P12 路由边界：见 `P11_P12_BOUNDARY.md`。
- 产品代码 / Frozen Core / Golden / Acceptance：READ ONLY。
- `v1.0.0` tag：IMMUTABLE。

---

# 9. Record

| Item | Value |
| --- | --- |
| Governance Baseline File | `P11/P11_GOVERNANCE_BASELINE.md` |
| Created By | P11_AGENT_PLAN_A / P11-MNT-GOV-01 |
| Created Date | 2026-09-04 |
| Status | FROZEN / ACTIVE — Human Freeze approved 2026-09-04 |
