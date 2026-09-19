# P11-MNT-003 — Root Cause Analysis

## Verified Root Cause

`AsciiToMermaidPass._transform_node()` handles `CodeBlock` in this order:

```text
1. normalize language
2. call _rescue_diagram_code()
3. ASCII auto-detection for language in ("", "text", "plain", "txt", "markdown")
```

Because `text` is included in the auto-detection language set, and because the
rescue path runs before any explicit-text guard, a `CodeBlock(language="text")`
can be replaced by a `Diagram` node.

The parser is not at fault: `CodeBuilder` correctly keeps `text` as a
`CodeBlock` because `text` is not an explicit diagram language.

## Failure Chain

```text
explicit ```text fence
    ↓
Parser -> CodeBlock(language="text")
    ↓
AsciiToMermaidPass -> _rescue_diagram_code()
    ↓
rescue finds Mermaid-like content OR ASCII heuristic finds diagram structure
    ↓
Diagram replaces explicit CodeBlock
```

## Fix Strategy

Apply the smallest correct guard after language normalization:

```python
if lang == "text":
    return node
```

This guard must execute before `_rescue_diagram_code()` and before ASCII
auto-detection. It preserves all other language semantics and does not change
the parser, service, renderer, or QA layers.

## Non-Root Causes Ruled Out

- Parser language classification is correct.
- `AsciiToMermaidService` does not mutate AST; it only supplies analysis.
- Renderer and QA layers are not involved in the semantic override.
