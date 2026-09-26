# WP-P12-04-02 — Main Window Foundation

**Program:** MD_Converter v2.0  
**Phase:** P12-04 — GUI Foundation  
**Execution Model:** Bounded Work Package  
**Authority Level:** G1 unless a G2 trigger is hit  
**Core Semantic Change Authority:** NONE  
**Golden Change Authority:** NONE  
**Real Conversion Integration Authority:** NONE in P12-04  


## 1. Objective

Implement the minimal v2.0 main window layout for the non-technical desktop workflow.

This WP creates the visible shell only.

Real conversion remains out of scope.

---

## 2. Preconditions

Required:

```text
WP-P12-04-01 CLOSED
```

Inspect `V2_GUI_UX_SPEC.md` before implementation.

---

## 3. Authorized Scope

Primary target:

```text
md_converter/gui/main_window.py
```

Small supporting GUI-only widgets/modules may be added if they reduce complexity.

Do not create a large widget framework.

---

## 4. Required UI Elements

The initial main window shall contain conceptually:

```text
┌──────────────────────────────────────────────┐
│ MD Converter                                 │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ Drop Markdown file here                │  │
│  │                                        │  │
│  │        [ Select File ]                 │  │
│  └────────────────────────────────────────┘  │
│                                              │
│ Output folder: Same as source       [Change] │
│                                              │
│                [ Convert ]                   │
│                                              │
│ Ready / status area                          │
└──────────────────────────────────────────────┘
```

At this WP stage, controls may be placeholders where later WPs implement behavior.

---

## 5. UX Constraints

Required:

- simple visual hierarchy;
- no technical terminology for ordinary controls;
- no CLI option dump;
- no advanced settings panel;
- primary Convert action visually clear;
- status area visible.

---

## 6. Convert Button Behavior in This WP

Because real conversion is not authorized yet:

- Convert may be disabled initially; or
- Convert may invoke a harmless placeholder action for later state-model testing.

It must not call Core or `ConversionService`.

---

## 7. Layout Rules

Prefer standard Qt layouts.

Avoid:

- absolute positioning;
- hard-coded pixel placement for every widget;
- custom painting unless necessary;
- complex theming.

The UI should resize reasonably.

---

## 8. Explicitly Forbidden

Not authorized:

- real conversion;
- worker/thread code;
- file picker behavior;
- drag/drop behavior;
- diagnostics dialog;
- preview;
- editor;
- advanced theme system;
- PDF/AI/template features.

---

## 9. Focused Verification

Verify:

```text
window renders required controls
controls have understandable labels
resize does not destroy primary layout
Convert is not wired to Core
CLI unaffected
```

GUI tests may inspect widget existence/object names where project conventions allow.

---

## 10. Acceptance Criteria

```text
main workflow controls visible
layout stable
no real conversion call
no Core import from MainWindow
no GUI scope expansion
focused verification PASS
```

---

## 11. Mandatory Stop Conditions

STOP if implementation requires:

- direct Core calls from MainWindow;
- architecture changes outside GUI layer;
- custom rendering framework;
- new product feature design.

---

## 12. Agent Completion Report

```text
WP: WP-P12-04-02
Status: PASS / BLOCKED

Files added:
Files modified:

Controls implemented:
Layout approach:

Core imports in GUI MainWindow: 0 / describe
Tests executed:
Tests passed:
Tests failed:

Scope expansion: NO / describe
Stop condition triggered: YES / NO
```

---

## 13. Closure Gate

```text
WP-P12-04-02 = CLOSED
```

Proceed to `WP-P12-04-03`.
