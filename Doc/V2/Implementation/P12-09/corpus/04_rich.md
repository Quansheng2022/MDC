---
title: Rich Rendering Case
date: 2026-09-27
tags:
  - acceptance
  - rendering
---

# Rich Rendering Case

This document exercises the richer accepted rendering paths: a code block, an
inline `code span`, a hyperlink, and an image reference.

## Code Block

```python
def convert(source: str) -> str:
    """Return a converted document path."""
    return source.replace(".md", ".docx")
```

## Inline Formatting

Text with **bold**, *italic*, `inline code`, and a
[hyperlink](https://example.com/acceptance).

## Embedded Structure

| Column A | Column B |
| --- | --- |
| alpha | beta |
| gamma | delta |

> Block quote with **bold text** inside it.

Final paragraph closing the rich case.
