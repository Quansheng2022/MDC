"""
Heading Builder - 标题节点构建器

将 markdown-it-py 的 heading 节点转换为 AST Heading 节点。
"""

from typing import List, Optional

from markdown_it.tree import SyntaxTreeNode

from ...ast.nodes import Heading, SourceSpan
from ..parser_context import ParserContext
from .base import BlockBuilder
from .inline import build_inline_children


class HeadingBuilder(BlockBuilder):
    """
    标题节点构建器。

    将 markdown-it-py 的 heading 节点转换为 Heading AST 节点。
    支持 h1-h6 级别，并提取标题内容中的行内节点。
    """

    def build(self, node: SyntaxTreeNode, ctx: ParserContext) -> List[Heading]:
        """
        构建标题节点。

        参数:
            node: markdown-it-py 的 SyntaxTreeNode (type='heading')
            ctx: 解析器上下文

        返回:
            List[Heading]: 标题节点列表（通常只有一个）
        """
        if node.type != "heading":
            ctx.diag.warning(
                f"HeadingBuilder received non-heading node: {node.type}",
                code="BUILD001",
                location=self.get_source_span(node)
            )
            return []

        # 提取标题级别
        level = self._extract_level(node)

        # 验证级别
        if level < 1 or level > 6:
            ctx.diag.warning(
                f"Invalid heading level: {level}, defaulting to 1",
                code="BUILD002",
                location=self.get_source_span(node)
            )
            level = 1

        # ✅ 正确方式：只提取 inline 子节点的内容
        content = []
        for child in node.children:
            if child.type == "inline":
                content = build_inline_children(child, ctx)
                break

        # 如果没有找到 inline 子节点，尝试处理所有子节点（备用）
        if not content:
            for child in node.children:
                content.extend(build_inline_children(child, ctx))

        # 获取源码位置
        span = self.get_source_span(node)

        # 递增解析计数
        ctx.increment_blocks()

        # 创建标题节点
        heading = Heading(
            level=level,
            content=content,
            span=span,
        )

        return [heading]

    def _extract_level(self, node: SyntaxTreeNode) -> int:
        """
        从节点提取标题级别。

        支持两种方式：
        1. 从 node.tag 提取 (h1 -> 1)
        2. 从 node.attrs 提取

        参数:
            node: SyntaxTreeNode

        返回:
            int: 标题级别 (1-6)
        """
        if node.tag and node.tag.startswith("h"):
            try:
                return int(node.tag[1])
            except (ValueError, IndexError):
                pass

        if hasattr(node, "attrs") and node.attrs:
            level = node.attrs.get("level")
            if level is not None:
                try:
                    return int(level)
                except (ValueError, TypeError):
                    pass

        return 1


# ============================================================
# 辅助函数
# ============================================================

def create_heading(
    level: int,
    content: List,
    span: Optional[SourceSpan] = None
) -> Heading:
    if level < 1:
        level = 1
    elif level > 6:
        level = 6
    return Heading(level=level, content=content, span=span)


def is_heading_node(node: SyntaxTreeNode) -> bool:
    return node.type == "heading" and node.tag and node.tag.startswith("h")


def get_heading_level(node: SyntaxTreeNode) -> Optional[int]:
    if not is_heading_node(node):
        return None
    try:
        return int(node.tag[1])
    except (ValueError, IndexError):
        return None