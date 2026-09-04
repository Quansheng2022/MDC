# P11 Maintenance Change Package Template

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_A / P11_AGENT_PLAN_B |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0（§8 Maintenance Change Package） |
| Usage | 每个实际修改必须拥有独立 Change Package；先 APPROVED 后修改 |

---

```text
Change Package:
P11-MNT-XXX

Title:
<short descriptive title>

Source:
<Canonical / ADR / defect evidence / compatibility requirement>

Classification:
DEFECT / TEST_DEFECT / SPEC_GAP / ARCH_CHANGE / OPTIONAL_IMPROVEMENT

Severity:
P1 / P2 / P3 / P4 / Enhancement

Affected Version:
v1.0.0 / v1.0.x

Affected Component:
<component>

Problem:
<verified problem>

Reproduction:
<minimal deterministic reproduction>

Expected:
<expected behavior>

Actual:
<actual behavior>

Evidence:
<logs / output / DOCX / stack trace / failing test>

Root Cause:
<verified root cause; UNKNOWN until verified>

Allowed Scope:
<exact files/modules allowed to change>

Forbidden Scope:
<files/modules explicitly prohibited>

Required Tests:
<targeted tests>

Conditional Gates:
Golden / Acceptance / Real DOCX / COM / Packaging / Fresh Install

Acceptance Criteria:
<measurable pass criteria>

Rollback:
<how to revert if needed>

Git Closure:
exact diff
authorized files only
git diff --check PASS
working tree CLEAN
closure commit SHA

Status:
OPEN / APPROVED / IMPLEMENTED / VERIFIED / CLOSED / REJECTED
```

---

# 规则

```text
Allowed Scope 必须尽量小。
未列入 Allowed Scope 的文件默认禁止修改。
AI Agent 不得因“顺便重构 / 代码更优雅 / 统一风格 / 消除技术债 / 未来更易扩展”
扩大范围。
```
