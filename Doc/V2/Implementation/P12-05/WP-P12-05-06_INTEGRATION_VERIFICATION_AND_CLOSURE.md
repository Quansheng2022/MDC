# WP-P12-05-06 — Integration Verification and P12-05 Closure

**Program:** MD_Converter v2.0  
**Phase:** P12-05 — GUI/Core Integration  
**Execution Model:** Bounded Work Package  
**Authority Level:** G1 unless a G2 trigger is hit  
**P12-05 Baseline SHA:** `4356ca7ede841d50e8d255ca9dfd79365f16bec4`  
**Core Semantic Change Authority:** NONE  
**Golden Change Authority:** NONE  
**P12-06 Diagnostics UX Authority:** NONE  


## 1. Objective

Perform final verification and closure of P12-05 GUI/Core Integration.

This WP adds no new user-facing feature.

## 2. Preconditions

Required closed:

```text
WP-P12-05-01
WP-P12-05-02
WP-P12-05-03
WP-P12-05-04
WP-P12-05-05
```

## 3. Required End-to-End Flow

```text
Launch
→ EMPTY
→ Select or Drop Markdown
→ READY
→ optional output directory
→ Convert
→ CONVERTING
→ Worker
→ ConversionService
→ Canonical Core
→ ConversionResult
→ SUCCESS / SUCCESS_WITH_WARNING / FAILED
```

## 4. Verification Layers

### V1 — Worker Boundary

```text
conversion off GUI thread
completion delivered to GUI thread
worker lifecycle clean
```

### V2 — Request Construction

```text
source correct
output-directory intent preserved
GUI does not own filename policy
no frontmatter parsing in GUI
```

### V3 — Real Conversion

At least one deterministic real `.md → .docx` conversion through GUI integration path.

### V4 — Result Mapping

Verify SUCCESS / SUCCESS_WITH_WARNING / FAILED map correctly.

### V5 — Lifecycle Protection

```text
duplicate execution prevented
source/output mutation blocked while CONVERTING
next conversion can run after completion
close behavior safe
```

### V6 — Architecture Boundary

Confirm:

```text
GUI direct CompilerContext calls = 0
GUI parser/renderer/QA imports = 0
Application layer Qt imports = 0
second conversion pipeline = 0
```

### V7 — Regression

Run:

- P12-05 focused GUI/integration tests;
- P12-03 application tests;
- relevant CLI/public API smoke;
- full required regression according to current policy.

Known approved packaging baseline failures may remain pre-existing.

Required:

```text
P12-05 introduced failures = 0
```

### V8 — Golden / Acceptance

Confirm:

```text
Golden changes = 0
Canonical output semantic changes = 0
```

unless separately authorized.

## 5. P12-05 Closure Evidence

Create:

```text
Doc/V2/Implementation/P12-05/P12-05_CLOSURE_EVIDENCE.md
```

Record:

- baseline SHA;
- WP 01–06 status;
- focused tests;
- full regression;
- known baseline failures;
- P12-05 introduced failures;
- real conversion evidence;
- thread-boundary evidence;
- Core/Golden/CLI drift;
- open blockers;
- closure decision.

Do not create redundant review documents.

## 6. Exit Criteria

All must be true:

```text
WP 01–05 CLOSED
GUI real conversion works
conversion is off main thread
GUI direct Core calls = 0
result mapping correct
duplicate execution prevented
worker lifecycle safe
P12-05 introduced regression failures = 0
Core semantic changes = 0
Golden changes = 0
CLI breaking changes = 0
open blockers = 0
```

Then:

```text
P12-05 GUI/Core Integration = CLOSED / ACCEPTED
P12-06 Error / Diagnostics UX = AUTHORIZED / NEXT
```

## 7. Explicitly Forbidden

Do not use closure to add:

- diagnostics panel;
- conversion report UI;
- Open Document/Open Folder;
- settings persistence;
- preview/editor;
- batch conversion;
- packaging changes;
- unrelated maintenance fixes.

## 8. Mandatory Stop Conditions

Do not close P12-05 if:

- real conversion requires direct GUI→Core call;
- conversion runs on GUI thread;
- worker lifecycle unsafe;
- native crash remains reproducible;
- P12-05 introduces a new required regression failure;
- Core/Golden semantics changed without authority;
- CLI/public API regression introduced.

## 9. Agent Final Report Template

```text
PHASE: P12-05 GUI/Core Integration
STATUS: PASS / BLOCKED

WP status:
- WP-P12-05-01:
- WP-P12-05-02:
- WP-P12-05-03:
- WP-P12-05-04:
- WP-P12-05-05:
- WP-P12-05-06:

Baseline SHA:

Files added:
Files modified:

GUI/integration tests:
- passed:
- failed:

Application tests:
- passed:
- failed:

Full regression:
- passed:
- failed:
- known pre-existing failures:
- P12-05 introduced failures:

Real GUI conversion:
Worker thread evidence:
Result mapping:
Duplicate protection:
Window-close behavior:

Direct Core calls from GUI:
Application-layer Qt dependency:
Core changes:
Golden changes:
CLI behavior changes:
Unauthorized drift:

Open blockers:

Recommended closure decision:
Recommended next phase:
```

## 10. Final Decision

If all exit criteria pass:

> **P12-05 GUI/Core Integration = CLOSED / ACCEPTED. Proceed to P12-06.**

If any gate fails:

> **Resolve only the concrete P12-05 blocker. Do not broaden scope.**
