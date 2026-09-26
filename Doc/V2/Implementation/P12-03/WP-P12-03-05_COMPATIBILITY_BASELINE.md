# WP-P12-03-05 — Compatibility Baseline

**Program:** MD_Converter v2.0  
**Phase:** P12-03 — Application Service Extraction  
**Execution Model:** Bounded Work Package  
**Authority Level:** G1 unless a G2 trigger is hit  
**Core Semantic Change Authority:** NONE  
**Golden Change Authority:** NONE  


## 1. Objective

Establish evidence that the new application service has not unintentionally changed the existing v1.1.0 externally visible file-conversion behavior.

This WP is primarily **verification and characterization**, not refactoring.

---

## 2. Why This WP Exists

P12-02 identified overlapping logic in:

```text
cli.py
CompilerContext.compile_file()
```

for:

- source reading;
- frontmatter;
- title handling;
- output path;
- filename sanitization.

The behaviors are not guaranteed to be byte-for-byte identical.

Therefore P12-03 must avoid treating code deduplication as proof of compatibility.

---

## 3. Authorized Scope

Authorized:

- add characterization/compatibility tests;
- add small test fixtures;
- document observed existing behavior;
- make minimal application-layer fixes if the service itself violates current behavior.

Not authorized:

- redesign filename policy;
- "standardize" CLI behavior;
- modify CLI for elegance;
- change frontmatter semantics;
- update Golden baseline.

---

## 4. Required Characterization Cases

At minimum inspect/test:

```text
simple source filename
title with spaces
title with Windows-forbidden/special characters
frontmatter title present
frontmatter title absent
explicit output path
default output path
nested source directory
existing output conflict behavior if already defined
UTF-8 source
```

Only include cases supported by the current product contract.

Do not invent new edge-case requirements.

---

## 5. CLI Baseline

For each relevant case, capture current CLI-observable behavior:

```text
input
CLI invocation
expected output path/name
exit behavior
diagnostic outcome where relevant
```

The purpose is to prevent P12-03 from accidentally changing established behavior.

---

## 6. Service Comparison

Where appropriate, compare:

```text
Existing supported path
vs
ConversionService
```

Focus on:

- output location;
- output naming;
- metadata/frontmatter effect;
- conversion success/failure;
- warning/error meaning.

Do not require identical log formatting.

---

## 7. Decision Rule

If differences are discovered:

### A. Service bug

If the new service deviates from an existing approved behavior:

```text
fix service
→ focused retest
```

### B. Existing path inconsistency

If two pre-existing v1.1.0 paths already behave differently:

```text
record
→ do not silently unify
→ escalate only if future product decision is required
```

This WP does not authorize resolution of legacy inconsistencies.

---

## 8. Tests

Preferred location:

```text
tests/application/test_conversion_compatibility.py
```

or integrate into existing focused service tests if project conventions favor fewer files.

Avoid duplicating the whole Acceptance Corpus.

---

## 9. Acceptance Criteria

```text
characterization completed
known behavior recorded in tests/evidence
service does not unintentionally change approved behavior
legacy inconsistencies, if any, documented rather than rewritten
CLI product code changes = 0
Canonical changes = 0
Golden changes = 0
tests PASS
```

---

## 10. Mandatory Stop Conditions

STOP if:

- compatibility requires intentional CLI behavior change;
- output naming policy requires a new product decision;
- frontmatter precedence must be changed;
- public API behavior must change;
- an existing v1.1.0 inconsistency cannot be safely preserved and blocks the service.

Report the exact conflict.

---

## 11. Agent Completion Report

```text
WP: WP-P12-03-05
Status: PASS / BLOCKED

Characterization cases:
Observed legacy differences:

Files added:
Files modified:

Compatibility tests:
Passed:
Failed:

CLI product code changed: NO / describe
Canonical changed: NO / describe
Golden changed: NO / describe

Decision required from Human/Reviewer:
Stop condition triggered: YES / NO
```

---

## 12. Closure Gate

After compatibility evidence is green:

```text
WP-P12-03-05 = CLOSED
```

Proceed to P12-03 final verification.
