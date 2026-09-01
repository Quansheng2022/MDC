"""
List Builder - 列表节点构建器

将 markdown-it-py 的列表节点转换为 AST ListBlock 和 ListItem 节点。
支持有序列表和无序列表，以及嵌套列表。
"""

from typing import List, Optional

from markdown_it.tree import SyntaxTreeNode

from ...ast.nodes import ListBlock, ListItem, Node, Paragraph, SourceSpan
from ..parser_context import ParserContext
from .base import BlockBuilder
from .blockquote import BlockQuoteBuilder
from .code import CodeBuilder
from .heading import HeadingBuilder
from .paragraph import ParagraphBuilder


class ListBuilder(BlockBuilder):
    """
    列表节点构建器。

    将 markdown-it-py 的 bullet_list 或 ordered_list 节点
    转换为 ListBlock AST 节点。

    支持:
        - 有序列表 (ordered=True)
        - 无序列表 (ordered=False)
        - 嵌套列表（自动递归处理）
        - 列表项包含段落、代码块、引用块等

    示例:
        输入:
            - Item 1
            - Item 2
              - Sub-item 2.1

        输出:
            ListBlock(
                ordered=False,
                items=[
                    ListItem(children=[Paragraph(content=[Text("Item 1")])]),
                    ListItem(
                        children=[
                            Paragraph(content=[Text("Item 2")]),
                            ListBlock(
                                ordered=False,
                                items=[ListItem(children=[Paragraph(content=[Text("Sub-item 2.1")])])]
                            )
                        ]
                    )
                ]
            )
    """

    def __init__(self, ordered: bool = False):
        """
        初始化列表构建器。

        参数:
            ordered: 是否为有序列表
        """
        self.ordered = ordered

    def build(self, node: SyntaxTreeNode, ctx: ParserContext) -> List[ListBlock]:
        """
        构建列表节点。

        参数:
            node: markdown-it-py 的 SyntaxTreeNode (type='bullet_list' 或 'ordered_list')
            ctx: 解析器上下文

        返回:
            List[ListBlock]: 列表节点列表（通常只有一个）
        """
        if node.type not in ("bullet_list", "ordered_list"):
            ctx.diag.warning(
                f"ListBuilder received non-list node: {node.type}",
                code="BUILD001",
                location=self.get_source_span(node)
            )
            return []

        # 判断是否为有序列表
        ordered = node.type == "ordered_list"

        # 提取列表项
        items = self._build_list_items(node, ctx)

        # 获取源码位置
        span = self.get_source_span(node)

        # 递增解析计数
        ctx.increment_blocks()

        # 创建列表节点
        list_block = ListBlock(
            ordered=ordered,
            items=items,
            span=span,
        )

        return [list_block]

    def _build_list_items(
        self,
        node: SyntaxTreeNode,
        ctx: ParserContext
    ) -> List[ListItem]:
        """
        构建列表项列表。

        参数:
            node: 列表节点 (bullet_list 或 ordered_list)
            ctx: 解析器上下文

        返回:
            List[ListItem]: 列表项节点列表
        """
        items = []

        for child in node.children:
            if child.type == "list_item":
                item = self._build_list_item(child, ctx)
                if item:
                    items.append(item)
            else:
                # 不是列表项，记录警告
                ctx.diag.warning(
                    f"Unexpected child in list: {child.type}",
                    code="LIST001",
                    location=self.get_source_span(child)
                )

        return items

    def _build_list_item(
        self,
        node: SyntaxTreeNode,
        ctx: ParserContext
    ) -> Optional[ListItem]:
        """
        构建单个列表项。

        参数:
            node: markdown-it-py 的 list_item 节点
            ctx: 解析器上下文

        返回:
            Optional[ListItem]: 列表项节点，如果构建失败则返回 None
        """
        if node.type != "list_item":
            ctx.diag.warning(
                f"Expected list_item, got {node.type}",
                code="LIST002",
                location=self.get_source_span(node)
            )
            return None

        # 获取列表项的子节点
        children = []
        for child in node.children:
            # 处理不同类型的子节点
            if child.type == "paragraph":
                # 段落
                para_nodes = ParagraphBuilder().build(child, ctx)
                children.extend(para_nodes)

            elif child.type == "heading":
                # 标题
                heading_nodes = HeadingBuilder().build(child, ctx)
                children.extend(heading_nodes)

            elif child.type in ("bullet_list", "ordered_list"):
                # 嵌套列表
                list_builder = ListBuilder(ordered=(child.type == "ordered_list"))
                list_nodes = list_builder.build(child, ctx)
                children.extend(list_nodes)

            elif child.type == "blockquote":
                # 引用块
                quote_nodes = BlockQuoteBuilder().build(child, ctx)
                children.extend(quote_nodes)

            elif child.type == "fence":
                # 代码块
                code_nodes = CodeBuilder().build(child, ctx)
                children.extend(code_nodes)

            elif child.type == "list_item":
                # 可能是嵌套列表项（某些解析器变体）
                sub_item = self._build_list_item(child, ctx)
                if sub_item:
                    children.append(sub_item)

            else:
                # 未知类型，记录警告
                ctx.diag.warning(
                    f"Unhandled node type in list item: {child.type}",
                    code="LIST003",
                    location=self.get_source_span(child)
                )
                # 尝试递归处理
                for sub_child in child.children:
                    if sub_child.type == "paragraph":
                        para_nodes = ParagraphBuilder().build(sub_child, ctx)
                        children.extend(para_nodes)

        # 获取源码位置
        span = self.get_source_span(node)

        # 如果没有子节点，创建一个空段落
        if not children:
            ctx.diag.warning(
                "Empty list item",
                code="LIST004",
                location=span
            )
            # 创建空段落
            empty_para = Paragraph(content=[], span=span)
            children.append(empty_para)

        # 递增解析计数
        ctx.increment_blocks()

        # 创建列表项
        return ListItem(
            children=children,
            span=span,
        )


