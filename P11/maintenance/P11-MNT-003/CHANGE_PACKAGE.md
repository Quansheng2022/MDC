# P11-MNT-003 — Maintenance Change Package

## Artifact Header

| Field | Value |
| --- | --- |
| Change Package | P11-MNT-003 |
| Title | Explicit text fenced block is incorrectly auto-converted into ASCII/Mermaid diagram |
| Source | Human-authorized Phase 11 Batch B |
| Classification | DEFECT |
| Severity | P2 Major |
| Affected Version | v1.0.x |
| Affected Component | `md_converter/pipeline/passes/ascii_mermaid_pass.py` |
| Canonical References | `SPEC-FUNC-005`, `SPEC-FUNC-014`, `SPEC-ARCH-003`, `SPEC-GOAL-004` |
| Status | VERIFIED / AWAITING REVIEW |

## Problem

Explicit `text` fenced blocks are overridden by Mermaid rescue or ASCII
heuristic inference.

## Expected Precedence

```text
explicit text syntax
    >
Mermaid rescue
    >
ASCII heuristic
```

## Authorized Scope

```text
md_converter/pipeline/passes/ascii_mermaid_pass.py
md_converter/tests/test_ascii_mermaid_pass.py
P11/P11_MAINTENANCE_REGISTRY.md
P11/maintenance/P11-MNT-003/**
```

## Forbidden Scope

```text
parser changes
AsciiToMermaidService changes unless absolutely necessary (then STOP)
renderer changes
QA / FinalArtifactQA changes
CANONICAL_SPEC.md
architecture changes
Acceptance corpus changes
Golden baseline changes
dependency changes
tools/review changes
docs cleanup
Ruff cleanup outside changed code
P11-MNT-004 / P11-MNT-005
PLAN_C
release / version / tag work
```

## Implementation

Smallest correct patch:

After normalizing `CodeBlock.language`, return the explicit `text`
`CodeBlock` unchanged before `_rescue_diagram_code()` and before ASCII
auto-detection.

Do not redefine `plain`, `txt`, `markdown`, `md`, or other languages.

## Required Evidence

```text
REPRODUCTION.md
ROOT_CAUSE_ANALYSIS.md
TARGET_VERIFICATION.md
REGRESSION_EVIDENCE.md
SCOPE_AUDIT.md
```
