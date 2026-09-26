# WP-P12-05-03 — Real Conversion Vertical Slice

**Program:** MD_Converter v2.0  
**Phase:** P12-05 — GUI/Core Integration  
**Execution Model:** Bounded Work Package  
**Authority Level:** G1 unless a G2 trigger is hit  
**P12-05 Baseline SHA:** `4356ca7ede841d50e8d255ca9dfd79365f16bec4`  
**Core Semantic Change Authority:** NONE  
**Golden Change Authority:** NONE  
**P12-06 Diagnostics UX Authority:** NONE  


## 1. Objective

Wire one complete real conversion path:

```text
MainWindow
→ Worker
→ ConversionService
→ Canonical Core
→ ConversionResult
→ GUI
```

This is the first WP in which real conversion is authorized.

## 2. Preconditions

Required:

```text
WP-P12-05-01 CLOSED
WP-P12-05-02 CLOSED
```

Inspect the actual P12-03 `ConversionService` API and current worker seam.

## 3. Required Flow

```text
READY
↓ Convert
CONVERTING
↓
build ConversionRequest
↓
submit worker job
↓
ConversionService.convert(request)
↓
ConversionResult returned
↓
result delivered to GUI thread
```

Detailed result-to-state mapping is finalized in WP-P12-05-04.

## 4. Threading Requirement

`ConversionService.convert()` must run outside the GUI main thread.

GUI widgets shall only be accessed/updated on the GUI thread.

## 5. Application Boundary

GUI may import application-layer types:

```text
ConversionService
ConversionRequest
ConversionResult
```

GUI shall not import `CompilerContext`, parser, AST, pipeline, renderer, or QA internals.

## 6. Service Lifetime

Use the simplest safe lifetime: per-conversion or retained stateless service. Do not create global mutable service state without evidence.

## 7. Real Conversion Test

Use a deterministic Markdown fixture:

```text
valid .md
→ Convert
→ worker executes
→ DOCX produced
→ GUI receives completion
```

Verify event processing remains responsive, worker thread differs from GUI thread, output exists, service is the only conversion entry, and no direct Core call exists in GUI.

## 8. Failure Slice

Test one deterministic failure:

```text
request/service failure
→ worker returns failure/result
→ GUI leaves CONVERTING
```

Do not build final error UX.

## 9. Explicitly Forbidden

Not authorized:

- direct GUI → `CompilerContext`;
- bypassing `ConversionService`;
- duplicating conversion logic;
- diagnostics dialog;
- Open Document/Open Folder;
- automatic retry;
- batch conversion;
- cancellation system unless required for safe shutdown;
- packaging changes.

## 10. Focused Tests

Test:

```text
real conversion completes through worker
ConversionService called exactly once
worker thread != GUI thread
DOCX exists
GUI leaves CONVERTING
deterministic service failure leaves CONVERTING
no direct Core imports/calls in GUI
```

Existing P12-03 application tests must remain green.

## 11. Acceptance Criteria

```text
GUI → Worker → ConversionService works
real DOCX produced
main thread does not execute conversion
GUI returns from CONVERTING
direct Core calls from GUI = 0
P12-03 application semantics unchanged
tests PASS
Golden changes = 0
```

## 12. Mandatory Stop Conditions

STOP if:

- GUI must call Core directly;
- ConversionService needs semantic modification for GUI;
- worker cannot safely deliver result;
- real conversion changes Golden/Canonical output;
- threading exposes a reproducible native crash or unsafe object-lifetime issue.

## 13. Agent Completion Report

```text
WP: WP-P12-05-03
Status: PASS / BLOCKED

Files added:
Files modified:

Real conversion path:
Worker thread evidence:
ConversionService call count:
Output artifact:

Success flow:
Failure flow:

Tests executed:
Tests passed:
Tests failed:

Direct Core calls from GUI:
Core semantic changes:
Golden changes:
CLI behavior changes:

Stop condition triggered: YES / NO
```

## 14. Closure Gate

```text
WP-P12-05-03 = CLOSED
```

Proceed to WP-P12-05-04.
