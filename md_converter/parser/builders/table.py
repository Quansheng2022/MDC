"""
Table Builder - 表格节点构建器

将 markdown-it-py 的 table 节点转换为 AST Table 节点。
支持表头、数据行、单元格对齐等。
"""

from typing import Any, Dict, List, Optional

from markdown_it.tree import SyntaxTreeNode

from ...ast.nodes import Node, SourceSpan, Table, TableCell, TableRow
from ..parser_context import ParserContext
from .base import BlockBuilder
from .inline import build_inline_children

# markdown-it-py 4.x 的表格节点类型名称
TR_TYPES = {"tr", "table_row"}          # 兼容新旧
TD_TYPES = {"td", "table_cell"}         # 兼容新旧
TH_TYPES = {"th"}                       # 表头单元格


class TableBuilder(BlockBuilder):
    """
    表格节点构建器。

    将 markdown-it-py 的 table 节点转换为 Table AST 节点。
    支持:
        - 表头（thead）
        - 表体（tbody）
        - 单元格对齐（left, center, right）
        - 多行表格

    兼容 markdown-it-py 4.x 的 AST 结构:
        table
          thead
            tr
              th
          tbody
            tr
              td
    """

    def build(self, node: SyntaxTreeNode, ctx: ParserContext) -> List[Table]:
        """
        构建表格节点。

        参数:
            node: markdown-it-py 的 SyntaxTreeNode (type='table')
            ctx: 解析器上下文

        返回:
            List[Table]: 表格节点列表（通常只有一个）
        """
        if node.type != "table":
            ctx.diag.warning(
                f"TableBuilder received non-table node: {node.type}",
                code="BUILD001",
                location=self.get_source_span(node)
            )
            return []

        # 提取所有行（兼容两种结构）
        rows = self._extract_rows(node, ctx)

        # 获取源码位置
        span = self.get_source_span(node)

        # 递增解析计数
        ctx.increment_blocks()

        # 创建表格节点
        table = Table(rows=rows, span=span)

        return [table]

    def _extract_rows(self, node: SyntaxTreeNode, ctx: ParserContext) -> List[TableRow]:
        """
        从表格节点提取所有行（兼容有无 thead/tbody 的结构）。

        参数:
            node: 表格节点
            ctx: 解析器上下文

        返回:
            List[TableRow]: 表格行节点列表
        """
        rows = []

        # 检查是否有 thead/tbody
        has_thead = any(child.type == "thead" for child in node.children)
        has_tbody = any(child.type == "tbody" for child in node.children)

        if has_thead or has_tbody:
            # 标准结构：处理 thead 和 tbody
            for child in node.children:
                if child.type == "thead":
                    rows.extend(self._build_rows_from_section(child, ctx, is_header=True))
                elif child.type == "tbody":
                    rows.extend(self._build_rows_from_section(child, ctx, is_header=False))
                else:
                    ctx.diag.warning(
                        f"Unexpected table child: {child.type}",
                        code="TABLE001",
                        location=self.get_source_span(child)
                    )
        else:
            # 简化结构：所有子节点都应是 tr
            for child in node.children:
                if child.type in TR_TYPES:
                    # 默认将第一行视为表头（更符合 Markdown 表格习惯）
                    is_header = (len(rows) == 0)  # 第一行为表头
                    row = self._build_table_row(child, ctx, is_header=is_header)
                    if row:
                        rows.append(row)
                else:
                    ctx.diag.warning(
                        f"Unexpected node in table: {child.type}",
                        code="TABLE006",
                        location=self.get_source_span(child)
                    )

        return rows

    def _build_rows_from_section(
        self,
        node: SyntaxTreeNode,
        ctx: ParserContext,
        is_header: bool = False
    ) -> List[TableRow]:
        """
        从表格区块（thead/tbody）构建行。

        参数:
            node: thead 或 tbody 节点
            ctx: 解析器上下文
            is_header: 是否为表头行

        返回:
            List[TableRow]: 表格行节点列表
        """
        rows = []

        for child in node.children:
            if child.type in TR_TYPES:
                row = self._build_table_row(child, ctx, is_header)
                if row:
                    rows.append(row)
            else:
                ctx.diag.warning(
                    f"Unexpected node in table section: {child.type}",
                    code="TABLE002",
                    location=self.get_source_span(child)
                )

        return rows

    def _build_table_row(
        self,
        node: SyntaxTreeNode,
        ctx: ParserContext,
        is_header: bool = False
    ) -> Optional[TableRow]:
        """
        构建单个表格行。

        参数:
            node: tr 节点
            ctx: 解析器上下文
            is_header: 是否为表头行

        返回:
            Optional[TableRow]: 表格行节点，如果构建失败则返回 None
        """
        if node.type not in TR_TYPES:
            ctx.diag.warning(
                f"Expected tr, got {node.type}",
                code="TABLE003",
                location=self.get_source_span(node)
            )
            return None

        cells = []
        for child in node.children:
            # 兼容 th 和 td
            if child.type in TH_TYPES or child.type in TD_TYPES:
                # th 一定是表头单元格，td 可能是表头或数据（取决于 is_header）
                cell_is_header = is_header or child.type in TH_TYPES
                cell = self._build_table_cell(child, ctx, is_header=cell_is_header)
                if cell:
                    cells.append(cell)
            else:
                ctx.diag.warning(
                    f"Unexpected node in table row: {child.type}",
                    code="TABLE004",
                    location=self.get_source_span(child)
                )

        # 获取源码位置
        span = self.get_source_span(node)

        # 递增解析计数
        ctx.increment_blocks()

        return TableRow(cells=cells, span=span)

    def _build_table_cell(
        self,
        node: SyntaxTreeNode,
        ctx: ParserContext,
        is_header: bool = False
    ) -> Optional[TableCell]:
        """
        构建单个表格单元格。

        参数:
            node: th 或 td 节点
            ctx: 解析器上下文
            is_header: 是否为表头单元格

        返回:
            Optional[TableCell]: 表格单元格节点，如果构建失败则返回 None
        """
        if node.type not in TH_TYPES and node.type not in TD_TYPES:
            ctx.diag.warning(
                f"Expected th or td, got {node.type}",
                code="TABLE005",
                location=self.get_source_span(node)
            )
            return None

        # 提取单元格内容（行内节点）
        content = []
        for child in node.children:
            if child.type == "inline":
                content = build_inline_children(child, ctx)
                break

        # 如果没有找到 inline 子节点，尝试递归处理所有子节点
        if not content:
            for child in node.children:
                content.extend(build_inline_children(child, ctx))

        # 提取单元格属性（对齐方式、列合并、行合并等）
        attrs = self._extract_cell_attributes(node, ctx)

        # 获取源码位置
        span = self.get_source_span(node)

        # 递增解析计数
        ctx.increment_inlines()

        # 创建表格单元格
        return TableCell(
            content=content,
            colspan=attrs.get("colspan", 1),
            rowspan=attrs.get("rowspan", 1),
            align=attrs.get("align"),
            span=span,
        )

    def _extract_cell_attributes(
        self,
        node: SyntaxTreeNode,
        ctx: ParserContext
    ) -> Dict[str, Any]:
        """
        提取单元格属性。

        支持:
            - align: 对齐方式 (left, center, right)
            - colspan: 列合并
            - rowspan: 行合并

        参数:
            node: th 或 td 节点
            ctx: 解析器上下文

        返回:
            Dict[str, Any]: 属性字典
        """
        attrs = {}

        # 从 node.attrs 提取
        if hasattr(node, "attrs") and node.attrs:
            # 对齐方式
            if "align" in node.attrs:
                align = node.attrs["align"]
                if align in ["left", "center", "right"]:
                    attrs["align"] = align

            # 列合并
            if "colspan" in node.attrs:
                try:
                    attrs["colspan"] = int(node.attrs["colspan"])
                except (ValueError, TypeError):
                    pass

            # 行合并
            if "rowspan" in node.attrs:
                try:
                    attrs["rowspan"] = int(node.attrs["rowspan"])
                except (ValueError, TypeError):
                    pass

        return attrs


