# P11-MNT-003 — Reproduction

## Activation Conditions

```text
P11-MNT-002: CLOSED / ACCEPTED
HEAD: 0639db259058970ea4be96d7d4c6985fefcdb4de
Working tree: CLEAN
```

## Reproduction Command

```powershell
@'
from md_converter.diagnostics.collector import DiagnosticCollector
from md_converter.parser.markdown_parser import MarkdownParser
from md_converter.parser.parser_context import ParserContext
from md_converter.pipeline.passes.ascii_mermaid_pass import AsciiToMermaidPass

ASCII_LIKE = """```text
+--------+     +--------+
| Start  | --> |  Done  |
+--------+     +--------+
```
"""

MERMAID_LIKE = """```text
graph LR
    A[Code Push] --> B[Build]
```
"""

for name, markdown in (
    ("text+ASCII-like", ASCII_LIKE),
    ("text+Mermaid-like", MERMAID_LIKE),
):
    diag = DiagnosticCollector()
    ast = MarkdownParser(ParserContext(diag=diag, config={})).parse(markdown)
    parsed = ast.children[0]
    result = AsciiToMermaidPass().run(ast, diag)
    transformed = result.document.children[0]
    print(
        f"{name}: parser={type(parsed).__name__} "
        f"lang={getattr(parsed, 'language', None)!r} "
        f"pass={type(transformed).__name__} "
        f"diagram={getattr(transformed, 'diagram_type', None)!r}"
    )
'@ | .\.venv\Scripts\python.exe -
```

## Observed Before Fix

```text
text+ASCII-like: parser=CodeBlock lang='text' pass=Diagram diagram='mermaid'
text+Mermaid-like: parser=CodeBlock lang='text' pass=Diagram diagram='mermaid'
```

## Expected

```text
text+ASCII-like: parser=CodeBlock lang='text' pass=CodeBlock language='text'
text+Mermaid-like: parser=CodeBlock lang='text' pass=CodeBlock language='text'
```

The explicit `text` fence must remain an exact `CodeBlock` in both cases.
