# P11 / P12 Evolution Boundary

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_A — Maintenance Governance Foundation |
| Work Package | P11-MNT-GOV-01 |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0（§4.2 / §23 / §24） |
| Canonical | `CANONICAL_SPEC.md` v1.0 FROZEN |
| Status | ESTABLISHED — binding upon Human Freeze of P11 Authority |

---

# 1. Purpose

固定 P11 Maintenance 与 P12 Evolution 的路由边界，防止 Feature / Semantic /
Architecture evolution 借 P11 越权实现。

---

# 2. P11 边界（Maintenance）

```text
verified defect
stability
security
compatibility
dependency maintenance
test defect
documentation correction
performance regression
diagnostic fix
strictly necessary bounded refactor
```

---

# 3. P12 边界（Evolution）

```text
new feature
new Markdown behavior
new CLI capability
new renderer
new output format
AST schema evolution
DecisionEngine semantic evolution
LayoutPlan evolution
new canonical theme behavior
Acceptance semantic change
architecture change
major dependency-induced semantic change
optional improvement
```

---

# 4. Routing Rule

```text
IF maintenance can preserve:
    Canonical semantics
    Frozen architecture
    Acceptance meaning
THEN
    P11 candidate
ELSE
    STOP
    P12 candidate
```

---

# 5. 禁止自动越界

```text
PLAN_A CLOSED
    ↓
自动扫描代码寻找“改进点”
    ↓
制造 defect / refactor
```

正确流程：

```text
PLAN_A CLOSED
    ↓
WAIT FOR REAL MAINTENANCE ISSUE
    ↓
Issue Intake → Classification → Severity → Reproduction
    ↓
Approved Maintenance Change Package → P11_AGENT_PLAN_B
```

---

# 6. 计划职责划分

```text
PLAN_A establishes authority.
PLAN_B executes maintenance.
PLAN_C releases patches.
PLAN_D audits and closes governance.
```
