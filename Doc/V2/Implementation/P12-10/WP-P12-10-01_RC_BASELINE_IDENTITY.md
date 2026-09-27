# WP-P12-10-01 — RC Baseline & Identity

**Product Baseline:** `4c02734`

## Objective
Freeze the exact source and artifact identity to be called the RC.

## Record
- full P12-09 Closure SHA
- current source HEAD
- authoritative version
- installer filename/size/SHA-256
- executable filename/size/SHA-256
- P12-08 build provenance
- RC freeze timestamp
- RC identifier, e.g. `v1.1.0 RC1`

Prefer an evidence-only RC label. Do not change version metadata without Human authority.

## Consistency
Frozen hashes must match the P12-09 verified candidate. Hash mismatch = STOP / candidate drift.

## Filename Safety
Do not use Windows-invalid filename characters:
```text
\ / : * ? " < > |
```

## Acceptance
Source, installer, executable, version, and RC identifier are frozen; candidate drift = 0.
