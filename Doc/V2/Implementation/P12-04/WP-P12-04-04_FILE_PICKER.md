# WP-P12-04-04 — Markdown File Picker

**Program:** MD_Converter v2.0  
**Phase:** P12-04 — GUI Foundation  
**Execution Model:** Bounded Work Package  
**Authority Level:** G1 unless a G2 trigger is hit  
**Core Semantic Change Authority:** NONE  
**Golden Change Authority:** NONE  
**Real Conversion Integration Authority:** NONE in P12-04  


## 1. Objective

Implement user-driven Markdown file selection through a standard desktop file dialog.

Selecting a valid file shall move the GUI from EMPTY to READY.

Real conversion remains out of scope.

---

## 2. Preconditions

Required:

```text
WP-P12-04-01 CLOSED
WP-P12-04-02 CLOSED
WP-P12-04-03 CLOSED
```

---

## 3. Authorized Scope

Implement:

- Select File button behavior;
- native/standard Qt file dialog;
- selected-source display;
- source validation appropriate to GUI boundary;
- state transition to READY.

---

## 4. Supported Selection

Normal file filter should prioritize:

```text
Markdown Files (*.md)
```

Do not invent support for other formats.

If the current product officially supports additional Markdown extensions, use the existing contract rather than guessing.

---

## 5. Cancel Behavior

If the user cancels:

```text
current valid selection preserved
or
state remains unchanged
```

Do not convert cancel into an error.

---

## 6. Invalid Selection

If the selected path is:

- missing;
- not a file;
- unsupported by current product contract;

then:

```text
conversion must not become enabled
state must not incorrectly become READY
user receives concise feedback where appropriate
```

Do not create the final P12-06 error framework here.

---

## 7. Source Display

The GUI should show the selected file clearly.

For long paths, use a reasonable display strategy:

- elision;
- tooltip;
- secondary path label;

without hiding the actual selected source internally.

---

## 8. Boundary Rule

The file picker determines **which file the user selected**.

It does not:

- parse frontmatter;
- compute DOCX content;
- inspect AST;
- call Core;
- call `ConversionService`.

---

## 9. Focused Tests

Test at least:

```text
select valid .md
cancel picker
select missing/invalid path via test seam where practical
selected file displayed
state EMPTY → READY
Convert enabled in READY
re-select new valid file updates source
```

Use mocking/monkeypatching for dialogs where appropriate.

---

## 10. Acceptance Criteria

```text
Select File works
valid Markdown enters READY
cancel safe
invalid input does not enter READY
no conversion invoked
focused tests PASS
```

---

## 11. Mandatory Stop Conditions

STOP if implementation requires:

- changing supported source semantics;
- modifying application service validation contract materially;
- adding new source formats;
- direct compiler calls.

---

## 12. Agent Completion Report

```text
WP: WP-P12-04-04
Status: PASS / BLOCKED

Files added:
Files modified:

File dialog filter:
Validation behavior:
State behavior:

Tests executed:
Tests passed:
Tests failed:

New format support added: NO
Conversion invoked: NO
Stop condition triggered: YES / NO
```

---

## 13. Closure Gate

```text
WP-P12-04-04 = CLOSED
```

Proceed to `WP-P12-04-05`.
