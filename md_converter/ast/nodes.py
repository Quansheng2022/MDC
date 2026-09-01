"""
AST Nodes - 不可变抽象语法树节点定义

所有节点都是不可变的（frozen dataclass），修改操作返回新节点。
每个节点都包含类型信息和源码位置信息（SourceSpan），
便于诊断和调试。

设计原则:
    1. 基类 Node 使用 field(init=False) 声明 node_type
    2. span 使用 kw_only=True，不参与字段顺序检查
    3. 子类不重复声明 span
    4. 所有子类在 __post_init__ 中设置 node_type
    5. 完全兼容 Python 3.13+ dataclass 顺序检查
"""

from abc import ABC
from dataclasses import dataclass, field, replace
from typing import Iterator, List, Optional

from ..constants.node_type import NodeType

# ============================================================
# SourceSpan - 源码位置信息
# ============================================================

@dataclass(frozen=True)
class SourceSpan:
    """
    源码位置信息，用于诊断和错误报告。

    属性:
        start_line: 起始行号（从 0 开始）
        start_col: 起始列号（从 0 开始）
        end_line: 结束行号（从 0 开始）
        end_col: 结束列号（从 0 开始）
    """
    start_line: int
    start_col: int
    end_line: int
    end_col: int

    @classmethod
    def from_map(cls, map_data: Optional[List[int]]) -> Optional["SourceSpan"]:
        """
        从 markdown-it-py 的 map 数据创建 SourceSpan。

        markdown-it-py 的 map 格式: [start_line, end_line]
        """
        if not map_data or len(map_data) < 2:
            return None
        return cls(
            start_line=map_data[0],
            start_col=0,
            end_line=map_data[1] - 1,
            end_col=0,
        )

    def __str__(self) -> str:
        if self.start_line == self.end_line:
            return f"line {self.start_line + 1}"
        return f"lines {self.start_line + 1}-{self.end_line + 1}"


# ============================================================
# Node 基类 - iter_children 不再是抽象方法
# ============================================================

@dataclass(frozen=True)
class Node(ABC):
    """
    AST 节点基类。

    设计说明:
        - node_type: 使用 field(init=False)，不参与构造函数
        - span: 使用 kw_only=True，作为关键字参数
        - 子类必须在 __post_init__ 中设置 node_type
        - 子类不重复声明 span
        - iter_children 提供默认实现，叶子节点无需重写

    属性:
        node_type: 节点类型 (NodeType 枚举) - 自动设置
        span: 源码位置信息，可选
    """
    node_type: NodeType = field(init=False)
    span: Optional[SourceSpan] = field(default=None, kw_only=True)

    def iter_children(self) -> Iterator['Node']:
        """
        遍历所有子节点。

        默认实现返回空迭代器（适用于叶子节点）。
        容器节点应重写此方法。
        """
        yield from ()

    def replace_children(self, children: List['Node']) -> 'Node':
        """
        返回替换子节点后的新节点（不可变更新）。

        默认实现返回自身（无子节点的节点无需重写）。
        有子节点的节点应该重写此方法。

        参数:
            children: 新的子节点列表

        返回:
            Node: 替换子节点后的新节点
        """
        return self

    def to_plain_text(self) -> str:
        """
        提取节点的纯文本内容。

        返回:
            str: 纯文本内容
        """
        return ''.join(c.to_plain_text() for c in self.iter_children())

    def find_all(self, node_type: NodeType) -> List['Node']:
        """
        查找所有指定类型的子节点（深度优先）。

        参数:
            node_type: 要查找的节点类型

        返回:
            List[Node]: 匹配的节点列表
        """
        result = []
        if self.node_type == node_type:
            result.append(self)
        for child in self.iter_children():
            result.extend(child.find_all(node_type))
        return result

    def find_first(self, node_type: NodeType) -> Optional['Node']:
        """
        查找第一个指定类型的节点（深度优先）。

        参数:
            node_type: 要查找的节点类型

        返回:
            Optional[Node]: 找到的第一个节点，如果没有则返回 None
        """
        if self.node_type == node_type:
            return self
        for child in self.iter_children():
            result = child.find_first(node_type)
            if result:
                return result
        return None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(node_type={self.node_type.name if self.node_type else 'None'})"


# ============================================================
# 块节点 (Block Nodes)
# ============================================================

@dataclass(frozen=True)
class Document(Node):
    """
    文档根节点。

    属性:
        children: 子节点列表（块节点）
    """
    children: List[Node] = field(default_factory=list)

    def __post_init__(self):
        object.__setattr__(self, 'node_type', NodeType.DOCUMENT)

    def iter_children(self) -> Iterator[Node]:
        yield from self.children

    def replace_children(self, children: List[Node]) -> 'Document':
        return replace(self, children=children)


@dataclass(frozen=True)
class Heading(Node):
    """
    标题节点。

    属性:
        level: 标题级别 (1-6)
        content: 标题内容（行内节点列表）
    """
    level: int
    content: List[Node]

    def __post_init__(self):
        object.__setattr__(self, 'node_type', NodeType.HEADING)

    def iter_children(self) -> Iterator[Node]:
        yield from self.content

    def replace_children(self, children: List[Node]) -> 'Heading':
        return replace(self, content=children)

    def to_plain_text(self) -> str:
        return ''.join(c.to_plain_text() for c in self.content)


