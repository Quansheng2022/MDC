"""
空白对齐简单表格识别（P12-CAND-001 / S/N 118 实现包 001）。

覆盖:
    - 纯识别规则：正例、ruler 装饰性对齐、各类负例（散文 / 位移间隙 / 围栏 / 富文本 / 管道）
    - Pass 行为：原位转换为 Table、其余节点不变、幂等、默认不产生诊断（CLAR-01）
    - 端到端：交付 DOCX 出现真实表格；配置关闭时不转换
"""

from pathlib import Path
from typing import Any, List

from docx import Document as DocxDocument

from md_converter.ast.nodes import Document, Paragraph, Table
from md_converter.compiler import CompilerContext
from md_converter.diagnostics.collector import DiagnosticCollector
from md_converter.parser.markdown_parser import parse_markdown
from md_converter.pipeline.passes.simple_table_pass import (
    SimpleTablePass,
    paragraph_lines,
    recognize_simple_table,
)

#: 真实语料派生的最小化样本（ruler 为装饰性，与数据列不对齐）
CORPUS_STYLE_BLOCK = (
    "  普通软件工程关注   Governance Engineering 额外关注\n"
    "  ------------------ -------------------------------------------------\n"
    "  代码是否能运行     AI是否有权这样修改\n"
    "  测试是否通过       测试是否覆盖正确 authority\n"
)

ASCII_BLOCK = (
    "Name        Description\n"
    "----------  -----------\n"
    "Alpha       First item\n"
    "Beta        Second item\n"
)


def _parse(text: str) -> Document:
    """解析 Markdown 为 AST。"""
    return parse_markdown(text, DiagnosticCollector())


def _run_pass(text: str) -> Any:
    """解析并运行 SimpleTablePass。"""
    diag = DiagnosticCollector()
    doc = parse_markdown(text, diag)
    result = SimpleTablePass().run(doc, diag)
    return result, doc, diag


def test_recognize_corpus_style_block() -> None:
    """语料派生的两列块被识别为 1 表头 + 2 数据行（行经 Parser 重建）。"""
    doc = _parse(CORPUS_STYLE_BLOCK)
    paragraph = next(node for node in doc.children if isinstance(node, Paragraph))
    lines = paragraph_lines(paragraph)

    assert lines is not None
    # Parser 已消费块级缩进：行首不再有空格
    assert lines[0].startswith("普通软件工程关注")

    rows = recognize_simple_table(lines)

    assert rows is not None
    assert len(rows) == 3
    assert rows[0] == ["普通软件工程关注", "Governance Engineering 额外关注"]
    assert rows[1] == ["代码是否能运行", "AI是否有权这样修改"]
    assert rows[2] == ["测试是否通过", "测试是否覆盖正确 authority"]


def test_recognize_ascii_block() -> None:
    """纯 ASCII 块使用公共锚点切分单元格。"""
    rows = recognize_simple_table(ASCII_BLOCK.rstrip("\n").split("\n"))

    assert rows is not None
    assert rows[0] == ["Name", "Description"]
    assert rows[2] == ["Beta", "Second item"]


def test_recognize_rejects_normal_prose() -> None:
    """普通散文（无 ruler）不识别。"""
    lines = ["This is a paragraph.", "It continues on a second line.", "And a third."]

    assert recognize_simple_table(lines) is None


def test_recognize_rejects_shifting_gaps() -> None:
    """列间隔位移的换行字段列表不识别（真实语料负例）。"""
    lines = [
        "（不可变对象）：",
        "decision_id / stock / date / inst_state / permission /  /",
        " / setup_type / prev_fsm / next_fsm / prev_position /",
    ]

    assert recognize_simple_table(lines) is None


def test_recognize_rejects_inconsistent_columns() -> None:
    """ruler 存在但数据列不一致时不识别。"""
    lines = [
        "Name   Description   Notes",
        "----   -----------   -----",
        "Alpha  First         N1",
    ]

    assert recognize_simple_table(lines) is None


def test_recognize_rejects_empty_cell() -> None:
    """单元格为空时不识别（宁可漏识别）。"""
    lines = [
        "Name        Description",
        "----------  -----------",
        "            Only right",
    ]

    assert recognize_simple_table(lines) is None


def test_recognize_rejects_pipe_and_tab() -> None:
    """含管道符或制表符时不识别。"""
    piped = [
        "Name | A      Description",
        "------------  -----------",
        "Alpha         First item",
    ]
    tabbed = [
        "Name\t        Description",
        "----------  -----------",
        "Alpha       First item",
    ]

    assert recognize_simple_table(piped) is None
    assert recognize_simple_table(tabbed) is None


