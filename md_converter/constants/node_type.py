"""
Node Type Enum - AST 节点类型枚举

使用枚举类型替代字符串，提供类型安全的节点类型标识。
所有 AST 节点必须使用这些枚举值。
"""

from enum import Enum, auto
from typing import Dict, Optional, Set


class NodeType(Enum):
    """
    AST 节点类型枚举。
    """

    # 根节点
    DOCUMENT = auto()

    # 块节点
    HEADING = auto()
    PARAGRAPH = auto()
    LIST_BLOCK = auto()
    LIST_ITEM = auto()
    TABLE = auto()
    TABLE_ROW = auto()
    TABLE_CELL = auto()
    CODE_BLOCK = auto()
    BLOCK_QUOTE = auto()
    DIAGRAM = auto()
    HORIZONTAL_RULE = auto()

    # 行内节点
    TEXT = auto()
    STRONG = auto()
    EMPHASIS = auto()
    INLINE_CODE = auto()
    LINK = auto()
    IMAGE = auto()
    SOFT_BREAK = auto()
    HARD_BREAK = auto()

    @property
    def is_block(self) -> bool:
        return self in BLOCK_NODE_TYPES

    @property
    def is_inline(self) -> bool:
        return self in INLINE_NODE_TYPES

    @property
    def is_container(self) -> bool:
        return self in CONTAINER_NODE_TYPES

    @property
    def is_leaf(self) -> bool:
        return self in LEAF_NODE_TYPES

    def __str__(self) -> str:
        return self.name


# ---------- 节点分类集合 ----------

BLOCK_NODE_TYPES: Set[NodeType] = {
    NodeType.DOCUMENT,
    NodeType.HEADING,
    NodeType.PARAGRAPH,
    NodeType.LIST_BLOCK,
    NodeType.LIST_ITEM,
    NodeType.TABLE,
    NodeType.TABLE_ROW,
    NodeType.TABLE_CELL,
    NodeType.CODE_BLOCK,
    NodeType.BLOCK_QUOTE,
    NodeType.DIAGRAM,
    NodeType.HORIZONTAL_RULE,
}

INLINE_NODE_TYPES: Set[NodeType] = {
    NodeType.TEXT,
    NodeType.STRONG,
    NodeType.EMPHASIS,
    NodeType.INLINE_CODE,
    NodeType.LINK,
    NodeType.IMAGE,
    NodeType.SOFT_BREAK,
    NodeType.HARD_BREAK,
}

CONTAINER_NODE_TYPES: Set[NodeType] = {
    NodeType.DOCUMENT,
    NodeType.HEADING,
    NodeType.PARAGRAPH,
    NodeType.LIST_BLOCK,
    NodeType.LIST_ITEM,
    NodeType.TABLE,
    NodeType.TABLE_ROW,
    NodeType.TABLE_CELL,
    NodeType.BLOCK_QUOTE,
    NodeType.STRONG,
    NodeType.EMPHASIS,
    NodeType.LINK,
}

LEAF_NODE_TYPES: Set[NodeType] = {
    NodeType.TEXT,
    NodeType.INLINE_CODE,
    NodeType.IMAGE,
    NodeType.CODE_BLOCK,
    NodeType.DIAGRAM,
    NodeType.HORIZONTAL_RULE,
    NodeType.SOFT_BREAK,
    NodeType.HARD_BREAK,
}

# ---------- 节点名称映射 ----------

NODE_TYPE_NAMES: Dict[NodeType, str] = {
    NodeType.DOCUMENT: "Document",
    NodeType.HEADING: "Heading",
    NodeType.PARAGRAPH: "Paragraph",
    NodeType.LIST_BLOCK: "ListBlock",
    NodeType.LIST_ITEM: "ListItem",
    NodeType.TABLE: "Table",
    NodeType.TABLE_ROW: "TableRow",
    NodeType.TABLE_CELL: "TableCell",
    NodeType.CODE_BLOCK: "CodeBlock",
    NodeType.BLOCK_QUOTE: "BlockQuote",
    NodeType.DIAGRAM: "Diagram",
    NodeType.HORIZONTAL_RULE: "HorizontalRule",
    NodeType.TEXT: "Text",
    NodeType.STRONG: "Strong",
    NodeType.EMPHASIS: "Emphasis",
    NodeType.INLINE_CODE: "InlineCode",
    NodeType.LINK: "Link",
    NodeType.IMAGE: "Image",
    NodeType.SOFT_BREAK: "SoftBreak",
    NodeType.HARD_BREAK: "HardBreak",
}

