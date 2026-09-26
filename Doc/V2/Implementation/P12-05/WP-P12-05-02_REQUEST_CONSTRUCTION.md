# WP-P12-05-02 — ConversionRequest Construction

**Program:** MD_Converter v2.0  
**Phase:** P12-05 — GUI/Core Integration  
**Execution Model:** Bounded Work Package  
**Authority Level:** G1 unless a G2 trigger is hit  
**P12-05 Baseline SHA:** `4356ca7ede841d50e8d255ca9dfd79365f16bec4`  
**Core Semantic Change Authority:** NONE  
**Golden Change Authority:** NONE  
**P12-06 Diagnostics UX Authority:** NONE  


## 1. Objective

Create the GUI-side adapter logic that converts current GUI session selections into one P12-03 `ConversionRequest`.

This WP constructs the request only. It does not execute it.

## 2. Preconditions

Required:

```text
WP-P12-05-01 CLOSED
```

Inspect `ConversionRequest`, MainWindow source storage, output-directory preference, and current filename/output policy in `ConversionService`.

## 3. Target Flow

```text
GUI source path
+
GUI output-directory preference
        ↓
request-construction adapter
        ↓
ConversionRequest
```

## 4. Output Path Rule

The GUI shall not invent DOCX naming.

If `output_directory = None`, preserve existing service default behavior.

If GUI has an explicit output directory, construct the request in the smallest way that lets `ConversionService` remain authoritative for approved filename semantics.

If the current `ConversionRequest` contract cannot safely represent output-directory intent without duplicating filename logic, STOP and report.

## 5. Authorized Scope

Preferred files:

```text
md_converter/gui/request_builder.py
md_converter/tests/gui/test_request_builder.py
```

Small MainWindow changes are allowed only to expose current selections.

## 6. Required Behavior

```text
valid source + default output
→ valid ConversionRequest
→ service default output preserved

valid source + explicit output directory
→ ConversionRequest preserving service filename authority

no source
→ no executable request
```

## 7. Explicitly Forbidden

Not authorized:

- parsing frontmatter;
- sanitizing output title in GUI;
- copying CLI filename rules;
- ConversionService execution;
- worker start;
- settings persistence;
- new metadata semantics.

## 8. Focused Tests

Test:

```text
request from valid selected source
default output behavior preserved
explicit output directory represented correctly
no source rejected deterministically
no filename sanitization in GUI
no frontmatter parsing in GUI
builder imports no Core/compiler modules
```

## 9. Acceptance Criteria

```text
request builder exists
ConversionRequest constructed from GUI state
service naming authority preserved
no duplicated filename policy
no frontmatter parsing in GUI
no conversion execution
tests PASS
Core/Golden/CLI changes = 0
```

## 10. Mandatory Stop Conditions

STOP if:

- GUI must duplicate filename sanitization;
- GUI must parse frontmatter;
- `ConversionRequest` contract is insufficient and requires semantic change;
- application service contract must change in a way affecting CLI/public API behavior.

## 11. Agent Completion Report

```text
WP: WP-P12-05-02
Status: PASS / BLOCKED

Files added:
Files modified:

Request construction path:
Default output behavior:
Explicit output-directory behavior:

Filename logic duplicated in GUI: YES / NO
Frontmatter parsing in GUI: YES / NO
Conversion invoked: YES / NO

Tests executed:
Tests passed:
Tests failed:

Core changes:
Golden changes:
CLI behavior changes:

Stop condition triggered: YES / NO
```

## 12. Closure Gate

```text
WP-P12-05-02 = CLOSED
```

Proceed to WP-P12-05-03.