def test_paragraph_lines_rejects_rich_inline() -> None:
    """包含行内格式的段落不可重建为纯文本行（R7）。"""
    doc = _parse("**Name**   Value\n----------  -----\nAlpha       Beta\n")
    paragraph = next(node for node in doc.children if isinstance(node, Paragraph))

    assert paragraph_lines(paragraph) is None


def test_pass_converts_paragraph_in_place() -> None:
    """识别成功的段落原位替换为 Table，且不产生诊断（CLAR-01）。"""
    result, _doc, diag = _run_pass(f"# Title\n\n{CORPUS_STYLE_BLOCK}\nAfter text.\n")

    types = [type(node).__name__ for node in result.document.children]
    assert "Table" in types
    table = next(node for node in result.document.children if isinstance(node, Table))
    assert len(table.rows) == 3
    assert len(table.rows[0].cells) == 2
    assert table.rows[0].cells[0].to_plain_text() == "普通软件工程关注"
    assert table.rows[2].cells[1].to_plain_text() == "测试是否覆盖正确 authority"
    assert result.metadata["stats"]["converted"] == 1
    assert diag.diagnostics == []


def test_pass_is_idempotent() -> None:
    """第二次运行不重复转换，结果稳定。"""
    first, _doc, _diag = _run_pass(CORPUS_STYLE_BLOCK)
    assert isinstance(first.document, Document)

    again = SimpleTablePass().run(first.document, DiagnosticCollector())

    assert again.metadata["stats"]["converted"] == 0
    assert [type(n).__name__ for n in again.document.children] == [
        type(n).__name__ for n in first.document.children
    ]


def test_pass_leaves_other_nodes_untouched() -> None:
    """围栏代码块、普通段落与既有管道表格保持不变。"""
    text = (
        "Prose paragraph.\n\n"
        "```\n"
        "Name        Description\n"
        "----------  -----------\n"
        "Alpha       First item\n"
        "```\n\n"
        "| A | B |\n| --- | --- |\n| 1 | 2 |\n"
    )
    result, _doc, diag = _run_pass(text)

    kinds = [type(node).__name__ for node in result.document.children]
    assert kinds.count("Table") == 1  # 仅既有管道表格
    assert "CodeBlock" in kinds
    assert result.metadata["stats"]["converted"] == 0
    assert diag.diagnostics == []


def test_pass_ambiguous_ruler_block_keeps_paragraph_without_diagnostic() -> None:
    """ruler 存在但结构不满足时保留段落且不产生任何诊断（CLAR-01）。"""
    text = "Name   Description   Notes\n----   -----------   -----\nAlpha  First         N1\n"
    result, _doc, diag = _run_pass(text)

    assert all(not isinstance(node, Table) for node in result.document.children)
    assert result.metadata["stats"]["converted"] == 0
    assert diag.diagnostics == []


def test_compiler_end_to_end_renders_table(tmp_path: Path) -> None:
    """端到端：交付 DOCX 中出现真实表格且文本无损。"""
    body = f"# Simple Table\n\n{CORPUS_STYLE_BLOCK}\nPlain prose stays prose.\n"
    output_path = tmp_path / "simple_table.docx"
    ctx = CompilerContext.create({"word_com": False, "verbose": False})
    ctx.compile(body, {}, output_path)

    doc = DocxDocument(str(output_path))
    assert len(doc.tables) == 1
    cells: List[str] = [cell.text for row in doc.tables[0].rows for cell in row.cells]
    assert cells[0] == "普通软件工程关注"
    assert "测试是否覆盖正确 authority" in cells
    assert ctx.final_artifact_qa_result is not None
    assert ctx.final_artifact_qa_result.metrics.get("content_coverage", 1.0) == 1.0


def test_compiler_config_can_disable_recognition(tmp_path: Path) -> None:
    """simple_tables.enabled = false 时不转换（可回滚开关）。"""
    body = f"# Simple Table\n\n{CORPUS_STYLE_BLOCK}\n"
    output_path = tmp_path / "disabled.docx"
    ctx = CompilerContext.create(
        {"word_com": False, "verbose": False, "simple_tables": {"enabled": False}}
    )
    ctx.compile(body, {}, output_path)

    doc = DocxDocument(str(output_path))
    assert len(doc.tables) == 0
    paragraphs = "\n".join(p.text for p in doc.paragraphs)
    assert "普通软件工程关注" in paragraphs


def test_config_validation_rejects_bad_simple_tables() -> None:
    """配置校验：simple_tables 必须为映射且 enabled 为布尔。"""
    from md_converter.config import resolve_config, validate_config

    assert any("simple_tables" in err for err in validate_config({"simple_tables": "yes"}))
    assert any(
        "simple_tables.enabled" in err
        for err in validate_config({"simple_tables": {"enabled": "yes"}})
    )
    assert resolve_config()["simple_tables"] == {"enabled": True}
