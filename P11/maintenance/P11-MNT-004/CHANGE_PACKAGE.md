# P11-MNT-004 — Maintenance Change Package

## Artifact Header

| Field | Value |
| --- | --- |
| Change Package | P11-MNT-004 |
| Title | Required Pipeline Pass Failure Does Not Fail Closed |
| Source | Human-authorized Phase 11 Batch C |
| Classification | DEFECT |
| Severity | P2 Major |
| Affected Version | v1.0.x |
| Affected Component | `md_converter/pipeline/pipeline.py`, `md_converter/pipeline/pass_registry.py` |
| Canonical References | `SPEC-INV-005`, `SPEC-INV-006` |
| Status | VERIFIED / AWAITING REVIEW |

## Authorized Scope

```text
md_converter/pipeline/pipeline.py
md_converter/pipeline/pass_registry.py
one focused pipeline/pass-registry test module
P11/P11_MAINTENANCE_REGISTRY.md
P11/maintenance/P11-MNT-004/**
```

## Forbidden Scope

```text
md_converter/compiler.py unless strictly necessary (then STOP)
Parser / AST
Renderer / Writer
QA / FinalArtifactQA
Diagnostic framework redesign
new exception hierarchy
retry / fallback framework
optional-pass framework
logging / print cleanup
general refactor
CANONICAL_SPEC.md
Architecture / ADR
Acceptance / Golden
dependencies
tools/review changes
P11-MNT-005
PLAN_C
version / tag / release work
```

## Implementation

Minimal fail-closed propagation only:

```text
Pipeline.run
    after existing PIPE001 diagnostic:
        bare raise

PassRegistry.get_passes
    after enabled-pass construction failure logging:
        re-raise the current exception
```

No unrelated cleanup. No new framework. Successful-pass and disabled-pass
behavior must remain unchanged.

## Required Evidence

```text
REPRODUCTION.md
ROOT_CAUSE_ANALYSIS.md
TARGET_VERIFICATION.md
REGRESSION_EVIDENCE.md
SCOPE_AUDIT.md
```
