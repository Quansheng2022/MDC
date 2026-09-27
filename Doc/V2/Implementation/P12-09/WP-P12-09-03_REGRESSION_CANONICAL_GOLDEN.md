# WP-P12-09-03 — Regression / Canonical / Golden

**Product Baseline:** `38614c7`

## Objective

Prove packaging/productization did not change accepted source behavior or canonical document semantics.

## Required Verification

Run once:

- full source regression;
- GUI suite;
- Application suite;
- public API / CLI regression;
- config/QA regression;
- Canonical tests;
- Golden/Acceptance tests.

## Failure Classification

Every failure must be classified:

```text
NEW / INTRODUCED
PRE-EXISTING / APPROVED
ENVIRONMENTAL / HARNESS
INCONCLUSIVE
```

Do not call a failure pre-existing without evidence.

## Required Drift Assertions

```text
Core semantic drift = 0
Canonical drift = 0
QA semantic drift = 0
Golden drift = 0
ConversionService semantic drift = 0
CLI/public API breaking drift = 0
```

The two previously accepted README-content/packaging-metadata failures may remain only if unchanged.

## Acceptance

```text
introduced required regression failures = 0
approved exceptions unchanged
Canonical/Golden drift = 0
public contract drift = 0
```
