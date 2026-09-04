# P11 Severity Rules

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_A — Maintenance Governance Foundation |
| Work Package | P11-MNT-GOV-01 |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0（§6 Severity and Priority） |
| Canonical | `CANONICAL_SPEC.md` v1.0 FROZEN |
| Status | ESTABLISHED — binding upon Human Freeze of P11 Authority |

---

# 1. Purpose

建立唯一的 Severity / Priority 模型，对应 Phase 11 Work Package：
`P11-04 / WP-MNT-04 Priority`。

---

# 2. Severity Model

| Severity | 定义 | 处理要求 |
| --- | --- | --- |
| **P1 — Critical / Release Blocker** | 数据损坏、严重错误输出、安全问题、核心流程不可用 | 立即建立 Change Package；不得发布存在该 blocker 的 patch |
| **P2 — Major** | 主要功能错误、明显稳定性问题、常见环境失败 | 高优先级处理 |
| **P3 — Normal** | 边缘缺陷、低频兼容问题、非核心错误 | 正常 Maintenance backlog |
| **P4 — Minor** | cosmetic、轻微文档、低影响诊断问题 | 可延后 |
| **Enhancement** | 非缺陷新能力或改进 | 转 P12 / Evolution backlog |

---

# 3. 判定依据（允许）

Severity 必须根据以下因素决定：

```text
user impact
correctness impact
data risk
security risk
availability impact
frequency / probability
```

---

# 4. 禁止依据

Severity 不得由以下因素决定：

```text
LOC
coding effort
fix difficulty
AI confidence
developer preference
```

---

# 5. 安全缺陷默认评级

Security DEFECT 默认至少 **P2**；存在数据泄漏、任意文件访问、代码执行或严重
integrity 风险时按 **P1** 处理。

---

# 6. 使用规则

- Classification 与 Severity 分离：先分类（5 类），再定级（P1..P4 / Enhancement）。
- Enhancement 不是 P11 修复目标；Enhancement 转 P12 / backlog。
- P1 与 Release-critical P2 是 Patch Release 的 blocker；见
  `P11_PATCH_RELEASE_GATE.md`。
