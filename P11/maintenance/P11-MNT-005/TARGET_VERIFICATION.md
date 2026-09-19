# P11-MNT-005 — Target Verification

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_B — Maintenance Change Package Execution |
| Work Package | P11-MNT-005 |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0 §8 / §20 / §21 |
| Status | VERIFIED / AWAITING REVIEW |

---

## 1. Syntax

```text
.\.venv\Scripts\python.exe -m py_compile
    md_converter/__init__.py
    md_converter/tests/test_public_api_convert.py

Result: PASS
```

## 2. Focused Tests

Pre-patch RED:

```text
pytest md_converter/tests/test_public_api_convert.py -q -ra

Result:
  2 failed
  AttributeError: 'PassRegistry' object has no attribute '_pass_classes'
```

Post-patch:

```text
pytest md_converter/tests/test_public_api_convert.py -q -ra

Result: 2 passed
```

Covered:

1. `convert("# Hello")` returns a Document-like object without exception;
2. `convert(..., partial config)` works through resolved defaults.

## 3. Manual Smoke Outside PROJECT_ROOT

UTF-8 console environment:

```text
default_is_document=True
partial_is_document=True
default_docx_exists=True
partial_docx_exists=True
attribute_error_occurred=False
key_error_occurred=False
```

The default cp1252 console run exposed a pre-existing post-processor print
encoding artifact (emoji not encodable in cp1252). Re-running with
`PYTHONIOENCODING=utf-8` matches the repository's existing console handling and
the required smoke result. No product change was made for this environment
artifact.

## 4. Ruff

```text
md_converter/__init__.py:
  baseline before change: All checks passed
  after change:           All checks passed

md_converter/tests/test_public_api_convert.py:
  All checks passed

No new lint findings. No unrelated historical lint debt was cleaned.
```

## 5. Product Diff

```text
md_converter/__init__.py

convert()
    no longer manually constructs DiagnosticCollector / ParserContext /
    RenderContext / PassRegistry / CompilerContext

    delegates to:
        compile_markdown(markdown_text, config=config, theme=theme)
```

Signature preserved:

```text
(markdown_text: str, config: dict = None, theme=None)
```

No new parameters. No new output/save semantics.

## 6. Post-Commit Strict Gate

```text
.\.venv\Scripts\python.exe
    tools/review/merge_project_for_phase11_review.py
    --mode maintenance --strict
    --output <outside PROJECT_ROOT>
```

The post-commit strict gate is run without `--run-pytest`; the full regression
has already passed. Result is recorded in the P11-MNT-005 final report.
