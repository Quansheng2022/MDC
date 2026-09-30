---
title: MD Converter R2 Pre-RC Installer Verification
---

# Installer Lifecycle Verification

This document is produced by the *installed* MD Converter application during the
R2 pre-release-candidate installer gate. It exercises headings, paragraphs,
inline formatting, lists, block quotes, code blocks, tables and horizontal rules
through the packaged GUI conversion path.

## Inline formatting

The paragraph below mixes **bold text**, *italic text*, `inline code` and a
[hyperlink](https://example.com/r2-pre-rc) in one flow, so nested inline state is
exercised rather than a single flat run.

### Lists

1. First ordered item
2. Second ordered item
3. Third ordered item

- First unordered item
- Second unordered item with `code`
- Third unordered item

### Block quote

> Determinism and architectural consistency matter more than clever output.
> This sentence is inside a block quote.

### Code block

```python
def convert(markdown: str) -> bytes:
    return compile_document(markdown)
```

### Table

| Stage | Owner | Verified by |
| --- | --- | --- |
| Parser | markdown-it-py | R2-V01 |
| Pipeline | TransformPass | R2-V01 |
| Renderer | NodeVisitor | R2-V01 |
| Post Processor | Word automation | R2-V03 |

### Closing section

The closing paragraph exists so the document has content after the table and
before the final horizontal rule.

---

End of the representative verification document.