# ============================================================
# 辅助函数
# ============================================================

def create_table(
    rows: List[TableRow],
    span: Optional[SourceSpan] = None
) -> Table:
    """
    创建表格节点的便捷函数。

    参数:
        rows: 表格行列表
        span: 源码位置

    返回:
        Table: 表格节点

    示例:
        >>> header_row = TableRow(cells=[TableCell(content=[Text("Name")])])
        >>> data_row = TableRow(cells=[TableCell(content=[Text("Alice")])])
        >>> table = create_table([header_row, data_row])
    """
    return Table(rows=rows, span=span)


def create_table_row(
    cells: List[TableCell],
    span: Optional[SourceSpan] = None
) -> TableRow:
    """
    创建表格行的便捷函数。

    参数:
        cells: 表格单元格列表
        span: 源码位置

    返回:
        TableRow: 表格行节点
    """
    return TableRow(cells=cells, span=span)


def create_table_cell(
    content: List[Node],
    align: Optional[str] = None,
    colspan: int = 1,
    rowspan: int = 1,
    span: Optional[SourceSpan] = None
) -> TableCell:
    """
    创建表格单元格的便捷函数。

    参数:
        content: 行内节点列表
        align: 对齐方式 (left, center, right)
        colspan: 列合并数
        rowspan: 行合并数
        span: 源码位置

    返回:
        TableCell: 表格单元格节点

    示例:
        >>> cell = create_table_cell([Text("Hello")], align="center")
    """
    return TableCell(
        content=content,
        align=align,
        colspan=colspan,
        rowspan=rowspan,
        span=span,
    )


