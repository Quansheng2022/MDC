# P11-MNT-005 — Issue Intake

## Artifact Header

| Field | Value |
| --- | --- |
| ID | P11-MNT-005 |
| Title | Top-Level convert() Uses Stale Parallel Compiler Construction |
| Source | P11-BACKLOG-TRIAGE-CONVERT + Human-authorized bounded implementation |
| Classification | DEFECT |
| Severity | P3 Normal |
| Affected Version | v1.0.x |
| Component | `md_converter/__init__.py` |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0 §8 / §20 / §21 |
| Canonical References | `SPEC-GOAL-002`, `SPEC-GOAL-006` |
| Status | APPROVED → VERIFIED / AWAITING REVIEW |

## Problem

`md_converter.convert()` owns a stale duplicated compiler-construction path.
It manually assembles `PassRegistry`, `CompilerContext`, config, and theme
instead of delegating to the existing canonical helper.

Primary failure:

```text
from md_converter import convert
convert("# Hello")

AttributeError: 'PassRegistry' object has no attribute '_pass_classes'
```

Secondary supporting evidence:

```text
After bypassing plugin discovery during triage:
KeyError: 'enable_cover'
```

The secondary KeyError is supporting evidence for the same stale construction
path, not a second maintenance issue.

## Impact

- The exported public API fails on first use in a normal installed
  environment.
- Config defaults are not resolved through the canonical path.
- Theme construction differs from `CompilerContext.create()`.
- The public API is not covered by tests.

## Expected

```text
convert()
    delegates to the existing canonical compiler path
    preserves the existing signature
    does not add API parameters
    does not redefine output/save semantics
```
