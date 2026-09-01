"""
Paragraph Builder - 段落节点构建器

将 markdown-it-py 的 paragraph 节点转换为 AST Paragraph 节点。
"""

from typing import List, Optional

from markdown_it.tree import SyntaxTreeNode

from ...ast.nodes import Paragraph, SourceSpan
from ..parser_context import ParserContext
from .base import BlockBuilder
from .inline import build_inline_children


class ParagraphBuilder(BlockBuilder):
    """
    段落节点构建器。

    将 markdown-it-py 的 paragraph 节点转换为 Paragraph AST 节点。
    自动提取段落内容中的行内节点（粗体、斜体、链接、图片等）。
    """

    def build(self, node: SyntaxTreeNode, ctx: ParserContext) -> List[Paragraph]:
        """
        构建段落节点。

        参数:
            node: markdown-it-py 的 SyntaxTreeNode (type='paragraph')
            ctx: 解析器上下文

        返回:
            List[Paragraph]: 段落节点列表（通常只有一个）
        """
        if node.type != "paragraph":
            ctx.diag.warning(
                f"ParagraphBuilder received non-paragraph node: {node.type}",
                code="BUILD001",
                location=self.get_source_span(node)
            )
            return []

        # ✅ 关键修复：只处理 inline 子节点
        content = []
        for child in node.children:
            if child.type == "inline":
                content = build_inline_children(child, ctx)
                break

        # 如果没有找到 inline 子节点，尝试递归处理所有子节点（一般不会发生）
        if not content:
            for child in node.children:
                content.extend(build_inline_children(child, ctx))

        # 获取源码位置
        span = self.get_source_span(node)

        # 递增解析计数
        ctx.increment_blocks()

        # 创建段落节点
        paragraph = Paragraph(
            content=content,
            span=span,
        )

        return [paragraph]


# ============================================================
# 辅助函数
# ============================================================

def create_paragraph(
    content: List,
    span: Optional[SourceSpan] = None
) -> Paragraph:
    """
    创建段落节点的便捷函数。

    参数:
        content: 行内节点列表
        span: 源码位置

    返回:
        Paragraph: 段落节点

    示例:
        >>> para = create_paragraph([Text("Hello World")])
    """
    return Paragraph(content=content, span=span)


def is_paragraph_node(node: SyntaxTreeNode) -> bool:
    """
    检查是否为段落节点。

    参数:
        node: SyntaxTreeNode

    返回:
        bool: 是否为段落节点
    """
    return node.type == "paragraph"


def get_paragraph_text(node: SyntaxTreeNode) -> str:
    """
    提取段落的纯文本内容。

    参数:
        node: SyntaxTreeNode

    返回:
        str: 段落的纯文本内容
    """
    from .base import extract_text_content
    return extract_text_content(node).strip()


def is_empty_paragraph(node: SyntaxTreeNode) -> bool:
    """
    检查是否为空段落（没有内容或只有空白字符）。

    参数:
        node: SyntaxTreeNode

    返回:
        bool: 是否为空段落
    """
    if not node.children:
        return True

    text = get_paragraph_text(node)
    return not text or text.isspace()


def normalize_paragraph_content(content: List) -> List:
    """
    规范化段落内容。

    合并相邻的 Text 节点，去除多余空白。

    参数:
        content: 行内节点列表

    返回:
        List: 规范化后的行内节点列表

    示例:
        >>> content = [Text("Hello "), Text("World")]
        >>> normalized = normalize_paragraph_content(content)
        >>> # 结果: [Text("Hello World")]
    """
    if not content:
        return []

    normalized = []
    current_text = ""

    for node in content:
        if hasattr(node, "content") and isinstance(node.content, str):
            # 如果是文本节点，合并
            if isinstance(node, type(content[0])):  # 简单处理
                current_text += node.content
            else:
                if current_text:
                    normalized.append(Text(content=current_text))
                    current_text = ""
                normalized.append(node)
        else:
            if current_text:
                normalized.append(Text(content=current_text))
                current_text = ""
            normalized.append(node)

    if current_text:
        normalized.append(Text(content=current_text))

    return normalized


# 导入 Text 节点（用于 normalize 函数）
from ...ast.nodes import Text