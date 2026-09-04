# P11 Patch Release Gate

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_A — Maintenance Governance Foundation |
| Work Package | P11-MNT-GOV-01 |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0（§17 Patch Release Policy / §18 Gate / §19 Evidence） |
| Canonical | `CANONICAL_SPEC.md` v1.0 FROZEN（SPEC-INV-010 Release Evidence） |
| Status | ESTABLISHED — binding upon Human Freeze of P11 Authority |
| Release Action | NOT AUTHORIZED by this plan |

---

# 1. Purpose

本文件只建立 Patch Release 规则，不进行任何发布。

---

# 2. Version Policy

| Change | Version Policy |
| --- | --- |
| Bug / Security / Compatibility fix | `1.0.1`, `1.0.2`, ... |
| Backward-compatible feature | P12 → candidate `1.1.0` |
| Canonical semantic change | P12 |
| Breaking change | P12 → candidate `2.0.0` |

P11 默认只生产 Patch Release（`v1.0.x`）。

---

# 3. Patch Release Trigger

以下任一情况可考虑 patch release：

```text
- 已关闭 P1 / P2 production defect
- security fix
- major compatibility fix
- 多个已验证 P3 修复累积到发布阈值
- Human 明确要求 patch release
```

不是每个 Maintenance Commit 都必须发布。

---

# 4. Patch Release Gate（全部 Required）

| Gate | Acceptance |
| --- | --- |
| Maintenance Packages | Release 范围内全部 CLOSED / ACCEPTED |
| Open P1 Blockers | **0** |
| Release-Critical P2 | **0** |
| Targeted Tests | PASS |
| Full Regression | PASS |
| Required Skip | 0 |
| Golden | PASS if affected |
| Acceptance | PASS if affected |
| Representative DOCX | PASS if affected |
| FinalArtifactQA | PASS |
| COM Gate | PASS if affected |
| Packaging | PASS |
| wheel + sdist | Build PASS |
| Artifact Integrity | SHA256 recorded |
| Fresh Install | PASS |
| CLI Smoke | PASS |
| Version Consistency | PASS |
| Release Notes | COMPLETE |
| Patch Manifest | COMPLETE |
| Known Limitations | UPDATED if needed |
| Git Tree | CLEAN |
| Human Production Approval | REQUIRED |

Default decision：

```text
Any Required Gate FAIL
    ↓
PATCH RELEASE DENIED
```

禁止 fail-open。

---

# 5. Patch Release Evidence

Patch release 建议产生独立证据，例如：

```text
RC_EVIDENCE/P11_v1.0.1/
```

或项目既有 Release Evidence Authority 规定的等效结构。

至少记录：

```text
source commit SHA
maintenance package IDs
Python / dependency environment
regression result
Golden / Acceptance result（如适用）
representative DOCX evidence（如适用）
package filenames
SHA256
fresh install result
CLI smoke result
release decision
Human approval
```

---

# 6. Human Authority

```text
Patch Production Approval:   REQUIRED Human
Release Tag Approval:        REQUIRED Human
P11 Final Closure:           REQUIRED Human
```

AI Agent 不得自动批准 Patch Release / Release Tag / Final Closure。
