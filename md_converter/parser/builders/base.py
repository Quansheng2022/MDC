"""
Builder Base - Builder 模式基类定义

提供 BlockBuilder 的抽象基类，
定义 Builder 的统一接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from markdown_it.tree import SyntaxTreeNode

from ...ast.nodes import Node, SourceSpan
from ..parser_context import ParserContext


class BlockBuilder(ABC):
    """
    块级节点 Builder 基类。

    用于将 markdown-it-py 的 SyntaxTreeNode 转换为 AST 块节点。
    所有块节点 Builder 都应继承此类。

    示例:
        >>> class HeadingBuilder(BlockBuilder):
        ...     def build(self, node: SyntaxTreeNode, ctx: ParserContext) -> List[Node]:
        ...         level = int(node.tag[1])
        ...         content = build_inline_children(node, ctx)
        ...         return [Heading(level=level, content=content)]
    """

    # 支持的 SyntaxTreeNode 类型（用于注册和验证）
    supported_types: List[str] = []

    @abstractmethod
    def build(self, node: SyntaxTreeNode, ctx: ParserContext) -> List[Node]:
        """
        构建 AST 节点。

        参数:
            node: markdown-it-py 的 SyntaxTreeNode
            ctx: 解析器上下文

        返回:
            List[Node]: 构建的 AST 节点列表

        异常:
            可以抛出任何异常，会在 Parser 中被捕获并记录到诊断中
        """
        pass

    def can_build(self, node: SyntaxTreeNode) -> bool:
        """
        检查是否可以构建此节点。

        默认检查节点类型是否在 supported_types 中。
        子类可以重写此方法以实现更复杂的逻辑。

        参数:
            node: 要检查的节点

        返回:
            bool: 是否可以构建
        """
        if not self.supported_types:
            return True
        return node.type in self.supported_types

    def get_source_span(self, node: SyntaxTreeNode) -> Optional[SourceSpan]:
        """
        从 SyntaxTreeNode 提取源码位置信息。

        参数:
            node: SyntaxTreeNode

        返回:
            Optional[SourceSpan]: 源码位置，如果不可用则返回 None
        """
        if node.map:
            return SourceSpan(
                start_line=node.map[0],
                start_col=0,
                end_line=node.map[1] - 1,
                end_col=0,
            )
        return None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(supported_types={self.supported_types})"


# ============================================================
# 工具函数
# ============================================================

def extract_text_content(node: SyntaxTreeNode) -> str:
    """
    从 SyntaxTreeNode 提取纯文本内容。

    递归提取所有文本节点的内容。

    参数:
        node: SyntaxTreeNode

    返回:
        str: 提取的纯文本内容
    """
    if node.type == "text":
        return node.content or ""
    result = []
    for child in node.children:
        result.append(extract_text_content(child))
    return "".join(result)


def get_node_attributes(node: SyntaxTreeNode) -> Dict[str, Any]:
    """
    获取 SyntaxTreeNode 的属性。

    参数:
        node: SyntaxTreeNode

    返回:
        Dict[str, Any]: 属性字典
    """
    attrs = {}
    if hasattr(node, "attrs") and node.attrs:
        attrs.update(node.attrs)
    if hasattr(node, "tag") and node.tag:
        attrs["tag"] = node.tag
    if hasattr(node, "info") and node.info:
        attrs["info"] = node.info
    return attrs


def is_leaf_node(node: SyntaxTreeNode) -> bool:
    """
    检查是否为叶子节点（没有子节点）。

    参数:
        node: SyntaxTreeNode

    返回:
        bool: 是否为叶子节点
    """
    return not node.children


def get_first_child(node: SyntaxTreeNode, child_type: str) -> Optional[SyntaxTreeNode]:
    """
    获取第一个指定类型的子节点。

    参数:
        node: SyntaxTreeNode
        child_type: 子节点类型

    返回:
        Optional[SyntaxTreeNode]: 找到的子节点，否则返回 None
    """
    for child in node.children:
        if child.type == child_type:
            return child
    return None


def get_children_by_type(
    node: SyntaxTreeNode,
    child_type: str
) -> List[SyntaxTreeNode]:
    """
    获取所有指定类型的子节点。

    参数:
        node: SyntaxTreeNode
        child_type: 子节点类型

    返回:
        List[SyntaxTreeNode]: 匹配的子节点列表
    """
    return [child for child in node.children if child.type == child_type]


def get_all_text_nodes(node: SyntaxTreeNode) -> List[SyntaxTreeNode]:
    """
    获取所有文本节点（深度优先）。

    参数:
        node: SyntaxTreeNode

    返回:
        List[SyntaxTreeNode]: 文本节点列表
    """
    result = []
    if node.type == "text":
        result.append(node)
    for child in node.children:
        result.extend(get_all_text_nodes(child))
    return result