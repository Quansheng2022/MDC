# P11-MNT-004 — Regression Evidence

## Required Final Regression

```text
Command:
  .\.venv\Scripts\python.exe -m pytest -q -ra

Result:
  exit code 0
  progress 100%
  collected tests 289
  failed 0
  unexpected skip 0
  new regression 0
```

## Test Count Basis

```text
Pre-Batch-C baseline: 284 tests
New focused tests:     5 tests
Collected total:       289 tests
```

## Failure Policy

Any unexplained failure or unexpected skip is a Batch C stop condition. Golden,
Acceptance, Canonical, Architecture, and unrelated product semantics must not
be changed to make this regression pass.

## Post-Commit Strict Gate

After the implementation commit, the maintenance merger is run in strict mode
without `--run-pytest`; the full regression has already passed once. The strict
result and clean-tree/nesting observations are recorded in the Batch C final
report.