@dataclass(frozen=True)
class Paragraph(Node):
    """
    段落节点。

    属性:
        content: 段落内容（行内节点列表）
    """
    content: List[Node]

    def __post_init__(self):
        object.__setattr__(self, 'node_type', NodeType.PARAGRAPH)

    def iter_children(self) -> Iterator[Node]:
        yield from self.content

    def replace_children(self, children: List[Node]) -> 'Paragraph':
        return replace(self, content=children)

    def to_plain_text(self) -> str:
        return ''.join(c.to_plain_text() for c in self.content)


@dataclass(frozen=True)
class BlockQuote(Node):
    """
    引用块节点。

    属性:
        children: 子节点列表（块节点）
    """
    children: List[Node]

    def __post_init__(self):
        object.__setattr__(self, 'node_type', NodeType.BLOCK_QUOTE)

    def iter_children(self) -> Iterator[Node]:
        yield from self.children

    def replace_children(self, children: List[Node]) -> 'BlockQuote':
        return replace(self, children=children)


@dataclass(frozen=True)
class ListItem(Node):
    """
    列表项节点。

    属性:
        children: 子节点列表（块节点，如 Paragraph, ListBlock 等）
    """
    children: List[Node]

    def __post_init__(self):
        object.__setattr__(self, 'node_type', NodeType.LIST_ITEM)

    def iter_children(self) -> Iterator[Node]:
        yield from self.children

    def replace_children(self, children: List[Node]) -> 'ListItem':
        return replace(self, children=children)


@dataclass(frozen=True)
class ListBlock(Node):
    """
    列表块节点。

    属性:
        ordered: 是否为有序列表
        items: 列表项列表
    """
    ordered: bool
    items: List[ListItem]

    def __post_init__(self):
        object.__setattr__(self, 'node_type', NodeType.LIST_BLOCK)

    def iter_children(self) -> Iterator[Node]:
        yield from self.items

    def replace_children(self, children: List[Node]) -> 'ListBlock':
        # 确保 children 都是 ListItem
        items = [c for c in children if isinstance(c, ListItem)]
        return replace(self, items=items)


@dataclass(frozen=True)
class Table(Node):
    """
    表格节点。

    属性:
        rows: 表格行列表
    """
    rows: List['TableRow']

    def __post_init__(self):
        object.__setattr__(self, 'node_type', NodeType.TABLE)

    def iter_children(self) -> Iterator[Node]:
        yield from self.rows

    def replace_children(self, children: List[Node]) -> 'Table':
        rows = [c for c in children if isinstance(c, TableRow)]
        return replace(self, rows=rows)


@dataclass(frozen=True)
class TableRow(Node):
    """
    表格行节点。

    属性:
        cells: 表格单元格列表
    """
    cells: List['TableCell']

    def __post_init__(self):
        object.__setattr__(self, 'node_type', NodeType.TABLE_ROW)

    def iter_children(self) -> Iterator[Node]:
        yield from self.cells

    def replace_children(self, children: List[Node]) -> 'TableRow':
        cells = [c for c in children if isinstance(c, TableCell)]
        return replace(self, cells=cells)


@dataclass(frozen=True)
class TableCell(Node):
    """
    表格单元格节点。

    属性:
        content: 单元格内容（行内节点列表）
        colspan: 列合并数
        rowspan: 行合并数
        align: 对齐方式 ('left', 'center', 'right', None)
    """
    content: List[Node]
    colspan: int = 1
    rowspan: int = 1
    align: Optional[str] = None

    def __post_init__(self):
        object.__setattr__(self, 'node_type', NodeType.TABLE_CELL)

    def iter_children(self) -> Iterator[Node]:
        yield from self.content

    def replace_children(self, children: List[Node]) -> 'TableCell':
        return replace(self, content=children)


@dataclass(frozen=True)
class CodeBlock(Node):
    """
    代码块节点。

    属性:
        language: 编程语言（可为空）
        text: 代码内容
    """
    language: str
    text: str

    def __post_init__(self):
        object.__setattr__(self, 'node_type', NodeType.CODE_BLOCK)

    def to_plain_text(self) -> str:
        return self.text


@dataclass(frozen=True)
class Diagram(Node):
    """
    图表节点（ASCII 结构图 或 Mermaid 图表）。

    属性:
        diagram_type: 图表类型 (ascii, mermaid, plantuml, graphviz, etc.)
        content: 图表原始内容（代码）
    """
    diagram_type: str
    content: str

    def __post_init__(self):
        object.__setattr__(self, 'node_type', NodeType.DIAGRAM)

    def to_plain_text(self) -> str:
        return self.content

    def iter_children(self) -> Iterator[Node]:
        yield from ()


@dataclass(frozen=True)
class HorizontalRule(Node):
    """水平分割线节点。"""

    def __post_init__(self):
        object.__setattr__(self, 'node_type', NodeType.HORIZONTAL_RULE)


