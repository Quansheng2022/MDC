# P11 Scope Baseline

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_A — Maintenance Governance Foundation |
| Work Package | P11-MNT-GOV-01 |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0（§4 Scope） |
| Canonical | `CANONICAL_SPEC.md` v1.0 FROZEN |
| Scope Status | ESTABLISHED — binding upon Human Freeze of P11 Authority |
| Product Code Modification | FORBIDDEN by this plan |

---

# 1. Purpose

把 Phase 11 Specification 中的 Allowed / Forbidden Maintenance Scope 转换为后续
Agent 可以直接执行的 Scope Authority，防止 Maintenance 演变为无边界重构。

对应 Phase 11 Work Package：`P11-01 / WP-MNT-01 Scope`。

---

# 2. Allowed Maintenance Scope

| 类型 | 代码 | 允许 |
| --- | --- | --- |
| Product Defect Fix | PRODUCT_DEFECT_FIX | ✅ |
| Stability Fix | STABILITY_FIX | ✅ |
| Security Fix | SECURITY_FIX | ✅ |
| Compatibility Fix | COMPATIBILITY_FIX | ✅ |
| Dependency Maintenance | DEPENDENCY_MAINTENANCE | ✅ |
| Test Defect Fix | TEST_DEFECT_FIX | ✅ |
| Documentation Correction | DOCUMENTATION_CORRECTION | ✅ |
| Performance Regression Fix | PERFORMANCE_REGRESSION_FIX | ✅ |
| Operational / Diagnostic Fix | OPERATIONAL_DIAGNOSTIC_FIX | ✅ |
| Minimal Refactor Required by Fix | MINIMAL_REFACTOR_REQUIRED_BY_FIX | ⚠️ 仅限缺陷修复不可避免的最小结构调整 |

---

# 3. Forbidden Maintenance Scope

| 类型 | 代码 | 处理 |
| --- | --- | --- |
| New Markdown feature | NEW_MARKDOWN_FEATURE | P12 |
| New CLI product feature | NEW_CLI_PRODUCT_FEATURE | P12 |
| New renderer | NEW_RENDERER | P12 |
| New output format | NEW_OUTPUT_FORMAT | P12 |
| AST schema evolution | AST_SCHEMA_EVOLUTION | P12 |
| DecisionEngine semantic change | DECISION_ENGINE_SEMANTIC_CHANGE | P12 |
| LayoutPlan schema evolution | LAYOUT_PLAN_SCHEMA_EVOLUTION | P12 |
| Theme V2 / Canonical theme semantic change | THEME_V2 / CANONICAL_THEME_CHANGE | P12 |
| Acceptance semantic redefinition | ACCEPTANCE_SEMANTIC_REDEFINITION | P12 |
| Golden baseline drift for implementation convenience | GOLDEN_DRIFT | 禁止 |
| General code cleanup | GENERAL_CODE_CLEANUP | 禁止 |
| Unjustified architecture refactor | UNJUSTIFIED_ARCH_REFACTOR | 禁止 |
| Optional improvement auto-implementation | OPTIONAL_IMPROVEMENT_IMPLEMENTATION | P12 / backlog |
| Test change to hide product defect | TEST_CHANGE_TO_HIDE_PRODUCT_DEFECT | 禁止 |

---

# 4. Scope Decision Rule

```text
P11_SCOPE_DECISION(change)

IF change is explicitly maintenance:
    P11 candidate
ELSE IF feature / semantic / architecture evolution:
    P12 candidate
ELSE:
    DENY
```

---

# 5. Default Deny Rule

> 没有明确授权的动作默认禁止。

```text
Product code:            READ ONLY
Frozen Core:             READ ONLY
CANONICAL_SPEC.md:       READ ONLY
ADR:                     READ ONLY
Golden:                  READ ONLY
Acceptance baseline:     READ ONLY
P10 evidence:            READ ONLY
v1.0.0 tag:              IMMUTABLE
```

只有明确获批的 Governance 文件 / Maintenance Change Package Allowed Scope 可以创建
或修改。

---

# 6. No Feature Development Rule

P11 不是继续开发新功能的阶段：

- 禁止“顺便重构”、“代码更优雅”、“统一风格”、“消除技术债”、“未来更易扩展”作为扩大
  范围的依据。
- Feature / Semantic / Architecture evolution 一律路由到 `P12_Evolution`。
- Optional Improvement 默认进入 Backlog，不得改名为 DEFECT 绕过 P12 / Human Gate。

---

# 7. Scope 冻结与变更

本 Scope Baseline 在 P11 Authority Human Freeze 后正式生效。本文件本身的实质性
修改必须走 Governance Change → Human Approval 流程，不得由普通 Maintenance Patch
顺带完成。
