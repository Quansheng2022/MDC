# P11 Test Matrix

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_A — Maintenance Governance Foundation |
| Work Package | P11-MNT-GOV-01 |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0（§10 Test Matrix / §10.1 / §10.2 / §11） |
| Canonical | `CANONICAL_SPEC.md` v1.0 FROZEN（SPEC-QA-001..004、SPEC-AC-001..004） |
| Status | ESTABLISHED — binding upon Human Freeze of P11 Authority |

---

# 1. Purpose

将 Phase 11 Spec 的 risk-based Test Matrix 转化为 Change Package 可直接选用的
Gate 规则，并固定 Golden / Acceptance Guard。

---

# 2. Risk-Based Test Matrix

| Change Type | Minimum Gate |
| --- | --- |
| Docs only | factual review + diff + Git closure |
| TEST_DEFECT | Unit + Targeted + Full Pytest |
| Parser / Normalize | Unit + Targeted + Full + Golden + Acceptance + DOCX |
| Diagram | Unit + Targeted + Full + Golden + Acceptance + DOCX |
| Decision / Layout | Unit + Targeted + Full + Golden + Acceptance + DOCX |
| Renderer / Writer | Unit + Targeted + Full + Golden + Acceptance + DOCX + conditional COM |
| PostProcessor / Final QA | Full quality gates + DOCX + conditional COM |
| COM lifecycle | targeted COM + DOCX |
| CLI | targeted + full + conditional acceptance / install |
| Packaging | targeted + full + Fresh Install |
| Dependency | broad regression + DOCX + conditional Golden / Acceptance / COM + Fresh Install |
| Security | risk-dependent required gates |
| Performance Regression | targeted performance evidence + regression |

---

# 3. Default Product-Code Gate

对 product code 的 P11 修复默认要求：

```text
Targeted Test:
PASS

Full Regression:
PASS

New Failure:
0

Required Skip:
0
```

如果 full regression 不适用，Change Package 必须明确说明原因并由 Reviewer 批准。

Agent 无权自行将 required gate 改为：

```text
SKIPPED
OPTIONAL
NOT NEEDED
```

除非 Change Package 明确批准。

---

# 4. Golden / Acceptance Guard

```text
IMPLEMENTATION FAILS GOLDEN
        ↓
DO NOT MODIFY GOLDEN
        ↓
INVESTIGATE IMPLEMENTATION / SPEC
```

禁止：

```text
failing test
→ rewrite expected output
→ declare PASS
```

Golden / Acceptance baseline 只有在以下条件全部满足时才允许修改：

```text
1. Canonical Authority 明确允许行为变化
2. 对应 Spec / ADR 已批准
3. 不属于简单 P11 defect patch
```

通常应进入 P12。

---

# 5. Runtime / Word COM Gate

如果变更涉及：

```text
WordRenderer
WordWriter
PostProcessor
COM lifecycle
TOC / Paragraph / Style proxy
retry / Word process cleanup
```

则至少要求：

```text
Dedicated COM Tests:
PASS

Representative DOCX:
PASS

FinalArtifactQA:
PASS

Fatal COM Error:
0
```

不得因 COM 环境偶发性而把 required test 改为 silent skip。

---

# 6. Fail-Closed 原则

```text
任何 Required Gate FAIL
    ↓
不得静默进入下一阶段
    ↓
QA 基础设施异常默认 FAIL CLOSED
```
