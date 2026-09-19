# P11-MNT-002 — Regression Evidence

## Required Final Regression

```text
Command:
  .\.venv\Scripts\python.exe -m pytest -q -ra

Result:
  exit code 0
  progress reached 100%
  collected tests: 281
  failed: 0
  skipped: 0
```

The collected count is the prior 277-test baseline plus the four new focused
review-tooling tests.

## Scope

The required regression covers the full project test suite, including the new
focused review-tooling tests. No product/runtime behavior is modified by this
change package.

## Failure Policy

Any unexplained failure is a Batch A stop condition. Golden, Acceptance, and
product semantics are not to be changed to make this tooling regression pass.
