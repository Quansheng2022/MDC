"""Tests for the Markdown parser (token tree -> immutable AST)."""

from md_converter.ast.nodes import CodeBlock, Paragraph, Strong, Text
from md_converter.diagnostics.collector import DiagnosticCollector
from md_converter.parser.markdown_parser import MarkdownParser
from md_converter.parser.parser_context import ParserContext


def _parse(text: str):
    diag = DiagnosticCollector()
    ctx = ParserContext(diag=diag, config={}, frontmatter={})
    ast = MarkdownParser(ctx).parse(text)
    return ast, diag


def test_indented_code_block_parsed() -> None:
    """Indented (4-space) code blocks become CodeBlock nodes without MD003."""
    ast, diag = _parse("段落\n\n    缩进代码\n    第二行\n\n后续\n")

    code_blocks = [c for c in ast.children if isinstance(c, CodeBlock)]
    assert len(code_blocks) == 1
    assert code_blocks[0].language == ""
    assert code_blocks[0].text == "缩进代码\n第二行\n"
    assert not any(d.code == "MD003" for d in diag.diagnostics)


def test_fenced_code_block_keeps_language() -> None:
    """Fenced code blocks keep their language and produce no MD003."""
    ast, diag = _parse("```python\nprint(1)\n```\n")

    code_blocks = [c for c in ast.children if isinstance(c, CodeBlock)]
    assert len(code_blocks) == 1
    assert code_blocks[0].language == "python"
    assert not any(d.code == "MD003" for d in diag.diagnostics)


def test_cjk_bold_with_fullwidth_quotes_parsed() -> None:
    """**“内容”**汉字 应解析为 Strong（汉字计入侧翼标点）。"""
    ast, _ = _parse(
        "**\u201c\u91cf\u4ef7\u4e92\u52a8\u3001\u8d44\u91d1\u6d41\u5411\u3001"
        "\u7b79\u7801\u5206\u5e03\u201d**\u4e09\u7ef4"
    )
    para = ast.children[0]
    assert isinstance(para, Paragraph)
    assert any(isinstance(c, Strong) for c in para.content)


def test_cjk_bold_with_ascii_quotes_parsed() -> None:
    """**"内容"**汉字 也应解析为 Strong（ASCII 引号场景）。"""
    ast, _ = _parse(
        '**"\u5438\u7b79\u2014\u6d17\u76d8\u2014\u62c9\u5347\u2014\u6d3e\u53d1"**'
        "\u56db\u9636\u6bb5"
    )
    para = ast.children[0]
    assert isinstance(para, Paragraph)
    assert any(isinstance(c, Strong) for c in para.content)


def test_underscore_placeholder_not_parsed_as_hr() -> None:
    """`1. ______` 中的 ______ 应保留为文本，而不是被解析为水平线。"""
    ast, diag = _parse("1. ______\n2. ______\n")
    assert not any(d.code in ("LIST003", "LIST004") for d in diag.diagnostics)

    texts: list = []

    def collect(node):
        if isinstance(node, Text):
            texts.append(node.content)
        for child in node.iter_children():
            collect(child)

    collect(ast)
    assert texts == ["______", "______"]
