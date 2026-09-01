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
        theme (object, optional): 主题实例，默认为 DefaultTheme。

    返回:
        docx.Document: 生成的 Word 文档对象，可进一步保存或处理。

    示例:
        >>> from md_converter import convert
        >>> doc = convert("# Hello\\n\\nThis is **bold** text.")
        >>> doc.save("output.docx")
    """
    from .compiler import CompilerContext
    from .diagnostics.collector import DiagnosticCollector
    from .parser.parser_context import ParserContext
    from .pipeline.pass_registry import PassRegistry
    from .pipeline.passes.ascii_mermaid_pass import AsciiToMermaidPass
    from .pipeline.passes.diagram_pass import DiagramPass
    from .pipeline.passes.normalize_pass import NormalizePass
    from .pipeline.plugin_discovery import discover_passes
    from .renderer.render_context import RenderContext

    if config is None:
        config = {}
    if theme is None:
        theme = DefaultTheme()

    diag = DiagnosticCollector()
    parser_ctx = ParserContext(diag=diag, config=config)
    render_ctx = RenderContext(theme=theme, diag=diag)

    pass_registry = PassRegistry()
    # 注册内置 Pass
    pass_registry.register(NormalizePass)
    pass_registry.register(AsciiToMermaidPass)
    pass_registry.register(DiagramPass)
    # 发现外部插件
    for pass_inst in discover_passes():
        pass_registry._pass_classes.append(type(pass_inst))

    ctx = CompilerContext(
        diag=diag,
        config=config,
        parser_ctx=parser_ctx,
        render_ctx=render_ctx,
        pass_registry=pass_registry,
    )
    return ctx.compile(markdown_text)
	
