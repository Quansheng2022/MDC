# P11-MNT-003 — Target Verification

## Artifact Header

| Field | Value |
| --- | --- |
| Plan | P11_AGENT_PLAN_B — Maintenance Change Package Execution |
| Work Package | P11-MNT-003 |
| Authority | `Doc/Phase_11_Maintenance_Specification.md` v1.0 §8 / §20 / §21 |
| Status | VERIFIED / AWAITING REVIEW |

---

## 1. Syntax

```text
.\.venv\Scripts\python.exe -m py_compile
    md_converter/pipeline/passes/ascii_mermaid_pass.py
    md_converter/tests/test_ascii_mermaid_pass.py

Result: PASS
```

## 2. Targeted Tests

```text
.\.venv\Scripts\python.exe -m pytest
    md_converter/tests/test_ascii_mermaid_pass.py -q -ra

Result: 15 passed
```

The three new focused tests cover:

1. explicit `text` + ASCII-like content remains an exact `CodeBlock`;
2. explicit `text` + Mermaid-like content remains an exact `CodeBlock`;
3. compiler integration proves an explicit `text` fence is not converted.

No existing tests for unlabeled ASCII auto-detection, explicit ASCII diagram
conversion, or ordinary non-diagram code blocks were duplicated.

## 3. Behavior Matrix

Observed after the fix:

```text
text+ASCII:                parser=CodeBlock(lang='text')
                           pass=CodeBlock(lang='text')

text+Mermaid:              parser=CodeBlock(lang='text')
                           pass=CodeBlock(lang='text')

unlabeled ASCII:           parser=CodeBlock(lang='')
                           pass=Diagram(diagram='mermaid')

explicit ascii:            parser=Diagram(diagram='ascii')
                           pass=Diagram(diagram='mermaid')

explicit diagram:          parser=Diagram(diagram='ascii')
                           pass=Diagram(diagram='mermaid')

ordinary unlabeled code:   parser=CodeBlock(lang='')
                           pass=CodeBlock(lang='')
```

## 4. Strict Maintenance Gate

Because strict mode requires a clean working tree, the single final strict
gate is executed immediately after the bounded implementation commit:

```text
.\.venv\Scripts\python.exe
    tools/review/merge_project_for_phase11_review.py
    --mode maintenance
    --run-pytest
    --strict
    --output <outside PROJECT_ROOT>
```

Required result:

```text
full regression failed=0
unexpected skip=0
new regression=0
strict=PASS
generated review nesting=0
```

The strict result is recorded in the Batch B final report; the implementation
commit cannot self-reference its own not-yet-existing SHA.
