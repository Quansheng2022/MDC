# WP-P12-04-06 — Output Selection and P12-04 Closure

**Program:** MD_Converter v2.0  
**Phase:** P12-04 — GUI Foundation  
**Execution Model:** Bounded Work Package  
**Authority Level:** G1 unless a G2 trigger is hit  
**Core Semantic Change Authority:** NONE  
**Golden Change Authority:** NONE  
**Real Conversion Integration Authority:** NONE in P12-04  


## 1. Objective

Implement the minimal output-folder selection behavior and perform final verification/closure of P12-04 GUI Foundation.

This is the last P12-04 work package.

Real conversion remains deferred to P12-05.

---

## 2. Preconditions

Required closed:

```text
WP-P12-04-01
WP-P12-04-02
WP-P12-04-03
WP-P12-04-04
WP-P12-04-05
```

---

## 3. Output Policy

Default GUI presentation:

```text
Output folder: Same as source
```

The GUI may allow:

```text
[Change]
→ choose output directory
```

This WP selects an **output directory preference**.

It shall not independently invent final DOCX filename rules.

Final file naming remains the responsibility of the approved application/service behavior.

---

## 4. Authorized Scope

Implement:

- output-folder display;
- Change button;
- directory chooser;
- reset/default behavior if part of minimal UX;
- GUI-side storage of the selected output directory for the current session;
- mock request construction if useful for later P12-05 integration.

---

## 5. Boundary Rule

GUI may determine:

```text
user selected output directory
```

GUI shall not become the authority for:

```text
frontmatter title
filename sanitization
final DOCX naming
conversion overwrite semantics
```

Those belong to the application/service contract.

---

## 6. Default Behavior

If the user does not choose another output folder:

```text
Same as source
```

should be represented clearly.

Do not precompute a conflicting filename algorithm.

---

## 7. Change Folder Behavior

Using a standard directory chooser:

```text
Change
↓
Select directory
↓
display selected output directory
```

Cancel leaves previous choice unchanged.

Missing/nonexistent selections shall not create undefined state.

---

## 8. P12-04 Mock Workflow

At the end of this WP, the GUI should support the complete mock foundation workflow:

```text
Launch
↓
EMPTY
↓
Select or Drop Markdown
↓
READY
↓
Choose output directory (optional)
↓
Convert
↓
CONVERTING
↓
simulated SUCCESS / WARNING / FAILED
```

No real conversion call is allowed yet.

---

## 9. P12-04 Verification

### V1 — GUI bootstrap

```text
launch PASS
close PASS
```

### V2 — Main window

```text
required controls present
layout usable
```

### V3 — State model

```text
required transitions PASS
duplicate convert prevented
```

### V4 — File picker

```text
valid selection PASS
cancel PASS
invalid input safe
```

### V5 — Drag/drop

```text
single valid .md PASS
invalid/multiple/folder safe
```

### V6 — Output selection

```text
default same-as-source
change directory PASS
cancel safe
```

### V7 — Architecture

Verify:

```text
real ConversionService call = 0
CompilerContext call from GUI = 0
Core semantic changes = 0
Golden changes = 0
application-layer Qt imports = 0
```

### V8 — Existing regression

Run relevant existing tests sufficient to prove GUI foundation did not break:

- application layer;
- public API smoke;
- CLI smoke;
- other required regression according to current project policy.

Full regression is recommended at P12-04 closure if practical.

---

## 10. P12-04 Acceptance Criteria

All must be true:

```text
GUI launches
main workflow visible
state model works
file picker works
drag/drop works
output folder selection works
real conversion integration = 0
Core changes = 0
Golden changes = 0
application layer remains Qt-free
new required regression failures = 0
```

Then:

```text
P12-04 GUI FOUNDATION = CLOSED / ACCEPTED
```

and P12-05 may begin.

---

## 11. Explicitly Forbidden

Do not use this closure WP to add:

- Worker/QThread integration;
- real ConversionService execution;
- diagnostics dialog;
- Open Document;
- Open Folder;
- settings persistence;
- preview;
- templates;
- AI features;
- batch/folder conversion.

Those belong to later phases.

---

## 12. Mandatory Stop Conditions

Do not close P12-04 if:

- GUI directly calls Core;
- application layer now depends on Qt;
- real conversion logic was added prematurely;
- filename semantics were duplicated in GUI;
- new required regression failure exists;
- scope expanded to batch/folder/preview/editor features;
- unauthorized Core/Golden change exists.

---

## 13. Agent Final Report Template

```text
PHASE: P12-04 GUI Foundation
STATUS: PASS / BLOCKED

WP status:
- WP-P12-04-01:
- WP-P12-04-02:
- WP-P12-04-03:
- WP-P12-04-04:
- WP-P12-04-05:
- WP-P12-04-06:

Files added:
Files modified:

GUI tests:
- passed:
- failed:

Existing regression:
- passed:
- failed:
- skipped:

Real conversion calls:
Core changes:
Golden changes:
Application-layer Qt dependency:

File picker:
Drag/drop:
Output selection:
State model:

Unauthorized drift:
Open blockers:

Git SHA:
Recommended next phase:
```

---

## 14. Final Decision

If all exit criteria pass:

> **Proceed to P12-05 — GUI/Core Integration.**

If not:

> **Resolve only the specific P12-04 blocker. Do not broaden the GUI scope.**
