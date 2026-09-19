# P11-MNT-002 — Issue Intake

## Artifact Header

| Field | Value |
| --- | --- |
| ID | P11-MNT-002 |
| Title | Generated Review Snapshot Nesting |
| Source | Human-authorized Batch A; Roadmap item 27 |
| Classification | DEFECT |
| Severity | P3 |
| Affected Version | v1.0.x maintenance tooling |
| Component | `tools/review/merge_project_for_phase11_review.py` |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0 §8 / §20 / §21 |
| Canonical References | `SPEC-GOAL-003` (determinism), `SPEC-GOAL-006` (auditability) |
| Status | VERIFIED / AWAITING REVIEW |

## Problem

The Phase 11 maintenance merger could include previously generated review
snapshots in a new snapshot. Generated filenames contain governance words such
as `maintenance` and `review`, so the maintenance inclusion policy selected
them as if they were source/governance files.

## Impact

- Review snapshots grow recursively as Snapshots A and B embed each other.
- Review evidence is polluted by stale generated content.
- The merged artifact is not reproducible in scope across consecutive runs.
- No product/runtime or Canonical behavior is affected.

## Classification Rationale

This is a bounded tooling defect in the review infrastructure. It is not a
product defect, not a Canonical specification gap, and not an architecture
change. The fix is limited to review-tool inclusion policy and focused tests.

## Required Outcome

1. Generated review snapshots are never embedded into later snapshots.
2. The maintenance collector includes `md_converter/py.typed`.
3. Approved maintenance profile/test collection behavior is preserved.

## Stop Conditions Checked

- Product/core code: not required.
- Canonical / Architecture / Acceptance: not required.
- Dependency change: not required.
- P12 or release authority: not required.