# ---------- markdown-it-py 类型映射 ----------

SYNTAX_TO_NODE_TYPE: Dict[str, NodeType] = {
    # 块节点
    "heading": NodeType.HEADING,
    "paragraph": NodeType.PARAGRAPH,
    "bullet_list": NodeType.LIST_BLOCK,
    "ordered_list": NodeType.LIST_BLOCK,
    "list_item": NodeType.LIST_ITEM,
    "table": NodeType.TABLE,
    "table_row": NodeType.TABLE_ROW,
    "table_cell": NodeType.TABLE_CELL,
    "fence": NodeType.CODE_BLOCK,
    "code_block": NodeType.CODE_BLOCK,  # 缩进式代码块（4 空格缩进）
    "blockquote": NodeType.BLOCK_QUOTE,
    "thematic_break": NodeType.HORIZONTAL_RULE,
    "hr": NodeType.HORIZONTAL_RULE,  # ✅ 添加兼容性映射
    # 行内节点
    "text": NodeType.TEXT,
    "strong": NodeType.STRONG,
    "em": NodeType.EMPHASIS,
    "code_inline": NodeType.INLINE_CODE,
    "link": NodeType.LINK,
    "image": NodeType.IMAGE,
    "softbreak": NodeType.SOFT_BREAK,
    "hardbreak": NodeType.HARD_BREAK,
}

NODE_TO_SYNTAX_TYPE: Dict[NodeType, str] = {v: k for k, v in SYNTAX_TO_NODE_TYPE.items()}


# ---------- 工具函数 ----------


def get_node_type_name(node_type: NodeType) -> str:
    return NODE_TYPE_NAMES.get(node_type, node_type.name)


def is_block_node(node_type: NodeType) -> bool:
    return node_type.is_block


def is_inline_node(node_type: NodeType) -> bool:
    return node_type.is_inline


def is_container_node(node_type: NodeType) -> bool:
    return node_type.is_container


def is_leaf_node(node_type: NodeType) -> bool:
    return node_type.is_leaf


def syntax_type_to_node_type(syntax_type: str) -> Optional[NodeType]:
    return SYNTAX_TO_NODE_TYPE.get(syntax_type)


def node_type_to_syntax_type(node_type: NodeType) -> Optional[str]:
    return NODE_TO_SYNTAX_TYPE.get(node_type)


def get_supported_syntax_types() -> Set[str]:
    return set(SYNTAX_TO_NODE_TYPE.keys())


# ---------- 快捷判断 ----------


def is_heading(node_type: NodeType) -> bool:
    return node_type == NodeType.HEADING


def is_list_node(node_type: NodeType) -> bool:
    return node_type in (NodeType.LIST_BLOCK, NodeType.LIST_ITEM)


def is_table_node(node_type: NodeType) -> bool:
    return node_type in (NodeType.TABLE, NodeType.TABLE_ROW, NodeType.TABLE_CELL)


def is_inline_element(node_type: NodeType) -> bool:
    return node_type.is_inline


def is_text_node(node_type: NodeType) -> bool:
    return node_type == NodeType.TEXT


def is_code_node(node_type: NodeType) -> bool:
    return node_type in (NodeType.CODE_BLOCK, NodeType.INLINE_CODE)


def is_link_node(node_type: NodeType) -> bool:
    return node_type == NodeType.LINK


def is_image_node(node_type: NodeType) -> bool:
    return node_type == NodeType.IMAGE
