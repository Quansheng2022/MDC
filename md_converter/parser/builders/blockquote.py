"""
BlockQuote Builder - 引用块节点构建器

将 markdown-it-py 的 blockquote 节点转换为 AST BlockQuote 节点。
"""

from typing import List, Optional

from markdown_it.tree import SyntaxTreeNode

from ...ast.nodes import BlockQuote, SourceSpan
from ..parser_context import ParserContext
from .base import BlockBuilder


class BlockQuoteBuilder(BlockBuilder):
    """
    引用块节点构建器。

    将 markdown-it-py 的 blockquote 节点转换为 BlockQuote AST 节点。
    支持嵌套引用块和包含其他块元素（段落、列表、代码块等）。

    示例:
        输入:
            > This is a quote
            > With multiple lines

        输出:
            BlockQuote(
                children=[
                    Paragraph(content=[Text("This is a quote")]),
                    Paragraph(content=[Text("With multiple lines")])
                ]
            )

        输入:
            > ### Heading in quote
            > - List item 1
            > - List item 2

        输出:
            BlockQuote(
                children=[
                    Heading(level=3, content=[Text("Heading in quote")]),
                    ListBlock(
                        ordered=False,
                        items=[
                            ListItem(children=[Paragraph(content=[Text("List item 1")])]),
                            ListItem(children=[Paragraph(content=[Text("List item 2")])])
                        ]
                    )
                ]
            )
    """

    def build(self, node: SyntaxTreeNode, ctx: ParserContext) -> List[BlockQuote]:
        """
        构建引用块节点。

        参数:
            node: markdown-it-py 的 SyntaxTreeNode (type='blockquote')
            ctx: 解析器上下文

        返回:
            List[BlockQuote]: 引用块节点列表（通常只有一个）
        """
        if node.type != "blockquote":
            ctx.diag.warning(
                f"BlockQuoteBuilder received non-blockquote node: {node.type}",
                code="BUILD001",
                location=self.get_source_span(node)
            )
            return []

        # 构建引用块内的子节点
        children = self._build_children(node, ctx)

        # 获取源码位置
        span = self.get_source_span(node)

        # 递增解析计数
        ctx.increment_blocks()

        # 创建引用块节点
        quote = BlockQuote(
            children=children,
            span=span,
        )

        return [quote]

    def _build_children(
        self,
        node: SyntaxTreeNode,
        ctx: ParserContext
    ) -> List:
        """
        构建引用块内的子节点列表。

        参数:
            node: 引用块节点
            ctx: 解析器上下文

        返回:
            List[Node]: 子节点列表
        """
        from .code import CodeBuilder
        from .heading import HeadingBuilder
        from .list import ListBuilder
        from .paragraph import ParagraphBuilder
        from .table import TableBuilder

        children = []

        for child in node.children:
            # 递归处理嵌套引用块
            if child.type == "blockquote":
                quote_nodes = self.build(child, ctx)
                children.extend(quote_nodes)
                continue

            # 根据子节点类型构建
            if child.type == "heading":
                builder = HeadingBuilder()
                nodes = builder.build(child, ctx)
                children.extend(nodes)

            elif child.type == "paragraph":
                builder = ParagraphBuilder()
                nodes = builder.build(child, ctx)
                children.extend(nodes)

            elif child.type in ("bullet_list", "ordered_list"):
                builder = ListBuilder(ordered=(child.type == "ordered_list"))
                nodes = builder.build(child, ctx)
                children.extend(nodes)

            elif child.type == "fence":
                builder = CodeBuilder()
                nodes = builder.build(child, ctx)
                children.extend(nodes)

            elif child.type == "table":
                builder = TableBuilder()
                nodes = builder.build(child, ctx)
                children.extend(nodes)

            else:
                # 未知节点类型，记录警告
                ctx.diag.warning(
                    f"Unhandled child node type in quote: {child.type}",
                    code="QUOTE002",
                    location=self.get_source_span(child)
                )
                # 尝试提取文本内容
                if child.children:
                    # 递归处理子节点
                    for sub_child in child.children:
                        if sub_child.type == "paragraph":
                            builder = ParagraphBuilder()
                            nodes = builder.build(sub_child, ctx)
                            children.extend(nodes)

        return children


# ============================================================
# 辅助函数
# ============================================================

def create_block_quote(
    children: List,
    span: Optional[SourceSpan] = None
) -> BlockQuote:
    """
    创建引用块节点的便捷函数。

    参数:
        children: 子节点列表
        span: 源码位置

    返回:
        BlockQuote: 引用块节点

    示例:
        >>> para = Paragraph(content=[Text("Quote text")])
        >>> quote = create_block_quote([para])
    """
    return BlockQuote(children=children, span=span)


def is_block_quote_node(node: SyntaxTreeNode) -> bool:
    """
    检查是否为引用块节点。

    参数:
        node: SyntaxTreeNode

    返回:
        bool: 是否为引用块节点
    """
    return node.type == "blockquote"


def extract_quote_text(node: SyntaxTreeNode) -> str:
    """
    提取引用块的纯文本内容。

    参数:
        node: SyntaxTreeNode

    返回:
        str: 引用块的纯文本内容
    """
    from .base import extract_text_content
    return extract_text_content(node).strip()


def get_quote_depth(node: SyntaxTreeNode, current_depth: int = 0) -> int:
    """
    获取引用块的嵌套深度。

    参数:
        node: SyntaxTreeNode
        current_depth: 当前深度

    返回:
        int: 最大嵌套深度
    """
    if not is_block_quote_node(node):
        return current_depth

    max_depth = current_depth + 1
    for child in node.children:
        if is_block_quote_node(child):
            depth = get_quote_depth(child, current_depth + 1)
            max_depth = max(max_depth, depth)

    return max_depth


def count_quote_lines(node: SyntaxTreeNode) -> int:
    """
    计算引用块的行数（近似）。

    参数:
        node: SyntaxTreeNode

    返回:
        int: 行数
    """
    text = extract_quote_text(node)
    if not text:
        return 0
    return len(text.splitlines())


def is_empty_quote(node: SyntaxTreeNode) -> bool:
    """
    检查是否为空引用块。

    参数:
        node: SyntaxTreeNode

    返回:
        bool: 是否为空引用块
    """
    if not node.children:
        return True

    text = extract_quote_text(node)
    return not text or text.isspace()


def get_quote_content_types(node: SyntaxTreeNode) -> List[str]:
    """
    获取引用块内子节点的类型列表。

    参数:
        node: SyntaxTreeNode

    返回:
        List[str]: 子节点类型列表
    """
    types = []
    for child in node.children:
        types.append(child.type)
    return types