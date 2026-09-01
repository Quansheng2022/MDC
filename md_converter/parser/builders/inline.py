"""
Inline Builder - 行内节点构建器

使用迭代式算法从 markdown-it-py 的 SyntaxTreeNode 构建行内 AST 节点。
支持嵌套样式（粗体、斜体、链接等），避免递归深度限制。
"""

from typing import List, Optional, Tuple

from markdown_it.tree import SyntaxTreeNode

from ...ast.nodes import (
    Emphasis,
    HardBreak,
    Image,
    InlineCode,
    Link,
    Node,
    SoftBreak,
    SourceSpan,
    Strong,
    Text,
)
from ..parser_context import ParserContext

# ============================================================
# 行内节点构建器类
# ============================================================

class InlineTextBuilder:
    """文本节点构建器"""
    def build(self, node: SyntaxTreeNode, ctx: ParserContext) -> List[Text]:
        return [Text(content=node.content or "")]


class InlineStrongBuilder:
    """粗体节点构建器 - 修复递归"""
    def build(self, node: SyntaxTreeNode, ctx: ParserContext) -> List[Strong]:
        content = []
        for child in node.children:
            content.extend(build_inline_children(child, ctx))
        return [Strong(content=content)]


class InlineEmphasisBuilder:
    """斜体节点构建器 - 修复递归"""
    def build(self, node: SyntaxTreeNode, ctx: ParserContext) -> List[Emphasis]:
        content = []
        for child in node.children:
            content.extend(build_inline_children(child, ctx))
        return [Emphasis(content=content)]


class InlineCodeBuilder:
    """行内代码节点构建器"""
    def build(self, node: SyntaxTreeNode, ctx: ParserContext) -> List[InlineCode]:
        return [InlineCode(text=node.content or "")]


class InlineLinkBuilder:
    """链接节点构建器 - 修复递归"""
    def build(self, node: SyntaxTreeNode, ctx: ParserContext) -> List[Link]:
        href = node.attrs.get("href", "") if hasattr(node, "attrs") else ""
        content = []
        for child in node.children:
            content.extend(build_inline_children(child, ctx))
        return [Link(href=href, content=content)]


class InlineImageBuilder:
    """图片节点构建器"""
    def build(self, node: SyntaxTreeNode, ctx: ParserContext) -> List[Image]:
        attrs = node.attrs if hasattr(node, "attrs") else {}
        src = attrs.get("src", "")
        alt = attrs.get("alt", "")
        return [Image(alt=alt, src=src)]


class InlineSoftBreakBuilder:
    """软换行节点构建器"""
    def build(self, node: SyntaxTreeNode, ctx: ParserContext) -> List[SoftBreak]:
        return [SoftBreak()]


class InlineHardBreakBuilder:
    """硬换行节点构建器"""
    def build(self, node: SyntaxTreeNode, ctx: ParserContext) -> List[HardBreak]:
        return [HardBreak()]


# ============================================================
# 构建器工厂
# ============================================================

def get_inline_builder(node_type: str):
    """
    根据节点类型获取对应的行内构建器。
    """
    builders = {
        "text": InlineTextBuilder(),
        "strong": InlineStrongBuilder(),
        "em": InlineEmphasisBuilder(),
        "code_inline": InlineCodeBuilder(),
        "link": InlineLinkBuilder(),
        "image": InlineImageBuilder(),
        "softbreak": InlineSoftBreakBuilder(),
        "hardbreak": InlineHardBreakBuilder(),
    }
    return builders.get(node_type)


# ============================================================
# 核心构建函数（迭代式）
# ============================================================

