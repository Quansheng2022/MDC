# P11-RECOVERY-PYTYPED — Review Evidence Recovery

## Context

| Field | Value |
| --- | --- |
| Plan ID | P11-RECOVERY-PYTYPED-AND-MNT004-CLOSURE |
| Related Package | P11-MNT-004 |
| Classification | Ancillary review-evidence integrity recovery |
| Date | 2026-09-19 |
| Package State | VERIFIED / AWAITING HUMAN CLOSURE |

## Confirmed Root Cause

```text
md_converter/py.typed:
  present and tracked

tools/review/collect_project_for_review.py:
  TEXT_EXTENSIONS includes ".typed"
  collector maintenance bundle includes md_converter/py.typed

tools/review/merge_project_for_phase11_review.py:
  separate TEXT_EXTENSIONS omitted ".typed"
  strict maintenance snapshot omitted md_converter/py.typed
```

## Pre-Fix Evidence

```text
Strict snapshot:
  merged_MDC_phase11_maintenance_review.txt

FILE: md_converter/py.typed count: 0
total FILE headers:              195
```

Collector bundle and manifest already included `md_converter/py.typed`.

## Recovery Patch

```text
tools/review/merge_project_for_phase11_review.py

TEXT_EXTENSIONS += ".typed"
```

No collector change. No product runtime change. No dependency change.

## Focused Verification

```text
py_compile changed tool/test: PASS

pytest md_converter/tests/test_review_tooling.py -q -ra:
  5 passed

Ruff changed files:
  merger: 8 pre-existing findings (I001 / F401 / E501)
  new focused test: no new finding
  pre-existing lint debt reported, not cleaned
```

## Regression Evidence Retained

```text
P11-MNT-004 implementation SHA:
  17b74e13ad5599f08dbdeddf9486c7ac74be4dcc

Product regression:
  289/289 PASS

Product code / tests / dependencies:
  unchanged by this recovery
```

## Post-Commit Strict Verification

The post-commit strict maintenance snapshot is generated outside
`PROJECT_ROOT` without `--run-pytest`. The resulting
`FILE: md_converter/py.typed` count, strict result, clean-tree state, and
nesting count are recorded in the P11-RECOVERY-PYTYPED final report.
