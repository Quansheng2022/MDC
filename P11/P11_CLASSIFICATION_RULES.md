# P11 Classification Rules

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_A — Maintenance Governance Foundation |
| Work Package | P11-MNT-GOV-01 |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0（§5 Issue Classification） |
| Canonical | `CANONICAL_SPEC.md` v1.0 FROZEN |
| Status | ESTABLISHED — binding upon Human Freeze of P11 Authority |

---

# 1. Purpose

建立唯一的 Issue Classification 模型，对应 Phase 11 Work Package：
`P11-03 / WP-MNT-03 Triage`。

所有 P11 Issue 必须先分类，未分类不进入任何实施阶段。

---

# 2. Classification Model（唯一允许的 5 类）

```text
DEFECT
TEST_DEFECT
SPEC_GAP
ARCH_CHANGE
OPTIONAL_IMPROVEMENT
```

---

# 3. Decision Rules

## 3.1 DEFECT

定义：实现违反 Canonical / Approved Behavior。

必须同时存在：

```text
reproducible problem
authoritative expected behavior
observed actual behavior
proven deviation
testable acceptance criteria
```

处理：Change Plan → Patch → Evidence。

## 3.2 TEST_DEFECT

定义：测试错误，产品行为本身无缺陷（assertion / fixture / mock / 测试边界错误）。

处理：Test Change Review → Test Patch。

## 3.3 SPEC_GAP

定义：Canonical 对真实场景定义不足或矛盾（行为缺失 / 规则矛盾 / 场景未充分定义）。

处理：

```text
STOP PRODUCT CHANGE
HUMAN CLARIFICATION REQUIRED
```

## 3.4 ARCH_CHANGE

定义：修复需要改变已冻结架构边界。

处理：

```text
STOP
ADR / HUMAN APPROVAL
normally P12
```

## 3.5 OPTIONAL_IMPROVEMENT

定义：未违反任何 approved behavior，改进虽然可取但对正确性并非必要。

处理：

```text
P12 / backlog
NO P11 IMPLEMENTATION
```

---

# 4. Classification Guard（禁止）

```text
OPTIONAL_IMPROVEMENT
    ↓
重新命名为 DEFECT
    ↓
绕过 P12 / Human Gate
```

Reviewer 必须要求以下证据，缺失则不得按 DEFECT 执行：

```text
- 可复现问题
- Expected Behavior 权威来源
- Actual Behavior
- 明确 deviation
- 可验证 acceptance criteria
```

---

# 5. 未分类 / 未验证状态

```text
Issue Status:
UNCLASSIFIED

处理：
NO IMPLEMENTATION
```

```text
Root Cause Status:
ROOT CAUSE UNVERIFIED

允许：
- 增加诊断
- 增加 reproduction test
- 增加 evidence

禁止：
- 实施未经证据支持的大范围修复
```

---

# 6. 权威来源引用要求

每次分类必须引用权威来源：

```text
Canonical: CANONICAL_SPEC.md SPEC-ID / 章节
Architecture: ADR-ID
Approved Behavior: 已批准文档 / Change Package
```

没有权威来源的 “Expected” 不成立。
