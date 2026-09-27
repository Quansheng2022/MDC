# WP-P12-09-01 — Verification Baseline

**Product Baseline:** `38614c7`  
**Authority:** verification planning only

## Objective

Freeze the verification matrix and release-candidate identity before execution.

## Required Inputs

Inspect:

- P12-08 closure evidence and WP evidence;
- V2 Product Specification;
- V2 Architecture;
- V2 GUI/UX Specification;
- V2 Acceptance Criteria;
- current regression inventory;
- Golden/Acceptance tests;
- final installer artifact;
- final packaged executable;
- known accepted exceptions.

## Required Outputs

Record:

- candidate installer path and SHA-256;
- packaged executable path/hash where authoritative;
- product version;
- target Windows environment;
- Word availability;
- verification matrix;
- accepted pre-existing failures;
- release-blocker criteria.

## Verification Matrix

Map requirements to one of:

```text
automated source test
packaged-app smoke
installed-app smoke
manual/visual Windows check
artifact/static inspection
prior evidence reused
```

Avoid broad test execution in this WP.

## Rules

Do not modify production code.
Do not start broad verification until candidate identity is frozen.

## Acceptance

```text
candidate identity frozen
verification matrix complete
known exceptions explicit
environment recorded
release-blocker policy explicit
```
