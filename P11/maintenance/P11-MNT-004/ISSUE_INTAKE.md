# P11-MNT-004 — Issue Intake

## Artifact Header

| Field | Value |
| --- | --- |
| ID | P11-MNT-004 |
| Title | Required Pipeline Pass Failure Does Not Fail Closed |
| Source | Human-authorized Phase 11 Batch C |
| Classification | DEFECT |
| Severity | P2 Major |
| Affected Version | v1.0.x |
| Component | `md_converter/pipeline/pipeline.py`, `md_converter/pipeline/pass_registry.py` |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0 §8 / §20 / §21 |
| Canonical References | `SPEC-INV-005`, `SPEC-INV-006` |
| Status | VERIFIED / AWAITING REVIEW |

## Problem

Required enabled Pipeline passes can fail without aborting compilation:

1. `Pipeline.run` catches a pass execution failure and continues.
2. `PassRegistry.get_passes` catches an enabled-pass construction failure and
   returns a partial pass list.

Both sites are part of one defect: required pass failure is incorrectly treated
as recoverable.

## Impact

- A required pipeline stage can be silently bypassed.
- Compilation can continue and produce a DOCX after a required pass fails.
- The behavior contradicts:

```text
SPEC-INV-005: 编译流程不得绕过任一阶段
SPEC-INV-006: Fail loudly; 禁止静默吞掉异常
```

## Status

Registered under the Human-authorized bounded Batch C execution.
