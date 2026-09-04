# P11 Reproduction Evidence Template

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_A / P11_AGENT_PLAN_B |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0（§9 Root Cause Gate / §12） |
| Usage | 复制后填写；Reproduction 未确认 → 不实施产品 patch |

---

```text
Issue ID:

Environment:

Input:

Prerequisites:

Reproduction Steps:
1.
2.
3.

Expected Behavior:

Expected Authority:
Canonical / ADR / Approved Behavior / Other

Actual Behavior:

Deviation:

Evidence:
logs / output / DOCX / stack trace / test

Deterministic:
YES / NO

Reproduction Result:
CONFIRMED / NOT_CONFIRMED

Notes:
```

---

# 规则

```text
Reproduction not confirmed
→ no product patch
```

```text
Root Cause 未验证时允许：诊断、reproduction test、evidence；
禁止大范围修复。
```
