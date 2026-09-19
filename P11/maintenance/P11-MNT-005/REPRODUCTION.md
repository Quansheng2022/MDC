# P11-MNT-005 — Reproduction

## Activation Conditions

```text
Base HEAD: 58ed7dcf9190051341dde680c86b999f476fff87
P11: FROZEN / ACTIVE
Working tree: CLEAN
P11-MNT-005 ID: unused
```

## M01 — Primary Reproduction

Executed outside `PROJECT_ROOT` in a temporary working directory:

```python
from md_converter import convert
convert("# Hello")
```

Observed:

```text
primary_exception=AttributeError:
    'PassRegistry' object has no attribute '_pass_classes'
primary_files_created=[]
```

The failure matches the triage reproduction exactly.

## M02 — Canonical Control Path

```python
from md_converter.compiler import compile_markdown

doc = compile_markdown(
    "# Hello\n\nCanonical path.\n",
    config={
        "output_dir": <temp>,
        "enable_cover": False,
        "toc": False,
        "style_tables": False,
        "diagram": False,
    },
    output_path=<temp>/control.docx,
)
```

Observed:

```text
control_result=Document
control_docx_exists=True
```

The canonical construction path passes.

## Secondary Evidence — Unresolved Config

During triage, bypassing plugin discovery reached `compile()` with `config={}`
and produced:

```text
KeyError: 'enable_cover'
```

This is supporting evidence for the stale `convert()` construction path.
