"""集成测试：AsciiToMermaidPass 与编译流水线。"""

from pathlib import Path

from md_converter.ast.nodes import CodeBlock, Diagram, Document
from md_converter.compiler import CompilerContext
from md_converter.diagnostics.collector import DiagnosticCollector
from md_converter.parser.markdown_parser import MarkdownParser
from md_converter.parser.parser_context import ParserContext
from md_converter.pipeline.passes.ascii_mermaid_pass import AsciiToMermaidPass

FLOWCHART_ASCII = """+--------+     +--------+
| Start  | --> |  Done  |
+--------+     +--------+
    |
    v
+--------+
|  End   |
+--------+
"""


def _make_document(nodes) -> Document:
    return Document(children=nodes)


def test_pass_converts_ascii_diagram_node() -> None:
    diag = DiagnosticCollector()
    document = _make_document([Diagram(diagram_type="ascii", content=FLOWCHART_ASCII)])
    result = AsciiToMermaidPass().run(document, diag)

    converted = result.document.children[0]
    assert isinstance(converted, Diagram)
    assert converted.diagram_type == "mermaid"
    assert converted.content.startswith("flowchart")
    assert result.metadata["stats"]["converted"] == 1


def test_pass_auto_detects_unlabeled_codeblock() -> None:
    diag = DiagnosticCollector()
    document = _make_document([CodeBlock(language="", text=FLOWCHART_ASCII)])
    result = AsciiToMermaidPass().run(document, diag)

    converted = result.document.children[0]
    assert isinstance(converted, Diagram)
    assert converted.diagram_type == "mermaid"


def test_pass_keeps_plain_code_block() -> None:
    diag = DiagnosticCollector()
    document = _make_document([CodeBlock(language="", text="def f():\n    return 1\n")])
    result = AsciiToMermaidPass().run(document, diag)

    assert isinstance(result.document.children[0], CodeBlock)
    assert result.metadata["stats"]["converted"] == 0


def test_pass_keeps_original_when_low_confidence() -> None:
    diag = DiagnosticCollector()
    # 单个无分节方框：既不是类图也不是内容盒，无法生成方案
    weak_ascii = """+------+
|  A   |
+------+
"""
    document = _make_document([Diagram(diagram_type="ascii", content=weak_ascii)])
    result = AsciiToMermaidPass().run(document, diag)

    assert isinstance(result.document.children[0], Diagram)
    assert result.document.children[0].diagram_type == "ascii"
    assert result.metadata["stats"]["converted"] == 0


def test_pass_preview_mode_writes_files(tmp_path: Path) -> None:
    diag = DiagnosticCollector()
    document = _make_document([Diagram(diagram_type="ascii", content=FLOWCHART_ASCII)])
    pass_instance = AsciiToMermaidPass(config={"mode": "preview", "preview_dir": str(tmp_path)})
    result = pass_instance.run(document, diag)

    mmd_files = list(tmp_path.glob("ascii_*.mmd"))
    assert mmd_files
    assert list(tmp_path.glob("preview_report_*.md"))
    assert list(tmp_path.glob("preview_report_*.json"))
    assert result.files
    assert result.metadata["stats"]["preview_written"] >= 1


def test_pass_interactive_mode_uses_selector() -> None:
    diag = DiagnosticCollector()
    document = _make_document([Diagram(diagram_type="ascii", content=FLOWCHART_ASCII)])

    def selector(plan):
        return plan.schemes[-1]

    pass_instance = AsciiToMermaidPass(config={"mode": "interactive", "selector": selector})
    result = pass_instance.run(document, diag)

    converted = result.document.children[0]
    assert isinstance(converted, Diagram)
    assert converted.diagram_type == "mermaid"


def test_compiler_context_registers_ascii_pass_before_diagram_pass() -> None:
    context = CompilerContext.create({"diagram": True})
    names = context.pass_registry.get_names()

    assert "AsciiToMermaidPass" in names
    assert "DiagramPass" in names
    passes = context.pass_registry.get_passes()
    order = [type(p).__name__ for p in passes]
    assert order.index("AsciiToMermaidPass") < order.index("DiagramPass")


def test_compiler_context_preview_mode_applies_config(tmp_path: Path) -> None:
    """注册表路径下 configure() 必须刷新 preview 模式参数。"""
    context = CompilerContext.create(
        {
            "diagram": True,
            "ascii_to_mermaid": {
                "enabled": True,
                "mode": "preview",
                "preview_dir": str(tmp_path),
            },
        }
    )
    pass_instance = context.pass_registry.get_pass("AsciiToMermaidPass")
    assert pass_instance is not None
    assert pass_instance.mode == "preview"
    assert pass_instance.preview_dir == str(tmp_path)


def test_compiler_end_to_end_ascii_to_mermaid(tmp_path: Path) -> None:
    markdown = "# Test\n\n" "```ascii\n" + FLOWCHART_ASCII + "```\n"
    context = CompilerContext.create(
        {
            "diagram": True,
            "output_dir": str(tmp_path),
            "enable_cover": False,
            "toc": False,
        }
    )
    output = tmp_path / "out.docx"
    doc = context.compile(markdown, output_path=output)

    assert output.exists()
    codes = {d.code for d in context.diag.diagnostics}
    assert "ASCI004" in codes  # 已转换
    assert doc is not None


def test_markdown_fence_renders_as_content() -> None:
    """```markdown 围栏内容应按 Markdown 解析（标题/表格成为真实节点）。"""
    text = (
        "```markdown\n"
        "## 3.2 功能需求\n\n"
        "| 类型 | 规范 |\n"
        "|------|------|\n"
        "| 类名 | PascalCase |\n"
        "```\n"
    )
    diag = DiagnosticCollector()
    ast = MarkdownParser(ParserContext(diag=diag, config={})).parse(text)

    headings = [n for n in ast.children if type(n).__name__ == "Heading"]
    tables = [n for n in ast.children if type(n).__name__ == "Table"]
    assert len(headings) == 1
    assert headings[0].to_plain_text() == "3.2 功能需求"
    assert len(tables) == 1


def test_gantt_fence_creates_mermaid_diagram() -> None:
    """```gantt 围栏应生成 Mermaid Diagram（gantt 为 Mermaid 语法）。"""
    text = "```gantt\n    title Project Timeline\n    dateFormat YYYY-MM-DD\n```\n"
    diag = DiagnosticCollector()
    ast = MarkdownParser(ParserContext(diag=diag, config={})).parse(text)

    diagrams = [n for n in ast.children if isinstance(n, Diagram) and n.diagram_type == "mermaid"]
    assert len(diagrams) == 1
    assert "Project Timeline" in diagrams[0].content
    assert diagrams[0].content.lstrip().startswith("gantt")


def test_rescues_swallowed_mermaid_in_code_block() -> None:
    """被围栏错配吞进代码块的 mermaid 内容应被抢救为 Diagram。"""
    diag = DiagnosticCollector()
    swallowed = (
        "**核心能力**：\n"
        "- 配置代码高亮\n\n"
        "```mermaid\n"
        "graph LR\n"
        "    A[Code Push] --> B[Build]\n"
        "```\n"
    )
    document = _make_document([CodeBlock(language="", text=swallowed)])
    result = AsciiToMermaidPass().run(document, diag)

    converted = result.document.children[0]
    assert isinstance(converted, Diagram)
    assert converted.diagram_type == "mermaid"
    assert "Code Push" in converted.content
