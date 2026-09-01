# MD Converter Sample Document

**Version**: 1.0.0  
**Date**: 2024-01-15  
**Author**: MD Converter Team

---

## Table of Contents

- [Document Metadata](#document-metadata)
- [Headings](#headings)
- [Text Formatting](#text-formatting)
- [Lists](#lists)
- [Tables](#tables)
- [Code Blocks](#code-blocks)
- [Blockquotes](#blockquotes)
- [Links](#links)
- [Images](#images)
- [Horizontal Rules](#horizontal-rules)
- [ASCII Diagrams](#ascii-diagrams)
- [Complex Nested Structures](#complex-nested-structures)
- [Edge Cases](#edge-cases)

---

## Document Metadata

```yaml
---
title: MD Converter Sample Document
author: MD Converter Team
date: 2024-01-15
tags: [sample, test, markdown, converter, documentation]
version: 1.0.0
status: draft
---
```

---

## Headings

# Heading Level 1

The main document title.

## Heading Level 2

Major section heading.

### Heading Level 3

Subsection heading.

#### Heading Level 4

Detailed subsection heading.

##### Heading Level 5

Minor heading.

###### Heading Level 6

Smallest heading.

---

## Text Formatting

### Basic Formatting

This is **bold text** and this is *italic text*.
This is ***bold and italic text***.
This is `inline code` text.

### Combined Formatting

- **Bold with *italic* inside**
- *Italic with **bold** inside*
- **Bold with `code` inside**
- *Italic with `code` inside*

### Strikethrough

~~This text is crossed out~~ (if supported).

### Underline

<u>This text is underlined</u> (if supported).

---

## Lists

### Unordered Lists

#### Basic Unordered List

- First item
- Second item
- Third item

#### Nested Unordered List

- Level 1 item
  - Level 2 item
    - Level 3 item
      - Level 4 item
  - Another level 2 item
- Back to level 1

#### Unordered List with Formatting

- **Bold list item**
- *Italic list item*
- `Code list item`
- ***Bold and italic list item***

### Ordered Lists

#### Basic Ordered List

1. First item
2. Second item
3. Third item

#### Nested Ordered List

1. Level 1 item
   1. Level 2 item
      1. Level 3 item
         1. Level 4 item
   2. Another level 2 item
2. Back to level 1

#### Ordered List with Start Attribute

1. Item one
2. Item two
3. Item three

### Mixed Lists

1. First level 1 item
   - Sub-item 1.1
   - Sub-item 1.2
2. Second level 1 item
   1. Sub-item 2.1
   2. Sub-item 2.2
3. Third level 1 item

### Task Lists

- [x] Completed task
- [x] Another completed task
- [ ] Pending task
- [ ] Task with **bold** text
- [x] Task with *italic* text

---

## Tables

### Simple Table

| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1.1 | Cell 1.2 | Cell 1.3 |
| Cell 2.1 | Cell 2.2 | Cell 2.3 |
| Cell 3.1 | Cell 3.2 | Cell 3.3 |

### Table with Alignment

| Left Align | Center Align | Right Align |
|:-----------|:------------:|------------:|
| Left 1     | Center 1     | Right 1     |
| Left 2     | Center 2     | Right 2     |
| Left 3     | Center 3     | Right 3     |

### Table with Formatting

| **Bold Header** | *Italic Header* | `Code Header` |
|-----------------|-----------------|---------------|
| **Bold Cell**   | *Italic Cell*   | `Code Cell`   |
| *Italic Cell*   | **Bold Cell**   | `Code Cell`   |
| `Code Cell`     | `Code Cell`     | **Bold Cell** |

### Table with Mixed Content

| Feature | Description | Example | Status |
|---------|-------------|---------|--------|
| Bold    | Makes text **bold** | `**text**` | ✅ |
| Italic  | Makes text *italic* | `*text*` | ✅ |
| Code    | Inline code | `` `code` `` | ✅ |
| Link    | Creates a [link](https://example.com) | `[text](url)` | ✅ |
| Image   | Inserts an image | `![alt](url)` | ✅ |

---

## Code Blocks

### Python Code

```python
#!/usr/bin/env python3
"""
Fibonacci sequence generator with caching.
"""

from functools import lru_cache

@lru_cache(maxsize=128)
def fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number.
    
    Args:
        n: The position in the Fibonacci sequence.
        
    Returns:
        The nth Fibonacci number.
    """
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

def generate_sequence(n: int) -> list:
    """Generate Fibonacci sequence up to n."""
    return [fibonacci(i) for i in range(n)]

if __name__ == "__main__":
    print(generate_sequence(10))
```

### JavaScript Code

```javascript
/**
 * Fibonacci sequence generator
 * @param {number} n - The position in the sequence
 * @returns {number} The nth Fibonacci number
 */
function fibonacci(n) {
    if (n < 2) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

/**
 * Generate Fibonacci sequence
 * @param {number} n - Number of terms
 * @returns {number[]} Fibonacci sequence
 */
function generateSequence(n) {
    const result = [];
    for (let i = 0; i < n; i++) {
        result.push(fibonacci(i));
    }
    return result;
}

console.log(generateSequence(10));
```

### HTML Code

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fibonacci Calculator</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 600px; margin: 0 auto; }
        .result { font-weight: bold; color: #2F5496; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Fibonacci Calculator</h1>
        <p>Enter a number to calculate the Fibonacci sequence:</p>
        <input type="number" id="input" min="0" max="20">
        <button onclick="calculate()">Calculate</button>
        <div id="result" class="result"></div>
    </div>
    <script>
        function calculate() {
            const n = parseInt(document.getElementById('input').value);
            // ... calculation logic
        }
    </script>
</body>
</html>
```

### SQL Code

```sql
-- ============================================================
-- Fibonacci Sequence Generator (PostgreSQL)
-- ============================================================

CREATE OR REPLACE FUNCTION fibonacci(n INTEGER)
RETURNS INTEGER AS $$
DECLARE
    a INTEGER := 0;
    b INTEGER := 1;
    c INTEGER := 0;
    i INTEGER := 1;
BEGIN
    IF n < 2 THEN
        RETURN n;
    END IF;
    
    WHILE i < n LOOP
        c := a + b;
        a := b;
        b := c;
        i := i + 1;
    END LOOP;
    
    RETURN c;
END;
$$ LANGUAGE plpgsql;

-- Generate sequence
SELECT 
    generate_series(0, 10) AS n,
    fibonacci(generate_series(0, 10)) AS fib;
```

---

## Blockquotes

### Simple Blockquote

> This is a simple blockquote.
> It can span multiple lines.
> 
> And include multiple paragraphs.

### Nested Blockquotes

> Level 1 quote
> 
> > Level 2 quote
> > 
> > > Level 3 quote
> > > 
> > > > Level 4 quote

### Blockquote with Formatting

> This blockquote contains **bold** and *italic* text.
> 
> It also contains `inline code` and [links](https://example.com).

### Blockquote with List

> Here's a list inside a blockquote:
> 
> - Item 1 with **bold**
> - Item 2 with *italic*
> - Item 3 with `code`
>   - Nested item 3.1
>   - Nested item 3.2

### Blockquote with Code Block

> Here's a code block inside a blockquote:
> 
> ```python
> def hello():
>     print("Hello from inside a blockquote!")
> ```

---

## Links

### External Links

- [GitHub](https://github.com)
- [Python Documentation](https://docs.python.org/3/)
- [Markdown Guide](https://www.markdownguide.org)
- [Stack Overflow](https://stackoverflow.com)

### Internal Links (Anchor Links)

- [Back to Top](#table-of-contents)
- [Headings](#headings)
- [Lists](#lists)
- [Tables](#tables)

### Links with Formatting

- [**Bold Link**](https://example.com)
- [*Italic Link*](https://example.com)
- [***Bold and Italic Link***](https://example.com)
- [`Code Link`](https://example.com)

### Reference Links

This is a [reference link][1].

[1]: https://example.com "Example Domain"

---

## Images

### Simple Image

![Placeholder Image](https://via.placeholder.com/150x150/2F5496/FFFFFF?text=MD)

### Image with Caption

![MD Converter Logo](https://via.placeholder.com/300x100/2F5496/FFFFFF?text=MD+Converter)

*Figure 1: MD Converter Logo*

### Image with Link

[![MD Converter](https://via.placeholder.com/200x80/2F5496/FFFFFF?text=MD+Converter)](https://example.com)

---

## Horizontal Rules

---

***

___

---

## ASCII Diagrams

### Simple Box Diagram

```
┌─────────────────────┐
│     Main Module     │
├──────────┬──────────┤
│ Sub 1    │ Sub 2    │
├──────────┴──────────┤
│    Shared Resource   │
└─────────────────────┘
```

### Flowchart

```
        ┌──────────┐
        │  Start   │
        └────┬─────┘
             │
             ▼
        ┌──────────┐
        │  Input   │
        └────┬─────┘
             │
             ▼
        ┌──────────┐
        │ Process  │
        └────┬─────┘
             │
             ▼
        ┌──────────┐
        │  Output  │
        └────┬─────┘
             │
             ▼
        ┌──────────┐
        │   End    │
        └──────────┘
```

### Database Schema Diagram

```
┌─────────────────────────────────────────────┐
│              Users Table                    │
├────────────┬────────────────────────────────┤
│ id         │ INTEGER PRIMARY KEY           │
│ username   │ VARCHAR(50) UNIQUE            │
│ email      │ VARCHAR(255) UNIQUE           │
│ password   │ VARCHAR(255)                  │
│ created_at │ TIMESTAMP                     │
│ updated_at │ TIMESTAMP                     │
│ status     │ VARCHAR(20) DEFAULT 'active'  │
└────────────┴────────────────────────────────┘
         │
         │ 1
         │
         ▼
┌─────────────────────────────────────────────┐
│             Orders Table                    │
├────────────┬────────────────────────────────┤
│ id         │ INTEGER PRIMARY KEY           │
│ user_id    │ INTEGER REFERENCES users      │
│ order_date │ TIMESTAMP                     │
│ total      │ DECIMAL(10,2)                 │
│ status     │ VARCHAR(50)                   │
│ notes      │ TEXT                          │
└────────────┴────────────────────────────────┘
         │
         │ 1
         │
         ▼
┌─────────────────────────────────────────────┐
│           Order Items Table                 │
├────────────┬────────────────────────────────┤
│ id         │ INTEGER PRIMARY KEY           │
│ order_id   │ INTEGER REFERENCES orders     │
│ product    │ VARCHAR(100)                  │
│ quantity   │ INTEGER                       │
│ price      │ DECIMAL(10,2)                 │
│ subtotal   │ DECIMAL(10,2)                 │
└────────────┴────────────────────────────────┘
```

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Application                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────┐      ┌─────────────────────────────┐  │
│  │     Frontend        │      │         Backend             │  │
│  │  ┌───────────────┐  │      │  ┌───────────────────────┐  │  │
│  │  │   React.js    │  │      │  │  Node.js / Express    │  │  │
│  │  │   Redux       │  │      │  │  REST API             │  │  │
│  │  │   Tailwind    │  │      │  │  WebSocket            │  │  │
│  │  └───────────────┘  │      │  └───────────────────────┘  │  │
│  │                     │      │                              │  │
│  │  ┌───────────────┐  │      │  ┌───────────────────────┐  │  │
│  │  │  Mobile App   │  │      │  │  Authentication       │  │  │
│  │  │  React Native │  │      │  │  JWT / OAuth2         │  │  │
│  │  └───────────────┘  │      │  └───────────────────────┘  │  │
│  └─────────────────────┘      └─────────────────────────────┘  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 Database Layer                         │   │
│  │  ┌─────────────────┐  ┌─────────────────────────────┐ │   │
│  │  │  PostgreSQL     │  │  Redis (Cache)              │ │   │
│  │  │  - Users        │  │  - Sessions                 │ │   │
│  │  │  - Orders       │  │  - Rate Limiting            │ │   │
│  │  │  - Products     │  │  - Queues                   │ │   │
│  │  └─────────────────┘  └─────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction Diagram

```
        ┌─────────────┐
        │   Client    │
        └──────┬──────┘
               │
               │ HTTP Request
               ▼
        ┌─────────────┐
        │    Load     │
        │  Balancer   │
        └──────┬──────┘
               │
               ▼
        ┌─────────────┐
        │   Web       │
        │  Server     │
        └──────┬──────┘
               │
       ┌───────┼───────┐
       │       │       │
       ▼       ▼       ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│  App    │ │  App    │ │  App    │
│ Server  │ │ Server  │ │ Server  │
└────┬────┘ └────┬────┘ └────┬────┘
     │           │           │
     └───────────┼───────────┘
                 │
                 ▼
        ┌─────────────┐
        │  Database   │
        └─────────────┘
```

---

## Complex Nested Structures

### Nested Lists with Formatting

1. **Level 1 Item 1**
   - *Level 2 Item 1.1*
     - `Level 3 Item 1.1.1`
       - Level 4 Item 1.1.1.1
         - ***Level 5 Item 1.1.1.1.1***
   - Level 2 Item 1.2 with **bold**
2. Level 1 Item 2
   - Level 2 Item 2.1 with *italic*
     - Level 3 Item 2.1.1 with `code`
3. Level 1 Item 3 with ***bold and italic***

### Nested Tables in Lists

1. Level 1 item
   - Level 2 item with table:
   
   | Sub-Header 1 | Sub-Header 2 |
   |--------------|--------------|
   | Sub-Cell 1.1 | Sub-Cell 1.2 |
   | Sub-Cell 2.1 | Sub-Cell 2.2 |

2. Level 1 item with another table:
   
   | Header A | Header B |
   |----------|----------|
   | Cell A.1 | Cell B.1 |
   | Cell A.2 | Cell B.2 |

### List Inside Table

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Text 1   | List:    | Text 3   |
|          | - Item 1 |          |
|          | - Item 2 |          |
|          | - Item 3 |          |
| Text 4   | Text 5   | Text 6   |

### Complex Blockquote with Everything

> # Quote Heading
> 
> This is a blockquote that contains **bold** and *italic* text.
> 
> ## Sub-quote Heading
> 
> > Nested blockquote with `code` and [links](https://example.com).
> > 
> > - List item 1
> > - List item 2
> >   - Nested list item 2.1
> > 
> > ```python
> > print("Hello from nested quote!")
> > ```
> 
> Back to main quote level.

---

## Edge Cases

### Empty Elements

<!-- Empty paragraph above -->

<!-- Empty paragraph below -->

### Whitespace and Line Breaks

This paragraph has    multiple    spaces.

This line has a trailing space after it.   

This text  
has a line break  
in the middle.

### Unicode and Special Characters

#### Mathematical Symbols

α β γ δ ε ζ η θ ι κ λ μ ν ξ ο π ρ σ τ υ φ χ ψ ω

Σ Π Ω Δ Θ Λ Ξ Ψ Φ Γ

#### Currency Symbols

$ € £ ¥ ₽ ₹ ₩ ₪ ₫ ₦ ₱ ₴ ₸

#### Punctuation

— – ― ‐ ‑ ‒ ‐

‘ ’ “ ” « » ‹ ›

© ® ™ ° ± × ÷

#### Emoji

🎉 🚀 💡 ⭐ 🔥 ✅ ❌ ⚠️ 📊 📝 📈 📉 💎 🏆 🎯

#### Language Characters

中文 日本語 한국어 Español Français Deutsch

Русский العربية हिन्दी ภาษาไทย

### Escaped Characters

\*This is not italic\*

\_This is not italic\_

\# Not a heading

\- Not a list item

\`Not code\`

### HTML Entities

&amp; &lt; &gt; &quot; &apos; &copy; &reg; &trade;

### Long Text Wrapping

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

---

## Conclusion

This sample document demonstrates all the features supported by the MD Converter MVP:

| Feature | Status | Notes |
|---------|--------|-------|
| Headings | ✅ | Level 1-6 supported |
| Paragraphs | ✅ | Basic and formatted |
| Lists | ✅ | Ordered, unordered, nested, task |
| Tables | ✅ | Simple, aligned, formatted |
| Code Blocks | ✅ | Multiple languages |
| Inline Formatting | ✅ | Bold, italic, code |
| Links | ✅ | External, internal, formatted |
| Images | ✅ | Basic image support |
| Blockquotes | ✅ | Single, nested, with content |
| Horizontal Rules | ✅ | Multiple styles |
| ASCII Diagrams | ✅ | Converted to SVG |
| Nested Structures | ✅ | Complex nesting supported |
| Unicode | ✅ | International characters |
| Special Characters | ✅ | Proper escaping |

---

**End of Document**