# ============================================================
# 辅助函数
# ============================================================

def create_list_block(
    ordered: bool,
    items: List[ListItem],
    span: Optional[SourceSpan] = None
) -> ListBlock:
    """
    创建列表节点的便捷函数。

    参数:
        ordered: 是否为有序列表
        items: 列表项列表
        span: 源码位置

    返回:
        ListBlock: 列表节点

    示例:
        >>> item1 = ListItem(children=[Paragraph(content=[Text("Item 1")])])
        >>> item2 = ListItem(children=[Paragraph(content=[Text("Item 2")])])
        >>> list_block = create_list_block(False, [item1, item2])
    """
    return ListBlock(ordered=ordered, items=items, span=span)


def create_list_item(
    children: List[Node],
    span: Optional[SourceSpan] = None
) -> ListItem:
    """
    创建列表项的便捷函数。

    参数:
        children: 子节点列表
        span: 源码位置

    返回:
        ListItem: 列表项节点
    """
    return ListItem(children=children, span=span)


def is_list_node(node: SyntaxTreeNode) -> bool:
    """
    检查是否为列表节点。

    参数:
        node: SyntaxTreeNode

    返回:
        bool: 是否为列表节点
    """
    return node.type in ("bullet_list", "ordered_list")


def is_list_item_node(node: SyntaxTreeNode) -> bool:
    """
    检查是否为列表项节点。

    参数:
        node: SyntaxTreeNode

    返回:
        bool: 是否为列表项节点
    """
    return node.type == "list_item"


def get_list_depth(node: SyntaxTreeNode, current_depth: int = 0) -> int:
    """
    获取列表的嵌套深度。

    参数:
        node: SyntaxTreeNode
        current_depth: 当前深度

    返回:
        int: 最大嵌套深度
    """
    if not is_list_node(node):
        return current_depth

    max_depth = current_depth
    for child in node.children:
        if is_list_node(child):
            depth = get_list_depth(child, current_depth + 1)
            max_depth = max(max_depth, depth)

    return max_depth


def count_list_items(node: SyntaxTreeNode) -> int:
    """
    计算列表项数量。

    参数:
        node: SyntaxTreeNode

    返回:
        int: 列表项数量
    """
    if not is_list_node(node):
        return 0

    count = 0
    for child in node.children:
        if child.type == "list_item":
            count += 1
        elif is_list_node(child):
            count += count_list_items(child)

    return count


def is_ordered_list(node: SyntaxTreeNode) -> bool:
    """
    判断是否为有序列表。

    参数:
        node: SyntaxTreeNode

    返回:
        bool: 是否为有序列表
    """
    return node.type == "ordered_list"


def is_unordered_list(node: SyntaxTreeNode) -> bool:
    """
    判断是否为无序列表。

    参数:
        node: SyntaxTreeNode

    返回:
        bool: 是否为无序列表
    """
    return node.type == "bullet_list"