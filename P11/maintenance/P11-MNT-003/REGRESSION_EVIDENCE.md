# P11-MNT-003 — Regression Evidence

## Required Final Regression

```text
Command:
  .\.venv\Scripts\python.exe
      tools/review/merge_project_for_phase11_review.py
      --mode maintenance
      --run-pytest
      --strict
      --output <outside PROJECT_ROOT>
```

## Expected Test Scope

```text
Baseline full regression: 281 tests
New focused tests:         3 tests
Expected collected total:  284 tests
```

## Result

The strict gate is executed once on the clean implementation commit. Its result
is recorded in the Batch B final report:

```text
failed=0
unexpected skip=0
new regression=0
strict=PASS
```

## Failure Policy

Any unexplained failure or unexpected skip is a Batch B stop condition. Golden,
Acceptance, Canonical, Architecture, and product semantics must not be changed
to make this tooling/behavior regression pass.
