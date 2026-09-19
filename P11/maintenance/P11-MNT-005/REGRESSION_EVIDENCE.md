# P11-MNT-005 — Regression Evidence

## Required Full Regression

```text
Command:
  .\.venv\Scripts\python.exe -m pytest -q -ra

Result:
  exit code 0
  progress 100%
  collected 292
  failed 0
  unexpected skip 0
  new regression 0
```

## Count Basis

```text
Post-recovery baseline: 290 tests
New focused tests:        2 tests
Collected total:          292 tests
```

The count was not assumed; it was confirmed by the actual full regression and
by `pytest --collect-only -q`.

## Environment Note

The full regression ran as the single regression cycle required by the plan.
It was not rerun after M13 because no product, test, or dependency code changed
after the regression.

## Post-Commit Strict Gate

After the implementation commit, the maintenance merger is run in strict mode
without `--run-pytest`. Clean-tree, strict-result, nesting, and `py.typed`
checks are recorded in the P11-MNT-005 final report.