# ============================================================
# 行内节点 (Inline Nodes)
# ============================================================

@dataclass(frozen=True)
class Text(Node):
    """
    纯文本节点。

    属性:
        content: 文本内容
    """
    content: str

    def __post_init__(self):
        object.__setattr__(self, 'node_type', NodeType.TEXT)

    def to_plain_text(self) -> str:
        return self.content


@dataclass(frozen=True)
class Strong(Node):
    """
    粗体节点。

    属性:
        content: 粗体内容（行内节点列表）
    """
    content: List[Node]

    def __post_init__(self):
        object.__setattr__(self, 'node_type', NodeType.STRONG)

    def iter_children(self) -> Iterator[Node]:
        yield from self.content

    def replace_children(self, children: List[Node]) -> 'Strong':
        return replace(self, content=children)


@dataclass(frozen=True)
class Emphasis(Node):
    """
    斜体节点。

    属性:
        content: 斜体内容（行内节点列表）
    """
    content: List[Node]

    def __post_init__(self):
        object.__setattr__(self, 'node_type', NodeType.EMPHASIS)

    def iter_children(self) -> Iterator[Node]:
        yield from self.content

    def replace_children(self, children: List[Node]) -> 'Emphasis':
        return replace(self, content=children)


@dataclass(frozen=True)
class InlineCode(Node):
    """
    行内代码节点。

    属性:
        text: 代码内容
    """
    text: str

    def __post_init__(self):
        object.__setattr__(self, 'node_type', NodeType.INLINE_CODE)

    def to_plain_text(self) -> str:
        return self.text


@dataclass(frozen=True)
class Link(Node):
    """
    链接节点。

    属性:
        href: 链接 URL
        content: 链接文本内容（行内节点列表）
    """
    href: str
    content: List[Node]

    def __post_init__(self):
        object.__setattr__(self, 'node_type', NodeType.LINK)

    def iter_children(self) -> Iterator[Node]:
        yield from self.content

    def replace_children(self, children: List[Node]) -> 'Link':
        return replace(self, content=children)


@dataclass(frozen=True)
class Image(Node):
    """
    图片节点。

    属性:
        alt: 替代文本
        src: 图片源地址（文件路径或 data URI）
    """
    alt: str
    src: str

    def __post_init__(self):
        object.__setattr__(self, 'node_type', NodeType.IMAGE)

    def to_plain_text(self) -> str:
        return self.alt or 'Image'


@dataclass(frozen=True)
class SoftBreak(Node):
    """软换行节点（Markdown 中的普通换行）。"""

    def __post_init__(self):
        object.__setattr__(self, 'node_type', NodeType.SOFT_BREAK)


@dataclass(frozen=True)
class HardBreak(Node):
    """硬换行节点（Markdown 中以两个空格结尾的换行）。"""

    def __post_init__(self):
        object.__setattr__(self, 'node_type', NodeType.HARD_BREAK)


# ============================================================
# 节点工具函数
# ============================================================

def is_leaf_node(node: Node) -> bool:
    """判断节点是否为叶子节点（无子节点）"""
    try:
        next(node.iter_children())
        return False
    except StopIteration:
        return True


def get_node_depth(node: Node, max_depth: int = 100) -> int:
    """获取节点的最大深度"""
    if is_leaf_node(node):
        return 1
    max_child_depth = 0
    for child in node.iter_children():
        child_depth = get_node_depth(child, max_depth - 1)
        if child_depth > max_child_depth:
            max_child_depth = child_depth
    return 1 + max_child_depth


def count_nodes(node: Node) -> int:
    """统计节点树中的节点总数"""
    count = 1
    for child in node.iter_children():
        count += count_nodes(child)
    return count


def collect_nodes(node: Node, node_type: Optional[NodeType] = None) -> List[Node]:
    """
    收集所有指定类型的节点（深度优先）。

    参数:
        node: 根节点
        node_type: 要收集的节点类型，None 表示收集所有节点

    返回:
        List[Node]: 匹配的节点列表
    """
    result = []
    if node_type is None or node.node_type == node_type:
        result.append(node)
    for child in node.iter_children():
        result.extend(collect_nodes(child, node_type))
    return result


def collect_blocks(node: Node) -> List[Node]:
    """收集所有块节点"""
    from ..constants.node_type import BLOCK_NODE_TYPES
    return [n for n in collect_nodes(node, None) if n.node_type in BLOCK_NODE_TYPES]


def collect_inlines(node: Node) -> List[Node]:
    """收集所有行内节点"""
    from ..constants.node_type import INLINE_NODE_TYPES
    return [n for n in collect_nodes(node, None) if n.node_type in INLINE_NODE_TYPES]


def to_plain_text(node: Node) -> str:
    """提取节点的纯文本内容"""
    return node.to_plain_text()


def get_heading_text(heading: Heading) -> str:
    """获取标题的纯文本内容"""
    return heading.to_plain_text()


def get_table_dimensions(table: Table) -> tuple:
    """获取表格的维度 (行数, 列数)"""
    if not table.rows:
        return (0, 0)
    return (len(table.rows), max(len(row.cells) for row in table.rows))