# WP-P12-05-05 — Lifecycle and Duplicate Execution Protection

**Program:** MD_Converter v2.0  
**Phase:** P12-05 — GUI/Core Integration  
**Execution Model:** Bounded Work Package  
**Authority Level:** G1 unless a G2 trigger is hit  
**P12-05 Baseline SHA:** `4356ca7ede841d50e8d255ca9dfd79365f16bec4`  
**Core Semantic Change Authority:** NONE  
**Golden Change Authority:** NONE  
**P12-06 Diagnostics UX Authority:** NONE  


## 1. Objective

Harden the real conversion lifecycle so one GUI conversion cannot launch multiple concurrent jobs or leave unsafe worker/thread state.

This is bounded lifecycle protection, not a general job-management system.

## 2. Preconditions

Required:

```text
WP-P12-05-04 CLOSED
```

## 3. Required Protections

### Duplicate Convert

While `GuiState.CONVERTING`, a second Convert activation shall not start a second worker/job.

### Source Mutation

While CONVERTING:

- File Picker cannot replace source;
- Drag & Drop cannot replace source.

### Output Mutation

While CONVERTING:

- Change Output remains disabled.

### Worker Lifetime

No overlapping active worker for the single-document workflow.

### Completion

On success/warning/failure:

- completion handled once;
- thread stops;
- active-worker reference cleared or safely transitioned;
- GUI can accept next workflow action.

## 4. Window Close During Conversion

Explicitly test and choose a bounded policy.

Preferred:

```text
A. prevent close until conversion completes
or
B. safe cooperative shutdown if already supported
```

Do not force-terminate worker threads.

If cancellation is not natively supported, prefer the simplest safe close policy.

## 5. No Job Queue

Do not introduce:

```text
job queue
multi-worker pool
parallel conversion
batch scheduler
background task manager
```

## 6. Native Lifetime Safety

Ensure tests do not create dangling Qt objects. Test helpers must retain payload/QObject lifetime for as long as Qt events require.

## 7. Focused Tests

Test:

```text
double Convert starts one job only
source cannot change while CONVERTING
output cannot change while CONVERTING
worker completes once
worker/thread cleanup verified
next conversion can start after prior completion
window-close policy deterministic and safe
no native crash in lifecycle tests
```

## 8. Acceptance Criteria

```text
duplicate execution prevented
single active job invariant holds
source/output mutation blocked during conversion
worker lifecycle cleaned
safe close behavior defined/tested
no queue/batch framework added
tests PASS
```

## 9. Mandatory Stop Conditions

STOP if:

- safe close requires force-terminating threads;
- worker leaks cannot be fixed without architecture redesign;
- reproducible native crash remains;
- lifecycle fix requires changing ConversionService/Core semantics.

## 10. Agent Completion Report

```text
WP: WP-P12-05-05
Status: PASS / BLOCKED

Files added:
Files modified:

Duplicate protection:
Single-job invariant:
Worker cleanup:
Window-close behavior:

Tests executed:
Tests passed:
Tests failed:

Native crash observed: YES / NO
Core changes:
Golden changes:
CLI behavior changes:

Stop condition triggered: YES / NO
```

## 11. Closure Gate

```text
WP-P12-05-05 = CLOSED
```

Proceed to WP-P12-05-06.
