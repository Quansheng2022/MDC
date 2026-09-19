# P11-MNT-005 — Maintenance Change Package

## Artifact Header

| Field | Value |
| --- | --- |
| Change Package | P11-MNT-005 |
| Title | Top-Level convert() Uses Stale Parallel Compiler Construction |
| Source | P11-BACKLOG-TRIAGE-CONVERT + Human-authorized bounded implementation |
| Classification | DEFECT |
| Severity | P3 Normal |
| Affected Version | v1.0.x |
| Affected Component | `md_converter/__init__.py` |
| Canonical References | `SPEC-GOAL-002`, `SPEC-GOAL-006` |
| Status | APPROVED → VERIFIED / AWAITING REVIEW |

## Authorized Scope

```text
md_converter/__init__.py
md_converter/tests/test_public_api_convert.py
P11/P11_MAINTENANCE_REGISTRY.md
P11/maintenance/P11-MNT-005/**
```

## Forbidden Scope

```text
md_converter/compiler.py
md_converter/config.py
PassRegistry implementation
plugin_discovery.py
parser/**
pipeline/**
renderer/**
QA
theme implementation
CANONICAL_SPEC.md
Architecture / ADR
Acceptance
Golden
dependencies
release / tag / version
PLAN_C
P12
general refactor
new API framework
```

## Implementation Principle

Do not patch `_pass_classes`, config keys, theme construction, plugin
discovery, or `PassRegistry` individually.

Remove stale compiler-construction ownership from `convert()` and delegate to
the existing canonical compiler helper.

## Minimal Change

```python
def convert(markdown_text: str, config: dict = None, theme=None):
    from .compiler import compile_markdown
    return compile_markdown(markdown_text, config=config, theme=theme)
```

Signature preserved. No new parameters. No new save/output semantics.

## Required Focused Tests

```text
1. convert("# Hello") returns Document-like object without exception.
2. convert(..., partial config) works through resolved defaults.
```

Tests must use `tmp_path` / temporary cwd so the repository is not polluted.

## Required Verification

```text
focused tests RED before patch
focused tests PASS after patch
py_compile PASS
Ruff changed files: no new findings
manual smoke outside PROJECT_ROOT: no AttributeError / KeyError
one full regression
strict maintenance snapshot outside PROJECT_ROOT
```
