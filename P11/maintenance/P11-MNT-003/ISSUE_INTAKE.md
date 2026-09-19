# P11-MNT-003 — Issue Intake

## Artifact Header

| Field | Value |
| --- | --- |
| ID | P11-MNT-003 |
| Title | Explicit text fenced block is incorrectly auto-converted into ASCII/Mermaid diagram |
| Source | Human-authorized Phase 11 Batch B |
| Classification | DEFECT |
| Severity | P2 Major |
| Affected Version | v1.0.x |
| Component | `md_converter/pipeline/passes/ascii_mermaid_pass.py` |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0 §8 / §20 / §21 |
| Canonical References | `SPEC-FUNC-005`, `SPEC-FUNC-014`, `SPEC-ARCH-003`, `SPEC-GOAL-004` |
| Status | VERIFIED / AWAITING REVIEW |

## Problem

An explicitly declared `text` fenced block is parsed correctly as
`CodeBlock(language="text")`, but `AsciiToMermaidPass` then attempts the
diagram rescue path and ASCII auto-detection. If the content resembles a
diagram, the explicit text block is replaced by a `Diagram` node.

## Impact

- Explicit author intent is lost.
- Literal `text` examples that contain arrows, boxes, or Mermaid-like lines can
  be converted into diagrams and rendered incorrectly.
- The behavior contradicts the expected precedence:

```text
explicit text syntax
    >
Mermaid rescue
    >
ASCII heuristic
```

## Scope Boundary

This change fixes only `language == "text"`.

It must not redefine:

```text
plain
txt
markdown
md
other fence languages
```

## Status

Registered under the Human-authorized bounded Batch B execution.
