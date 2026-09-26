# WP-P12-04-01 — GUI Application Bootstrap

**Program:** MD_Converter v2.0  
**Phase:** P12-04 — GUI Foundation  
**Execution Model:** Bounded Work Package  
**Authority Level:** G1 unless a G2 trigger is hit  
**Core Semantic Change Authority:** NONE  
**Golden Change Authority:** NONE  
**Real Conversion Integration Authority:** NONE in P12-04  


## 1. Objective

Create the minimum PySide6 desktop application bootstrap required to launch and close the MD_Converter GUI.

This WP establishes the GUI runtime boundary only.

It does **not** implement:

- real conversion;
- file selection;
- drag & drop;
- output selection;
- diagnostics;
- settings;
- installer behavior.

---

## 2. Preconditions

Required:

- P12-03 implementation accepted;
- P12-03 Git baseline/closure SHA recorded or otherwise explicitly authorized;
- ADR-GUI-001 remains accepted;
- PySide6 dependency strategy is understood well enough for development use.

Before implementation, inspect:

- current package structure;
- `pyproject.toml`;
- current CLI entry points;
- current package version authority;
- whether a `gui/` package already exists.

Do not create duplicate GUI packages.

---

## 3. Authorized Scope

Conceptual target:

```text
md_converter/
└── gui/
    ├── __init__.py
    ├── app.py
    └── main_window.py
```

Focused tests may be added under the existing test authority.

Minimal `pyproject.toml` development dependency/entry-point change is allowed only if strictly necessary to launch the GUI during development.

If packaging implications are material, STOP and defer packaging decisions to P12-08.

---

## 4. Required Behavior

The application shall support:

```text
start Python GUI entry
↓
construct QApplication
↓
construct MainWindow
↓
show MainWindow
↓
enter Qt event loop
↓
close normally
```

---

## 5. MainWindow Baseline

The first window may be visually minimal.

Required only:

- application title;
- stable initial size;
- central widget/layout;
- placeholder content sufficient to prove bootstrap.

No production-grade styling is required.

---

## 6. Dependency Boundary

PySide6 imports shall remain inside the GUI layer.

Forbidden:

```text
md_converter/application/*
→ import PySide6
```

P12-03 application code must remain GUI-independent.

---

## 7. Entry Point Rule

The GUI entry path shall not replace or break the CLI entry point.

Target concept:

```text
CLI entry → existing CLI
GUI entry → md_converter.gui.app
```

One package may expose two front ends.

---

## 8. Explicitly Forbidden

Not authorized:

- calling `ConversionService`;
- calling `CompilerContext`;
- changing conversion semantics;
- modifying parser/renderer/QA;
- creating worker threads;
- adding drag/drop;
- adding installer logic;
- broad `pyproject.toml` cleanup;
- changing CLI behavior;
- changing Golden.

---

## 9. Focused Tests / Verification

Minimum:

```text
GUI module imports successfully
QApplication can be constructed in test environment where supported
MainWindow can be instantiated
window title correct
window closes without exception
application layer has no Qt dependency
```

If headless CI requires special Qt handling, use the smallest existing-project-compatible test approach.

Do not redesign test infrastructure.

---

## 10. Acceptance Criteria

```text
GUI package exists
application launches
MainWindow opens
MainWindow closes normally
CLI still imports/runs
application layer imports without Qt
core semantic changes = 0
Golden changes = 0
```

---

## 11. Mandatory Stop Conditions

STOP if:

- GUI bootstrap requires changing Core semantics;
- CLI entry point must be replaced;
- application layer must import Qt;
- packaging architecture must be redesigned;
- existing dependency policy conflicts materially with PySide6;
- broad repository restructuring appears necessary.

---

## 12. Agent Completion Report

```text
WP: WP-P12-04-01
Status: PASS / BLOCKED

Files added:
Files modified:

GUI entry:
MainWindow:
PySide6 dependency location:

Tests executed:
Tests passed:
Tests failed:

CLI behavior changes: 0 / describe
Application-layer Qt dependency: 0 / describe
Core semantic changes: 0 / describe
Golden changes: 0 / describe

Stop condition triggered: YES / NO
```

---

## 13. Closure Gate

After focused verification passes:

```text
WP-P12-04-01 = CLOSED
```

Proceed to `WP-P12-04-02`.
