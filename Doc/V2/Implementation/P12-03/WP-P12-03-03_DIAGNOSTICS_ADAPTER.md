# WP-P12-03-03 — DiagnosticsAdapter

**Program:** MD_Converter v2.0  
**Phase:** P12-03 — Application Service Extraction  
**Execution Model:** Bounded Work Package  
**Authority Level:** G1 unless a G2 trigger is hit  
**Core Semantic Change Authority:** NONE  
**Golden Change Authority:** NONE  


## 1. Objective

Introduce a thin `DiagnosticsAdapter` that transforms existing diagnostic/QA evidence into an application-facing representation suitable for future CLI/GUI display.

It shall **adapt existing evidence**, not create a second QA system.

---

## 2. Preconditions

Required:

- WP-P12-03-01 closed;
- WP-P12-03-02 closed.

Inspect current:

- `DiagnosticCollector`;
- diagnostic severity model;
- current warning/error codes/messages;
- `CompilerContext.get_quality_gate_report()` or equivalent;
- StaticQA / RenderedQA / FinalArtifactQA / PostProcessor result surfaces;
- existing COM availability warning path.

---

## 3. Authorized Scope

Authorized:

```text
md_converter/application/diagnostics_adapter.py
tests/application/test_diagnostics_adapter.py
minimal application exports
```

---

## 4. Responsibilities

The adapter may:

- obtain error/warning counts;
- normalize diagnostic records into plain application structures;
- produce concise summaries;
- map known diagnostic information to user-display-safe text;
- preserve diagnostic code/severity/detail;
- attach quality-gate report data where already available.

Example conceptual flow:

```text
DiagnosticCollector
Quality Gate Evidence
PostProcessor Evidence
        ↓
DiagnosticsAdapter
        ↓
Application Diagnostic Summary
```

---

## 5. User vs Technical Information

The adapter should support two conceptual layers:

### User-facing

Example:

```text
Word post-processing was unavailable.
The document was generated with limited post-processing.
```

### Technical

Example:

```text
diagnostic_code
severity
stage
internal message
exception detail
```

The technical layer must not be silently destroyed.

---

## 6. No New QA Semantics

Forbidden:

```text
Document Quality Score = 87
Visual Quality Score
new pass/fail scoring rules
new renderer validation
new canonical checks
```

unless separately authorized.

Existing QA is authoritative.

---

## 7. Exception Handling Rule

The adapter must not use broad exception swallowing to hide failures.

Forbidden pattern:

```python
try:
    ...
except Exception:
    return "Something went wrong"
```

without retaining technical evidence.

If defensive handling is required, technical detail must remain available.

---

## 8. Focused Tests

Recommended:

```text
zero diagnostics
warnings only
errors present
mixed severity
diagnostic code retained
summary counts correct
technical detail retained
quality-gate report passed through/normalized where applicable
known COM-warning mapping where evidence exists
```

Do not add heavy integration conversion tests yet.

---

## 9. Acceptance Criteria

```text
DiagnosticsAdapter exists
uses existing diagnostics
does not redefine QA
user summary available
technical evidence preserved
focused tests PASS
Golden changed = 0
```

---

## 10. Mandatory Stop Conditions

STOP if implementation requires:

- modifying DiagnosticCollector semantics;
- changing severity authority;
- changing QA policy;
- modifying PostProcessor behavior;
- changing Canonical output;
- introducing a new QA/scoring framework.

---

## 11. Agent Completion Report

```text
WP: WP-P12-03-03
Status: PASS / BLOCKED

Files added:
Files modified:

Existing diagnostic sources used:
Mappings introduced:

Tests executed:
Tests passed:
Tests failed:

QA semantic changes: 0 / describe
Golden changes: 0 / describe
Stop condition triggered: YES / NO
```

---

## 12. Closure Gate

After focused tests pass:

```text
WP-P12-03-03 = CLOSED
```

Proceed to `WP-P12-03-04`.
