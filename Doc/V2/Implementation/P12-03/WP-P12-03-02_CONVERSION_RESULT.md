# WP-P12-03-02 — ConversionResult

**Program:** MD_Converter v2.0  
**Phase:** P12-03 — Application Service Extraction  
**Execution Model:** Bounded Work Package  
**Authority Level:** G1 unless a G2 trigger is hit  
**Core Semantic Change Authority:** NONE  
**Golden Change Authority:** NONE  


## 1. Objective

Introduce a normalized application-layer result model named `ConversionResult`.

It shall represent the outcome of one conversion in a form suitable for future CLI/GUI consumption without exposing UI concerns.

This WP does not implement `ConversionService`.

---

## 2. Preconditions

Required:

- `WP-P12-03-01` closed;
- `ConversionRequest` available;
- current diagnostic and QA result surfaces inspected.

Inspect current:

- `DiagnosticCollector`;
- warning/error accessors;
- quality-gate report;
- output path/result behavior;
- exception behavior.

---

## 3. Authorized Scope

Authorized:

```text
md_converter/application/conversion_result.py
tests/application/test_conversion_result.py
minimal exports
```

---

## 4. Required Result States

Define one application-level conversion status representation.

Preferred values:

```text
SUCCESS
SUCCESS_WITH_WARNING
FAILED
```

Do not mix in GUI-only states:

```text
EMPTY
READY
CONVERTING
```

Those belong to the GUI state model.

---

## 5. Proposed Fields

Candidate fields:

```text
status
source_path
output_path

warnings
errors
diagnostics
diagnostic_summary

quality_gate_report

error_category
error_message
technical_detail
```

Not every field must be mandatory.

Prefer a stable, minimal representation over a broad speculative schema.

---

## 6. Semantics

### SUCCESS

Use when conversion completed and no user-relevant warning is present.

### SUCCESS_WITH_WARNING

Use when output was generated successfully but one or more non-fatal warnings should be surfaced.

### FAILED

Use when the requested output was not successfully produced according to existing product semantics.

Do not redefine existing fail-closed behavior.

---

## 7. Design Rules

`ConversionResult` shall:

- not depend on Qt;
- not contain QWidget/QDialog objects;
- not contain renderer/parser instances;
- preserve useful diagnostics;
- support plain-language presentation later;
- keep technical detail available for support/debugging;
- avoid silently discarding error evidence.

---

## 8. Explicitly Forbidden

Not authorized:

- creating GUI dialogs;
- changing core exception policy;
- changing severity semantics;
- changing QA rules;
- suppressing existing failures to produce `SUCCESS`;
- converting warnings into failures without existing authority;
- Golden changes;
- core refactor.

---

## 9. Focused Tests

Recommended:

```text
SUCCESS result
SUCCESS_WITH_WARNING result
FAILED result
result with output path
failed result without output path
diagnostics retained
technical detail retained
basic serialization/repr behavior if project conventions use it
```

---

## 10. Acceptance Criteria

```text
ConversionResult exists
status semantics are explicit
no GUI dependency
focused tests PASS
Canonical semantics changed = 0
Golden changed = 0
```

---

## 11. Mandatory Stop Conditions

STOP if defining the result model appears to require:

- changing current warning/error meaning;
- weakening fail-closed behavior;
- changing QA authority;
- changing conversion success semantics;
- changing CLI exit semantics.

---

## 12. Agent Completion Report

```text
WP: WP-P12-03-02
Status: PASS / BLOCKED

Files added:
Files modified:

Result states implemented:
Fields implemented:

Tests executed:
Tests passed:
Tests failed:

Semantic changes: 0 / describe
Golden changes: 0 / describe
Stop condition triggered: YES / NO
```

---

## 13. Closure Gate

After focused tests pass:

```text
WP-P12-03-02 = CLOSED
```

Proceed to `WP-P12-03-03`.
