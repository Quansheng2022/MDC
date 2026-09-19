# P11-MNT-003 — Scope Audit

## Authorized Product File

```text
md_converter/pipeline/passes/ascii_mermaid_pass.py
```

## Authorized Test File

```text
md_converter/tests/test_ascii_mermaid_pass.py
```

## Authorized Governance Files

```text
P11/P11_MAINTENANCE_REGISTRY.md
P11/maintenance/P11-MNT-003/**
```

## Forbidden Scope Audit

```text
parser changes:                       no changes
AsciiToMermaidService changes:        no changes
renderer changes:                     no changes
QA / FinalArtifactQA changes:         no changes
CANONICAL_SPEC.md:                    no changes
architecture changes:                 no changes
Acceptance corpus changes:            no changes
Golden baseline changes:              no changes
dependency changes:                   no changes
tools/review changes:                 no changes
docs cleanup:                         not performed
Ruff cleanup outside changed code:    not performed
P11-MNT-004 / P11-MNT-005:            not started
PLAN_C:                               not started
release / version / tag work:         not performed
```

## Unauthorized Changes

```text
0
```

## Generated Review Output

All generated strict-merger and reviewer-bundle outputs are written outside
`PROJECT_ROOT`; they are not part of the implementation commit.
