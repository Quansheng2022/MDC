# WP-P12-04-03 — GUI State Model

**Program:** MD_Converter v2.0  
**Phase:** P12-04 — GUI Foundation  
**Execution Model:** Bounded Work Package  
**Authority Level:** G1 unless a G2 trigger is hit  
**Core Semantic Change Authority:** NONE  
**Golden Change Authority:** NONE  
**Real Conversion Integration Authority:** NONE in P12-04  


## 1. Objective

Implement an explicit GUI state model so widget enablement, labels, and workflow transitions are centrally controlled rather than scattered across event handlers.

Real conversion is still out of scope.

---

## 2. Preconditions

Required:

```text
WP-P12-04-01 CLOSED
WP-P12-04-02 CLOSED
```

---

## 3. Required States

Implement:

```text
EMPTY
READY
CONVERTING
SUCCESS
SUCCESS_WITH_WARNING
FAILED
```

These are GUI presentation/workflow states.

They are distinct from P12-03 `ConversionResult` status semantics.

---

## 4. Minimum Transition Model

```text
EMPTY
 ↓ valid source available
READY
 ↓ Convert requested
CONVERTING
 ├── SUCCESS
 ├── SUCCESS_WITH_WARNING
 └── FAILED

SUCCESS / WARNING / FAILED
 ↓ new valid source or reset
READY
```

For P12-04, completion states may be driven by mock/simulated events only.

---

## 5. Authorized Scope

Possible implementation:

```text
md_converter/gui/state.py
```

or an equivalent small GUI module.

MainWindow may delegate to the state model/controller.

Avoid introducing a large framework.

---

## 6. Required State Effects

At minimum define behavior for:

### EMPTY

```text
Convert disabled
Select enabled
Drop enabled
```

### READY

```text
Convert enabled
source visible
```

### CONVERTING

```text
Convert disabled
duplicate start prevented
status shows converting
```

### SUCCESS

```text
status shows success
```

### SUCCESS_WITH_WARNING

```text
status shows success with warning
```

### FAILED

```text
status shows failure
```

Open Document/Open Folder behavior belongs later unless already present as inert controls.

---

## 7. Centralization Rule

Do not scatter state rules across many callbacks such as:

```python
button.setEnabled(...)
label.setText(...)
```

with contradictory conditions.

Prefer one controlled state-application path.

---

## 8. Real Conversion Boundary

This WP may use mock methods such as:

```text
simulate_success()
simulate_warning()
simulate_failure()
```

for tests only.

Do not call `ConversionService`.

---

## 9. Focused Tests

Test:

```text
initial state = EMPTY
EMPTY → READY
READY → CONVERTING
CONVERTING → SUCCESS
CONVERTING → SUCCESS_WITH_WARNING
CONVERTING → FAILED
completion → READY when new source selected
Convert disabled while CONVERTING
invalid transitions rejected or handled deterministically
```

---

## 10. Acceptance Criteria

```text
state enum/model exists
widget state derives from GUI state
duplicate convert prevented in CONVERTING
all required transitions tested
real conversion calls = 0
Core changes = 0
```

---

## 11. Mandatory Stop Conditions

STOP if:

- state implementation requires changing P12-03 result semantics;
- conversion semantics must be changed;
- GUI state becomes stored in application/Core layer;
- a large event/state framework is proposed.

---

## 12. Agent Completion Report

```text
WP: WP-P12-04-03
Status: PASS / BLOCKED

States implemented:
Transition mechanism:
Files added:
Files modified:

Tests executed:
Tests passed:
Tests failed:

Application/Core state changes: 0 / describe
Real conversion calls: 0
Stop condition triggered: YES / NO
```

---

## 13. Closure Gate

```text
WP-P12-04-03 = CLOSED
```

Proceed to `WP-P12-04-04`.
