# WP-P12-03-01 — ConversionRequest

**Program:** MD_Converter v2.0  
**Phase:** P12-03 — Application Service Extraction  
**Execution Model:** Bounded Work Package  
**Authority Level:** G1 unless a G2 trigger is hit  
**Core Semantic Change Authority:** NONE  
**Golden Change Authority:** NONE  


## 1. Objective

Introduce a minimal application-layer request model named `ConversionRequest` for one Markdown → DOCX conversion request.

The purpose is to decouple future GUI/CLI adapters from direct knowledge of compiler internals.

This WP does **not** execute conversion.

---

## 2. Preconditions

Before implementation, the Coding Agent shall inspect:

- current `md_converter` package structure;
- current file/path handling in `cli.py`;
- current `CompilerContext.compile_file()` signature and behavior;
- current public `convert()` / `compile_markdown()` / `compile_file()` APIs;
- current config representation and expected override shape.

The agent shall use the actual repository structure and shall not create duplicate packages merely because this specification shows conceptual paths.

---

## 3. Authorized Scope

Authorized:

- create an `application` package if no equivalent application layer exists;
- create `conversion_request.py`;
- add focused tests for the request model;
- add minimal `__init__.py` exports if useful.

Conceptual target:

```text
md_converter/
└── application/
    ├── __init__.py
    └── conversion_request.py
```

---

## 4. Proposed Model

Preferred concept:

```python
ConversionRequest
```

Minimum candidate fields:

```text
source_path
output_path          optional
config_overrides     optional
metadata_overrides   optional
```

Exact Python types shall follow existing project conventions.

### 4.1 Required properties

The request model should:

- represent one file conversion;
- be usable without importing GUI frameworks;
- avoid embedding compiler objects;
- avoid embedding parser/renderer objects;
- avoid embedding mutable global state;
- validate only application-boundary invariants that are safe to validate here.

---

## 5. Validation Rules

At minimum evaluate whether to validate:

- source path supplied;
- source path type/path normalization;
- supported source extension where current product contract allows;
- explicit output path shape if supplied;
- config/metadata override mapping type if supplied.

Do **not** move deep conversion validation out of the existing core.

Do **not** invent new product restrictions.

---

## 6. Explicitly Forbidden

Not authorized:

- changing `CompilerContext.compile()` semantics;
- changing parser behavior;
- changing AST;
- changing pipeline;
- changing renderer;
- changing QA;
- changing filename policy;
- changing CLI behavior;
- changing Golden files;
- introducing PySide6;
- adding GUI state;
- opportunistic refactoring.

---

## 7. Focused Tests

Create focused tests for the request model.

Recommended cases:

```text
valid source path
explicit output path
output omitted
config_overrides omitted
metadata_overrides omitted
config_overrides supplied
metadata_overrides supplied
invalid structural input where the model itself is responsible
```

Avoid testing compiler behavior in this WP.

---

## 8. Acceptance Criteria

WP passes when:

```text
ConversionRequest exists
imports without GUI dependency
focused tests PASS
core product files modified = 0 unless strictly required for export
Canonical semantics changed = 0
Golden changed = 0
CLI behavior changed = 0
```

---

## 9. Mandatory Stop Conditions

STOP and report if implementation appears to require:

- changing existing conversion semantics;
- redefining current output naming;
- changing CLI options/contracts;
- modifying Canonical Specification;
- modifying architecture outside the approved application boundary;
- changing Golden baseline.

Do not solve those issues inside this WP.

---

## 10. Agent Completion Report

Return:

```text
WP: WP-P12-03-01
Status: PASS / BLOCKED

Files added:
Files modified:

Tests executed:
Tests passed:
Tests failed:

Core semantic changes: 0 / describe
Golden changes: 0 / describe
CLI behavior changes: 0 / describe

Observed issues outside scope:
Stop condition triggered: YES / NO
```

---

## 11. Closure Gate

Only after focused tests pass and no stop condition is triggered:

```text
WP-P12-03-01 = CLOSED
```

Then proceed to `WP-P12-03-02`.