def build_inline_children(
    node: SyntaxTreeNode,
    ctx: Optional[ParserContext] = None
) -> List[Node]:
    """
    从 SyntaxTreeNode 构建行内节点列表（迭代式）。

    使用栈遍历避免递归深度限制，支持深层嵌套。

    重要：此函数假设传入的是 'inline' 类型的节点或其子节点。
    如果传入其他类型，会记录警告并尝试处理子节点。

    参数:
        node: markdown-it-py 的 SyntaxTreeNode (通常是 'inline' 类型或其子节点)
        ctx: 解析器上下文（可选，用于诊断）

    返回:
        List[Node]: 行内节点列表
    """
    if ctx is None:
        from ...diagnostics.collector import DiagnosticCollector
        from ..parser_context import ParserContext
        ctx = ParserContext(diag=DiagnosticCollector())

    # 如果节点是 'inline' 容器，递归处理其子节点
    if node.type == "inline":
        result = []
        for child in node.children:
            result.extend(build_inline_children(child, ctx))
        return result

    result: List[Node] = []
    # 栈元素: (node, parent_list, processed)
    stack: List[Tuple[SyntaxTreeNode, List[Node], bool]] = [
        (node, result, False)
    ]

    while stack:
        current_node, parent_list, processed = stack.pop()

        if processed:
            continue

        builder = get_inline_builder(current_node.type)

        if builder:
            try:
                built_nodes = builder.build(current_node, ctx)
                parent_list.extend(built_nodes)
            except Exception as e:
                if ctx:
                    ctx.diag.warning(
                        f"Failed to build inline node '{current_node.type}': {e}",
                        code="INLINE001",
                        location=_get_span(current_node)
                    )
                # 降级处理：提取文本内容
                text_content = _extract_text_content(current_node)
                if text_content:
                    parent_list.append(Text(content=text_content))
        else:
            # 未知节点类型，尝试递归处理子节点
            if ctx:
                ctx.diag.warning(
                    f"Unknown inline node type: {current_node.type}",
                    code="INLINE002",
                    location=_get_span(current_node)
                )

            stack.append((current_node, parent_list, True))

            for child in reversed(current_node.children):
                stack.append((child, parent_list, False))

    return result


def build_inline_from_tokens(
    tokens: List,
    ctx: Optional[ParserContext] = None
) -> List[Node]:
    """
    从 Token 列表构建行内节点。

    参数:
        tokens: markdown-it-py Token 列表
        ctx: 解析器上下文

    返回:
        List[Node]: 行内节点列表
    """
    if not tokens:
        return []

    from markdown_it.tree import SyntaxTreeNode
    root = SyntaxTreeNode(tokens)

    result = []
    for child in root.children:
        if child.type == "inline":
            result.extend(build_inline_children(child, ctx))
        else:
            if ctx:
                ctx.diag.warning(
                    f"Expected inline node, got {child.type}",
                    code="INLINE002",
                    location=_get_span(child)
                )

    return result


# ============================================================
# 辅助函数
# ============================================================

def _get_span(node: SyntaxTreeNode) -> Optional[SourceSpan]:
    if node.map:
        return SourceSpan(
            start_line=node.map[0],
            start_col=0,
            end_line=node.map[1] - 1,
            end_col=0,
        )
    return None


def _extract_text_content(node: SyntaxTreeNode) -> str:
    if node.type == "text":
        return node.content or ""

    result = []
    for child in node.children:
        result.append(_extract_text_content(child))

    return "".join(result)


# ============================================================
# 便捷函数
# ============================================================

def create_text(text: str) -> Text:
    return Text(content=text)


def create_strong(content: List[Node]) -> Strong:
    return Strong(content=content)


def create_emphasis(content: List[Node]) -> Emphasis:
    return Emphasis(content=content)


def create_inline_code(text: str) -> InlineCode:
    return InlineCode(text=text)


def create_link(href: str, content: List[Node]) -> Link:
    return Link(href=href, content=content)


def create_image(src: str, alt: str = "") -> Image:
    return Image(alt=alt, src=src)


def create_soft_break() -> SoftBreak:
    return SoftBreak()


def create_hard_break() -> HardBreak:
    return HardBreak()


# ============================================================
# 规范化工具
# ============================================================

def normalize_inline_nodes(nodes: List[Node]) -> List[Node]:
    """合并相邻的 Text 节点"""
    if not nodes:
        return []

    normalized = []
    current_text = ""

    for node in nodes:
        if isinstance(node, Text):
            current_text += node.content
        else:
            if current_text:
                normalized.append(Text(content=current_text))
                current_text = ""
            normalized.append(node)

    if current_text:
        normalized.append(Text(content=current_text))

    return normalized


def merge_text_nodes(nodes: List[Node]) -> List[Node]:
    return normalize_inline_nodes(nodes)


def strip_whitespace(nodes: List[Node]) -> List[Node]:
    if not nodes:
        return []

    result = list(nodes)

    while result and isinstance(result[0], Text) and result[0].content.isspace():
        result.pop(0)

    while result and isinstance(result[-1], Text) and result[-1].content.isspace():
        result.pop(-1)

    return result


def is_empty_inline(nodes: List[Node]) -> bool:
    if not nodes:
        return True

    for node in nodes:
        if isinstance(node, Text) and node.content.strip():
            return False
        elif not isinstance(node, Text):
            return False

    return True


def get_inline_text(nodes: List[Node]) -> str:
    return "".join(node.to_plain_text() for node in nodes)