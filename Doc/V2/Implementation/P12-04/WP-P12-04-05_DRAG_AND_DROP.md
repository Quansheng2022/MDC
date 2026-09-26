# WP-P12-04-05 — Drag and Drop

**Program:** MD_Converter v2.0  
**Phase:** P12-04 — GUI Foundation  
**Execution Model:** Bounded Work Package  
**Authority Level:** G1 unless a G2 trigger is hit  
**Core Semantic Change Authority:** NONE  
**Golden Change Authority:** NONE  
**Real Conversion Integration Authority:** NONE in P12-04  


## 1. Objective

Implement single-file drag-and-drop for supported Markdown input.

A valid dropped Markdown file shall use the same source-selection/state path as the File Picker.

---

## 2. Preconditions

Required:

```text
WP-P12-04-01 CLOSED
WP-P12-04-02 CLOSED
WP-P12-04-03 CLOSED
WP-P12-04-04 CLOSED
```

File picker/source-selection logic should already exist and should be reused.

---

## 3. Authorized Scope

Implement:

- drag-enter acceptance;
- drag-over visual feedback where simple;
- drop handling;
- validation/reuse of existing source-selection path.

---

## 4. Single Source of Selection Logic

Do not implement separate validation rules for picker and drag/drop.

Preferred:

```text
File Picker ─┐
             ├→ set_source_file(path)
Drag & Drop ─┘
```

The shared method/controller applies:

- validation;
- selected-source display;
- state transition.

---

## 5. Required Drop Behavior

### Valid single Markdown file

```text
drop
→ accepted
→ source selected
→ READY
```

### Unsupported file

```text
drop
→ rejected
→ current valid source/state preserved where appropriate
```

### Folder

For v2.0 P12-04:

```text
reject
```

unless folder input is already explicitly authorized elsewhere.

### Multiple files

For P12-04:

```text
reject or deterministically accept only if product spec explicitly authorizes
```

Default recommendation:

> reject multiple files with concise feedback.

Do not silently choose the first file.

### Drop during CONVERTING

Must not alter active conversion state.

For P12-04 mock state testing:

```text
drop ignored/rejected while CONVERTING
```

---

## 6. Visual Feedback

Simple visual feedback is allowed, such as:

- border/highlight;
- text change;
- cursor acceptance.

Do not build a custom animation system.

---

## 7. Explicitly Forbidden

Not authorized:

- folder conversion;
- multiple-file batch conversion;
- recursive drop;
- project import;
- real conversion;
- Core calls.

---

## 8. Focused Tests

Test:

```text
valid single .md accepted
unsupported file rejected
folder rejected
multiple files rejected
drop enters READY
picker and drop use same selection logic
drop during CONVERTING does not corrupt state
```

---

## 9. Acceptance Criteria

```text
valid drag/drop works
source-selection logic shared
invalid drops safe
multiple files not silently accepted
folder not silently accepted
CONVERTING state protected
real conversion invoked = 0
```

---

## 10. Mandatory Stop Conditions

STOP if:

- drag/drop implementation starts expanding into batch/folder support;
- separate source semantics are created;
- Core/Application semantics must be changed;
- GUI framework architecture must be redesigned.

---

## 11. Agent Completion Report

```text
WP: WP-P12-04-05
Status: PASS / BLOCKED

Files added:
Files modified:

Shared source-selection path:
Drop cases implemented:

Tests executed:
Tests passed:
Tests failed:

Batch support added: NO
Folder support added: NO
Conversion invoked: NO
Stop condition triggered: YES / NO
```

---

## 12. Closure Gate

```text
WP-P12-04-05 = CLOSED
```

Proceed to `WP-P12-04-06`.
