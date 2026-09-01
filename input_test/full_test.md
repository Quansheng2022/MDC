---
title: MD Converter Full Test
author: Test User
date: 2024-01-15
tags: [test, full, markdown]
---

# Heading 1

## Heading 2

### Heading 3

#### Heading 4

##### Heading 5

###### Heading 6

---

## Text Formatting

**Bold text** and *italic text* and ***bold italic***.

`Inline code` with **bold** and *italic*.

---

## Lists

### Unordered List

- Item 1
- Item 2
  - Sub-item 2.1
  - Sub-item 2.2
- Item 3

### Ordered List

1. First item
2. Second item
3. Third item

### Task List

- [x] Completed task
- [ ] Pending task

---

## Tables

| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1.1 | Cell 1.2 | Cell 1.3 |
| Cell 2.1 | Cell 2.2 | Cell 2.3 |

---
# Mermaid Diagram Test

```mermaid
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Process 1]
    B -->|No| D[Process 2]
    C --> E[End]
    D --> E
```	
----

## Code Blocks

```python
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b
```		
### 目录结构与模块职责

```mermaid
flowchart LR
    root["md_converter/"]

    root --> init["__init__.py"]
    root --> cli["cli.py<br/>Click CLI 入口"]
    root --> compiler["compiler.py<br/>CompilerContext 统一上下文"]
    root --> config["config.py<br/>配置加载（YAML）"]

    root --> constants["constants/"]
    constants --> node_type["node_type.py<br/>NodeType Enum"]

    root --> ast["ast/"]
    ast --> ast_nodes["nodes.py<br/>所有 AST 节点（含 SourceSpan）"]
    ast --> node_visitor["node_visitor.py<br/>NodeVisitor 基类"]

    root --> parser["parser/"]
    parser --> markdown_parser["markdown_parser.py<br/>markdown-it-py + SyntaxTree"]
    parser --> builder_registry["builder_registry.py<br/>NodeType → Builder 注册"]
    parser --> parser_context["parser_context.py<br/>ParserContext 数据类"]
    parser --> builders["builders/"]
    builders --> builder_base["base.py<br/>BlockBuilder 抽象"]
    builders --> heading_builder["heading.py"]
    builders --> paragraph_builder["paragraph.py"]
    builders --> list_builder["list.py"]
    builders --> table_builder["table.py"]
    builders --> code_builder["code.py"]
    builders --> blockquote_builder["blockquote.py"]
    builders --> inline_builder["inline.py<br/>迭代式构建行内节点"]

    root --> renderer["renderer/"]
    renderer --> word_renderer["word_renderer.py<br/>NodeVisitor 实现"]
    renderer --> word_writer["word_writer.py<br/>原子文档操作"]
    renderer --> render_context["render_context.py<br/>渲染状态"]
    renderer --> inline_state["inline_state.py<br/>样式栈"]
    renderer --> style_resolver["style_resolver.py<br/>样式决策器"]
    renderer --> themes["themes/"]
    themes --> default_theme["default.py<br/>默认主题"]

    root --> pipeline["pipeline/"]
    pipeline --> pipeline_core["pipeline.py<br/>Pipeline 执行器"]
    pipeline --> pass_registry["pass_registry.py<br/>Pass 注册"]
    pipeline --> plugin_discovery["plugin_discovery.py<br/>entry_points 加载"]
    pipeline --> passes["passes/"]
    passes --> pass_base["base.py<br/>TransformPass 基类"]
    passes --> normalize_pass["normalize_pass.py<br/>合并相邻 Text"]
    passes --> diagram_pass["diagram_pass.py<br/>Diagram → Image"]

    root --> services["services/"]
    services --> diagram_service["diagram_service.py<br/>ASCII → SVG 渲染"]

    root --> diagnostics["diagnostics/"]
    diagnostics --> diagnostic["diagnostic.py<br/>Diagnostic 类（含 code）"]
    diagnostics --> collector["collector.py<br/>DiagnosticCollector"]

    root --> utils["utils/"]
    utils --> helpers["helpers.py<br/>文件操作、frontmatter 解析"]

    root --> tests["tests/"]
    tests --> conftest["conftest.py"]
    tests --> test_golden["test_golden.py<br/>OOXML Snapshot 测试"]
    tests --> golden["golden/"]
    golden --> sample_md["sample.md"]
    golden --> sample_xml["sample.docx.xml"]
```

### 整体架构

```mermaid
flowchart TD
    input["用户输入（Markdown 文件）"] --> cli_parse

    subgraph cli["CLI（Click）"]
        direction TB
        cli_parse["解析命令行参数，读取配置文件"] --> cli_context["初始化 CompilerContext"]
    end

    cli_context --> parser_markdown

    subgraph parser["Parser Layer"]
        direction TB
        parser_markdown["markdown-it-py + SyntaxTree"] --> parser_builders["BuilderRegistry（按 NodeType）<br/>HeadingBuilder, ParagraphBuilder, ListBuilder,<br/>TableBuilder, CodeBuilder, BlockQuoteBuilder,<br/>Inline（迭代式构建）"]
        parser_builders --> ast["Immutable AST（带 SourceSpan）"]
    end

    ast --> pipeline_registry

    subgraph pipeline["Pipeline（插件化）"]
        direction TB
        pipeline_registry["PassRegistry + entry_points"] --> pipeline_passes["NormalizePass（合并文本）<br/>DiagramPass（ASCII → SVG）<br/>用户插件可注册"]
    end

    pipeline_passes --> renderer_visitor

    subgraph renderer["Renderer Layer"]
        direction TB
        renderer_visitor["WordRenderer（NodeVisitor）<br/>遍历 AST，调用 StyleResolver 获取样式，<br/>使用 InlineState 管理嵌套"] --> renderer_writer["WordWriter（原子操作）<br/>add_paragraph, add_run, start_table,<br/>add_cell, add_image, add_hrule"]
    end

    renderer_writer --> output["Word 文档（.docx）"]
```

---


# Mermaid Diagram Test

```mermaid
flowchart TD
    input["用户输入（Markdown 文件）"] --> cli_parse

    subgraph cli["CLI（Click）"]
        direction TB
        cli_parse["解析命令行参数，读取配置文件"] --> cli_context["初始化 CompilerContext"]
    end

    cli_context --> parser_markdown

    subgraph parser["Parser Layer"]
        direction TB
        parser_markdown["markdown-it-py + SyntaxTree"] --> parser_builders["BuilderRegistry（按 NodeType）<br/>Heading, Paragraph, List, Table,<br/>Code, BlockQuote, Inline（迭代式构建）"]
        parser_builders --> ast["Immutable AST（带 SourceSpan）"]
    end

    ast --> pipeline_registry

    subgraph pipeline["Pipeline（插件化）"]
        direction TB
        pipeline_registry["PassRegistry + entry_points"] --> pipeline_passes["NormalizePass（合并文本）<br/>DiagramPass（ASCII → SVG）<br/>用户插件可注册"]
    end

    pipeline_passes --> renderer_visitor

    subgraph renderer["Renderer Layer"]
        direction TB
        renderer_visitor["WordRenderer（NodeVisitor）<br/>遍历 AST，调用 StyleResolver 获取样式，<br/>使用 InlineState 管理嵌套"] --> renderer_writer["WordWriter（原子操作）<br/>add_paragraph, add_run, start_table,<br/>add_cell, add_image, add_hrule"]
    end

    renderer_writer --> output["Word 文档（.docx）"]
```

---
	
