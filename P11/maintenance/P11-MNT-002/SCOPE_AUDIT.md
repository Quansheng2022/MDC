# P11-MNT-002 — Scope Audit

## Allowed Scope Audit

```text
tooling/review implementation:
  tools/review/merge_project_for_phase11_review.py
  tools/review/collect_project_for_review.py

focused tests:
  md_converter/tests/test_review_tooling.py

governance:
  P11/P11_MAINTENANCE_REGISTRY.md
  P11/maintenance/P11-MNT-002/**
```

## Forbidden Scope Audit

```text
md_converter product/runtime code:   no changes
CANONICAL_SPEC.md:                   no changes
frozen architecture:                 no changes
Acceptance / Golden semantics:       no changes
dependencies:                        no changes
P11-MNT-003/004/005:                 not implemented
release / PLAN_C:                    not started
broad refactoring:                   not performed
new governance framework:            not introduced
```

## Pre-Existing Untracked Artifacts

The following pre-existing untracked artifacts were present before this batch
and were not modified:

```text
Review_Bundle/
collect_project_for_review.py
```

The tracked collector is the bounded tooling copy under
`tools/review/collect_project_for_review.py`.

## Pre-Existing Lint Debt

The copied/review tool scripts contain pre-existing Ruff findings unrelated to
this batch (import ordering, `B023`, `F401`, and `E501`). This batch does not
perform broad refactoring; the new focused test file is Ruff-clean.
