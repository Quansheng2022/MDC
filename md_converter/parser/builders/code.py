"""
Code Builder - 代码块节点构建器

将 markdown-it-py 的 fence 节点转换为 AST CodeBlock 或 Diagram 节点。
只负责识别，不负责渲染。

仅当语言显式声明为图表类型（如 mermaid, ascii, diagram 等）时，
才创建 Diagram 节点。其他所有代码块均保持为 CodeBlock。
"""

from __future__ import annotations

import re
from typing import Final, List, Optional

from markdown_it.tree import SyntaxTreeNode

from ...ast.nodes import CodeBlock, Diagram, SourceSpan
from ..parser_context import ParserContext
from .base import BlockBuilder

# 支持显式声明为图表的语言
DIAGRAM_LANGUAGES: Final[set[str]] = {
    "mermaid",
    "gantt",
    "plantuml",
    "graphviz",
    "dot",
    "uml",
    "ascii",
    "diagram",
}


class CodeBuilder(BlockBuilder):
    """
    代码块节点构建器。

    将 markdown-it-py 的 fence / code_block 节点转换为 CodeBlock 或 Diagram AST 节点。
    只负责识别图表类型，不负责渲染。
    """

    def build(self, node: SyntaxTreeNode, ctx: ParserContext) -> List:
        """
        构建代码块或图表节点。

        参数:
            node: markdown-it-py 的 SyntaxTreeNode (type='fence' 或 'code_block')
            ctx: 解析器上下文

        返回:
            List[Union[CodeBlock, Diagram]]: 节点列表（通常只有一个）
        """
        if node.type not in ("fence", "code_block"):
            ctx.diag.warning(
                f"CodeBuilder received unsupported node: {node.type}",
                code="BUILD001",
                location=self.get_source_span(node),
            )
            return []

        # 提取代码块信息
        language = (getattr(node, "info", "") or "").strip()
        content = node.content or ""

        # 获取源码位置
        span = self.get_source_span(node)

        # ✅ ```markdown 围栏：内容按 Markdown 重新解析
        # （标题/表格/列表渲染为真实 Word 元素，而非等宽代码）
        if language.lower() in ("markdown", "md"):
            return self._parse_markdown_fence(content, ctx, span)

        # ✅ 只有显式声明的语言才转换为 Diagram
        if language.lower() in DIAGRAM_LANGUAGES:
            # 对于 mermaid/plantuml 等，保留原语言作为 diagram_type
            # 对于 ascii/diagram，统一使用 "ascii"
            if language.lower() in ("ascii", "diagram"):
                diagram_type = "ascii"
            else:
                # gantt 等也是 Mermaid 语法，统一交给 Mermaid 渲染
                diagram_type = (
                    "mermaid" if language.lower() in ("mermaid", "gantt") else language.lower()
                )

            ctx.diag.info(
                f"Detected {diagram_type} diagram with {len(content.splitlines())} lines",
                code="INFO003",
                location=span,
            )
            if diagram_type == "mermaid":
                content = self._ensure_mermaid_header(language.lower(), content)
            return [
                Diagram(
                    diagram_type=diagram_type,
                    content=content,
                    span=span,
                )
            ]

        # 其他所有代码块（包括 text, python, bash 等）保持 CodeBlock
        return [
            CodeBlock(
                language=language,
                text=content,
                span=span,
            )
        ]

    @staticmethod
    def _ensure_mermaid_header(lang: str, content: str) -> str:
        """
        确保 Mermaid 内容带类型关键字首行。

        ```gantt 围栏内容以 `title` 开头，缺少 `gantt` 类型关键字，
        直接解析会报 "No diagram type detected"。
        """
        stripped = content.lstrip()
        if re.match(
            r"^(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|"
            r"mindmap|gantt|pie|journey|timeline|erDiagram|gitGraph)\b",
            stripped,
        ):
            return content
        if lang == "gantt":
            return "gantt\n" + content
        return content

    def _parse_markdown_fence(
        self,
        content: str,
        ctx: ParserContext,
        span: Optional[SourceSpan],
    ) -> List:
        """
        将 ```markdown 围栏内容按 Markdown 重新解析为块节点。

        限制嵌套深度，防止 ```markdown 内再嵌套 ```markdown 时无限递归。
        """
        depth = int(ctx.custom_data.get("markdown_fence_depth", 0))
        if depth >= 2:
            return [CodeBlock(language="markdown", text=content, span=span)]

        from ..markdown_parser import MarkdownParser

        nested_ctx = ParserContext(
            diag=ctx.diag,
            config=ctx.config,
            frontmatter=ctx.frontmatter,
            custom_data={**ctx.custom_data, "markdown_fence_depth": depth + 1},
        )
        parser = MarkdownParser(nested_ctx)
        try:
            doc = parser.parse(content)
        except Exception as e:
            ctx.diag.warning(
                f"Failed to re-parse markdown fence: {e}",
                code="BUILD002",
                location=span,
            )
            return [CodeBlock(language="markdown", text=content, span=span)]
        return list(doc.children)
