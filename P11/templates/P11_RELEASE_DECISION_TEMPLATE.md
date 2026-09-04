# P11 Release Decision Template

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_A / P11_AGENT_PLAN_C |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0（§18 / §19） |
| Usage | Patch Release Candidate 评审时填写；Human Production Approval 为 Required Gate |

---

```text
Candidate Version:

Included Maintenance Packages:

P1 Open:

Release-Critical P2 Open:

Regression:

Required Skip:

Golden:

Acceptance:

DOCX:

FinalArtifactQA:

COM:

Build:

Wheel:

Sdist:

Hashes:

Fresh Install:

CLI Smoke:

Version Consistency:

Release Notes:

Manifest:

Known Limitations:

Git Tree:

Technical Gate:
PASS / FAIL

Human Production Approval:
PENDING / APPROVED / REJECTED

Final Decision:
NOT AUTHORIZED until Human Approval
```

---

# 规则

```text
Any Required Gate FAIL
    ↓
PATCH RELEASE DENIED
```

AI Agent 不得自动批准 Patch Release / Release Tag。
