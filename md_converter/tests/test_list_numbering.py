"""Tests for ordered-list numbering in the rendered DOCX."""

from pathlib import Path

from docx import Document

from md_converter.compiler import CompilerContext


def _compile_text(text: str, tmp_path: Path) -> Document:
    ctx = CompilerContext.create(
        {
            "diagram": False,
            "enable_cover": False,
            "toc": False,
            "style_tables": False,
        }
    )
    out = tmp_path / "out.docx"
    ctx.compile(text, output_path=out)
    return Document(str(out))


def _paragraph_texts(doc: Document) -> list:
    return [p.text for p in doc.paragraphs if p.text.strip()]


def test_ordered_lists_restart_numbering(tmp_path: Path) -> None:
    """多个有序列表应各自从 1 开始编号。"""
    text = "1. 甲\n" "2. 乙\n" "3. 丙\n\n" "**另一组条件：**\n\n" "1. A\n" "2. B\n"
    doc = _compile_text(text, tmp_path)
    texts = _paragraph_texts(doc)

    assert texts[0].startswith("1.")
    assert texts[1].startswith("2.")
    assert texts[2].startswith("3.")
    assert texts[4].startswith("1.")
    assert texts[5].startswith("2.")


def test_bold_only_paragraph_renders(tmp_path: Path) -> None:
    """纯加粗段落不应因空文本归一化而崩溃。"""
    text = "**若以下任一事件发生，应立即重新评估投资逻辑：**\n\n1. 甲\n2. 乙\n"
    doc = _compile_text(text, tmp_path)
    texts = _paragraph_texts(doc)

    assert texts[0].startswith("若以下任一事件")
    assert texts[1].startswith("1.")
    assert texts[2].startswith("2.")