def is_table_node(node: SyntaxTreeNode) -> bool:
    """
    检查是否为表格节点。

    参数:
        node: SyntaxTreeNode

    返回:
        bool: 是否为表格节点
    """
    return node.type == "table"


def is_table_row_node(node: SyntaxTreeNode) -> bool:
    """
    检查是否为表格行节点。

    参数:
        node: SyntaxTreeNode

    返回:
        bool: 是否为表格行节点
    """
    return node.type in TR_TYPES


def is_table_cell_node(node: SyntaxTreeNode) -> bool:
    """
    检查是否为表格单元格节点。

    参数:
        node: SyntaxTreeNode

    返回:
        bool: 是否为表格单元格节点
    """
    return node.type in TH_TYPES or node.type in TD_TYPES


def get_table_dimensions(table: Table) -> tuple:
    """
    获取表格维度。

    参数:
        table: Table 节点

    返回:
        tuple: (行数, 列数)
    """
    if not table.rows:
        return (0, 0)

    rows = len(table.rows)
    cols = 0
    for row in table.rows:
        cols = max(cols, len(row.cells))

    return (rows, cols)


def get_cell_count(table: Table) -> int:
    """
    获取表格单元格总数。

    参数:
        table: Table 节点

    返回:
        int: 单元格总数
    """
    count = 0
    for row in table.rows:
        count += len(row.cells)
    return count


def is_empty_table(table: Table) -> bool:
    """
    检查是否为空表格。

    参数:
        table: Table 节点

    返回:
        bool: 是否为空表格
    """
    return not table.rows or all(not row.cells for row in table.rows)


def get_first_row_cells(table: Table) -> List[TableCell]:
    """
    获取表格第一行的单元格（通常为表头）。

    参数:
        table: Table 节点

    返回:
        List[TableCell]: 第一行的单元格列表
    """
    if not table.rows:
        return []
    return table.rows[0].cells