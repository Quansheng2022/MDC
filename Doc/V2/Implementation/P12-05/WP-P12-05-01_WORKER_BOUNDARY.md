# WP-P12-05-01 — Worker Boundary

**Program:** MD_Converter v2.0  
**Phase:** P12-05 — GUI/Core Integration  
**Execution Model:** Bounded Work Package  
**Authority Level:** G1 unless a G2 trigger is hit  
**P12-05 Baseline SHA:** `4356ca7ede841d50e8d255ca9dfd79365f16bec4`  
**Core Semantic Change Authority:** NONE  
**Golden Change Authority:** NONE  
**P12-06 Diagnostics UX Authority:** NONE  


## 1. Objective

Introduce the minimum worker/thread boundary required to execute conversion outside the Qt GUI main thread.

This WP establishes the execution boundary only. It does **not** wire the real Convert button to a real conversion yet.

## 2. Preconditions

Required:

- P12-04 GUI Foundation is CLOSED / ACCEPTED.
- P12-04 Closure SHA is `4356ca7ede841d50e8d255ca9dfd79365f16bec4`.
- `ConversionService` from P12-03 remains the application-layer authority.
- GUI state model from P12-04 remains the workflow-state authority.

Inspect `main_window.py`, `state.py`, `conversion_service.py`, existing GUI test patterns, and any existing worker utility.

## 3. Target Boundary

```text
MainWindow
    ↓
GUI Worker / Thread Boundary
    ↓
Application Service
```

In this WP the worker may use a fake/mock callable. Real `ConversionService` execution is deferred to WP-P12-05-03.

## 4. Authorized Scope

Preferred files:

```text
md_converter/gui/worker.py
md_converter/tests/gui/test_worker.py
```

Small changes to `main_window.py` are allowed only if needed to host/invoke the worker seam.

## 5. Worker Responsibilities

The worker shall support:

- accepting one callable/job;
- executing it outside the GUI main thread;
- delivering success result back to GUI thread;
- delivering failure/exception evidence back to GUI thread;
- deterministic completion signal;
- safe cleanup of worker/thread objects.

The worker shall not know Markdown semantics, parser, renderer, QA, filename, frontmatter, or DOCX logic.

## 6. Threading Rule

Prove:

```text
GUI thread id != worker execution thread id
```

using a deterministic test seam.

## 7. Error Transport

Transport raw/structured failure evidence only. Do not create final error UX or message boxes.

## 8. Lifecycle Rule

Ensure:

- one job starts once;
- completion occurs once;
- thread exits;
- worker/thread references are cleaned or safely reusable;
- app shutdown is not blocked by orphaned worker threads.

## 9. Explicitly Forbidden

Not authorized:

- real `ConversionService` wiring;
- real Markdown conversion;
- direct `CompilerContext` use in GUI;
- diagnostics UI;
- retry framework;
- queue/multi-job framework;
- parallel batch conversion;
- broad MainWindow refactor.

## 10. Focused Tests

Test:

```text
worker executes outside GUI thread
success payload delivered
failure payload delivered
completion emitted exactly once
thread stops after completion
no GUI widget accessed from worker thread
second start behavior deterministic
```

## 11. Acceptance Criteria

```text
worker boundary exists
worker execution is off main GUI thread
success/failure transport works
lifecycle cleanup works
real ConversionService calls = 0
Core calls from worker = 0
GUI tests PASS
Core/Golden/CLI changes = 0
```

## 12. Mandatory Stop Conditions

STOP if:

- `ConversionService` semantics must change;
- GUI must call `CompilerContext` directly;
- application layer must import Qt;
- worker architecture expands into queue/batch/executor framework;
- safe lifecycle requires broad architecture change.

## 13. Agent Completion Report

```text
WP: WP-P12-05-01
Status: PASS / BLOCKED

Files added:
Files modified:

Worker design:
Thread mechanism:
Success transport:
Failure transport:
Cleanup behavior:

Tests executed:
Tests passed:
Tests failed:

Real ConversionService calls:
Application-layer Qt dependency:
Core changes:
Golden changes:
CLI behavior changes:

Stop condition triggered: YES / NO
```

## 14. Closure Gate

```text
WP-P12-05-01 = CLOSED
```

Proceed to WP-P12-05-02.
