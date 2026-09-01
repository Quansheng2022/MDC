"""
Horizontal Rule Builder - 水平分割线节点构建器

将 markdown-it-py 的 hr 节点转换为 AST HorizontalRule 节点。
"""

from typing import List, Optional

from markdown_it.tree import SyntaxTreeNode

from ...ast.nodes import HorizontalRule, SourceSpan
from ..parser_context import ParserContext
from .base import BlockBuilder


class HorizontalRuleBuilder(BlockBuilder):
    """
    水平分割线节点构建器。

    将 markdown-it-py 的 hr 节点转换为 HorizontalRule AST 节点。

    示例:
        输入: ---
        输出: HorizontalRule()
    """

    def build(self, node: SyntaxTreeNode, ctx: ParserContext) -> List[HorizontalRule]:
        """
        构建水平分割线节点。

        参数:
            node: markdown-it-py 的 SyntaxTreeNode (type='hr')
            ctx: 解析器上下文

        返回:
            List[HorizontalRule]: 水平分割线节点列表（通常只有一个）
        """
        if node.type != "hr":
            ctx.diag.warning(
                f"HorizontalRuleBuilder received non-hr node: {node.type}",
                code="BUILD001",
                location=self.get_source_span(node)
            )
            return []

        # 获取源码位置
        span = self.get_source_span(node)

        # 递增解析计数
        ctx.increment_blocks()

        # 创建水平分割线节点
        return [HorizontalRule(span=span)]


# ============================================================
# 辅助函数
# ============================================================

def create_horizontal_rule(span: Optional[SourceSpan] = None) -> HorizontalRule:
    """
    创建水平分割线节点的便捷函数。

    参数:
        span: 源码位置

    返回:
        HorizontalRule: 水平分割线节点
    """
    return HorizontalRule(span=span)


def is_horizontal_rule_node(node: SyntaxTreeNode) -> bool:
    """
    检查是否为水平分割线节点。

    参数:
        node: SyntaxTreeNode

    返回:
        bool: 是否为水平分割线节点
    """
    return node.type == "hr"