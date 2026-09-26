# WP-P12-03-04 — ConversionService

**Program:** MD_Converter v2.0  
**Phase:** P12-03 — Application Service Extraction  
**Execution Model:** Bounded Work Package  
**Authority Level:** G1 unless a G2 trigger is hit  
**Core Semantic Change Authority:** NONE  
**Golden Change Authority:** NONE  


## 1. Objective

Implement the first usable `ConversionService`.

The service shall accept one `ConversionRequest`, invoke the existing canonical conversion path, and return one `ConversionResult`.

This is the primary implementation package of P12-03.

---

## 2. Preconditions

Required:

```text
WP-P12-03-01 CLOSED
WP-P12-03-02 CLOSED
WP-P12-03-03 CLOSED
```

Before modification, inspect the exact current implementations of:

- `CompilerContext.create()`;
- `CompilerContext.compile()`;
- `CompilerContext.compile_file()`;
- public `compile_file()` helper if present;
- public `convert()` path;
- CLI file/frontmatter/output logic.

---

## 3. Target Flow

```text
ConversionRequest
       ↓
ConversionService.convert()
       ↓
application validation
       ↓
existing config resolution
       ↓
existing canonical compiler path
       ↓
existing diagnostics / QA
       ↓
DiagnosticsAdapter
       ↓
ConversionResult
```

---

## 4. Authorized Scope

Preferred files:

```text
md_converter/application/conversion_service.py
tests/application/test_conversion_service.py
```

Minimal related application exports are allowed.

Modification to `cli.py`, `CompilerContext.compile()`, parser, renderer, QA, or Golden is **not authorized in this WP**.

---

## 5. Service Responsibilities

The first service implementation may:

1. accept a `ConversionRequest`;
2. perform safe application-level validation;
3. resolve source/output paths using existing approved behavior;
4. resolve approved config inputs;
5. construct/use the existing compiler context;
6. execute one conversion;
7. collect diagnostics/quality evidence;
8. classify outcome as SUCCESS / SUCCESS_WITH_WARNING / FAILED;
9. return `ConversionResult`.

---

## 6. Critical Compatibility Rule

The service shall not invent a new filename/output policy.

P12-02 found overlap between CLI file handling and `CompilerContext.compile_file()`, including differences in filename sanitization.

Therefore:

> The initial service must preserve current approved behavior rather than "cleaning up" or unifying naming rules.

If exact preservation requires selecting one existing canonical helper, document that choice.

If there is ambiguity, STOP instead of silently changing behavior.

---

## 7. Frontmatter Rule

Reuse existing frontmatter behavior.

Do not introduce:

- new YAML keys;
- new metadata semantics;
- new title priority;
- new default naming policy.

---

## 8. Error Policy

The service may translate bounded application-facing failures into `ConversionResult`.

It must not weaken existing fail-closed behavior.

If the existing core deliberately raises a blocking exception, the service must preserve that meaning.

Allowed:

```text
core failure
→ capture evidence
→ FAILED ConversionResult
```

only where doing so does not alter existing required semantics for the caller.

If this is ambiguous, STOP and report.

---

## 9. No GUI Dependency

`conversion_service.py` shall import no PySide6/Qt GUI module.

This must remain true so CLI, tests, and future non-GUI callers can use the service.

---

## 10. Focused Integration Tests

At minimum:

### Case A — Basic success

```text
simple valid Markdown
→ service.convert()
→ DOCX exists
→ SUCCESS
```

### Case B — Output path

```text
explicit output
→ expected DOCX location
```

### Case C — Default output

Verify current approved behavior without inventing a new convention.

### Case D — Warning

Where a deterministic warning fixture exists:

```text
output created
warning present
→ SUCCESS_WITH_WARNING
```

Do not manufacture environment-dependent tests if they are unstable.

### Case E — Failure

Use a deterministic application/core failure condition that does not require changing product behavior.

Verify:

```text
FAILED
technical evidence retained
```

---

## 11. Required Regression After Focused Tests

After focused service tests:

```text
existing public API focused tests
existing compiler/config focused tests
existing relevant quality-gate tests
```

Full required regression is reserved for WP-P12-03-06 unless current project policy mandates earlier full regression.

---

## 12. Explicitly Forbidden

Not authorized:

- modify `CompilerContext.compile()` behavior;
- change parser/AST/pipeline;
- change renderer;
- change PostProcessor semantics;
- change QA;
- change Golden;
- change CLI;
- add GUI;
- refactor broad core code;
- change output naming policy.

---

## 13. Acceptance Criteria

```text
ConversionService exists
one-file conversion succeeds through existing core
ConversionResult returned
diagnostics retained
no Qt dependency
no core semantic changes
no Golden changes
focused integration tests PASS
```

---

## 14. Mandatory Stop Conditions

STOP if:

- service cannot be implemented without modifying canonical conversion semantics;
- filename behavior cannot be preserved without a product decision;
- CLI/public API contract would necessarily change;
- core exception/fail-closed behavior would be weakened;
- application service requires renderer/parser changes;
- Golden update appears necessary.

---

## 15. Agent Completion Report

```text
WP: WP-P12-03-04
Status: PASS / BLOCKED

Files added:
Files modified:

Canonical conversion entry used:
Output-path behavior used:
Frontmatter behavior used:

Focused tests:
Regression subset:

Core semantic changes: 0 / describe
CLI changes: 0 / describe
Golden changes: 0 / describe

Out-of-scope issues:
Stop condition triggered: YES / NO
```

---

## 16. Closure Gate

Only after service conversion and focused tests pass:

```text
WP-P12-03-04 = CLOSED
```

Proceed to compatibility-baseline work.
