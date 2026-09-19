# P11-MNT-002 — Maintenance Change Package

## Artifact Header

| Field | Value |
| --- | --- |
| Change Package | P11-MNT-002 |
| Title | Generated Review Snapshot Nesting |
| Source | Human-authorized Batch A; roadmap item 27 |
| Classification | DEFECT |
| Severity | P3 |
| Affected Version | v1.0.x maintenance tooling |
| Affected Component | `tools/review/merge_project_for_phase11_review.py` |
| Canonical References | `SPEC-GOAL-003`, `SPEC-GOAL-006` |
| Status | VERIFIED / AWAITING REVIEW |

## Problem

Generated review snapshots were eligible for inclusion in later review
snapshots, causing recursive embedding and non-reproducible review scope.

## Expected

Review snapshots contain project source, governance, tests, and tooling only.
Previously generated review artifacts are excluded regardless of their output
name or conventional directory.

## Actual

Before the fix, consecutive list-only runs selected 170 and 171 files and
included prior `Merged_Code/` and `Review_Bundle/` artifacts.

## Allowed Scope

- `tools/review/merge_project_for_phase11_review.py`
- `tools/review/collect_project_for_review.py`
- focused tests for these tools
- `P11/P11_MAINTENANCE_REGISTRY.md`
- `P11/maintenance/P11-MNT-002/**`

## Forbidden Scope

- `md_converter` product/runtime code
- `CANONICAL_SPEC.md`
- frozen architecture
- Acceptance / Golden semantics
- dependencies
- P11-MNT-003 / P11-MNT-004 / P11-MNT-005 implementation
- release / PLAN_C
- broad refactoring
- new governance framework

## Implementation

Bounded tooling-only changes:

1. Merger version `1.2.1`.
2. `Merged_Code` and `Review_Bundle` added to generated path exclusions.
3. Generated review artifact name patterns excluded during enumeration.
4. Collector `TEXT_EXTENSIONS` includes `.typed`, covering
   `md_converter/py.typed`.
5. Focused regression tests added for both tools.

## Traceability

```text
Issue:      P11-MNT-002
Repro:      P11/maintenance/P11-MNT-002/REPRODUCTION.md
RCA:        P11/maintenance/P11-MNT-002/ROOT_CAUSE_ANALYSIS.md
Verify:     P11/maintenance/P11-MNT-002/TARGET_VERIFICATION.md
Regression: P11/maintenance/P11-MNT-002/REGRESSION_EVIDENCE.md
Scope:      P11/maintenance/P11-MNT-002/SCOPE_AUDIT.md
Commit:     P11/maintenance/P11-MNT-002/IMPLEMENTATION_COMMIT.md
```

## Rollback

Revert the bounded implementation commit. Generated review snapshots are
read-only outputs and can be regenerated; no product data migration is needed.
