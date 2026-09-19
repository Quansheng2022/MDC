"""
MD Converter - Markdown to DOCX Compiler

A compiler-architecture based converter with immutable AST, pipeline, and plugin support.
"""

__version__ = "1.0.0"

# 导出核心类
from .ast.nodes import (
    CodeBlock,
    Document,
    Emphasis,
    Heading,
    Image,
    InlineCode,
    Link,
    ListBlock,
    Node,
    Paragraph,
    Strong,
    Table,
    Text,
)
from .compiler import CompilerContext
from .renderer.themes.default import DefaultTheme

__all__ = [
    "__version__",
    "CompilerContext",
    "DefaultTheme",
    "Node",
    "Document",
    "Heading",
    "Paragraph",
    "ListBlock",
    "Table",
    "CodeBlock",
    "Image",
    "Strong",
    "Emphasis",
    "InlineCode",
    "Link",
    "Text",
    "convert",
]


def convert(markdown_text: str, config: dict = None, theme=None):
    """
    将 Markdown 文本转换为 python-docx Document 对象。

    参数:
        markdown_text (str): Markdown 源文本。
        config (dict, optional): 配置字典，如 {'output_dir': './output'}。
        theme (object, optional): 主题实例；默认使用 canonical compiler 默认主题。

    返回:
        docx.Document: 生成的 Word 文档对象，可进一步保存或处理。

    示例:
        >>> from md_converter import convert
        >>> doc = convert("# Hello\\n\\nThis is **bold** text.")
        >>> doc.save("output.docx")
    """
    from .compiler import compile_markdown

    return compile_markdown(markdown_text, config=config, theme=theme)
