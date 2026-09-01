"""
Normalize Pass - AST 标准化 Pass

合并相邻的 Text 节点，优化 AST 结构。
减少冗余节点，提高后续处理效率。
"""

from typing import Any, Dict, List, Optional

from ...ast.nodes import (
    BlockQuote,
    Document,
    Emphasis,
    Heading,
    Link,
    ListBlock,
    ListItem,
    Node,
    Paragraph,
    Strong,
    Table,
    TableCell,
    TableRow,
    Text,
)
from ...diagnostics.collector import DiagnosticCollector
from .base import PassResult, TransformPass


class NormalizePass(TransformPass):
    """
    AST 标准化 Pass。

    功能:
        1. 合并相邻的 Text 节点
        2. 移除空白的 Text 节点（可选）
        3. 规范化列表结构
        4. 规范化表格结构

    配置:
        merge_text: 是否合并相邻文本节点（默认 True）
        remove_empty_text: 是否移除空文本节点（默认 True）
        normalize_list: 是否规范化列表结构（默认 False）
        normalize_table: 是否规范化表格结构（默认 False）
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 NormalizePass。

        参数:
            config: 配置字典
                - merge_text: 是否合并相邻文本节点
                - remove_empty_text: 是否移除空文本节点
                - normalize_list: 是否规范化列表结构
                - normalize_table: 是否规范化表格结构
        """
        super().__init__(config=config or {})

        # 从 config 加载配置
        self.merge_text = self.config.get("merge_text", True)
        self.remove_empty_text = self.config.get("remove_empty_text", True)
        self.normalize_list = self.config.get("normalize_list", False)
        self.normalize_table = self.config.get("normalize_table", False)

        self._stats = {
            "text_merged": 0,
            "text_removed": 0,
            "list_normalized": 0,
            "table_normalized": 0,
        }

    def run(self, document: Node, diag: DiagnosticCollector) -> PassResult:
        """
        执行标准化 Pass。

        参数:
            document: AST 根节点
            diag: 诊断收集器

        返回:
            PassResult: 执行结果
        """
        # 重置统计信息
        self._stats = {
            "text_merged": 0,
            "text_removed": 0,
            "list_normalized": 0,
            "table_normalized": 0,
        }

        # 执行标准化
        new_doc = self._normalize_node(document)

        # 记录诊断信息
        if self.merge_text and self._stats["text_merged"] > 0:
            diag.info(f"Merged {self._stats['text_merged']} text nodes", code="NORM001")

        if self.remove_empty_text and self._stats["text_removed"] > 0:
            diag.info(f"Removed {self._stats['text_removed']} empty text nodes", code="NORM002")

        return PassResult(
            document=new_doc,
            metadata={"stats": self._stats},
        )

    # ============================================================
    # 节点标准化
    # ============================================================

    def _normalize_node(self, node: Node) -> Node:
        """
        递归标准化节点。

        参数:
            node: 要标准化的节点

        返回:
            Node: 标准化后的节点
        """
        # 处理不同类型的节点
        if isinstance(node, (Document, Heading, Paragraph, BlockQuote)):
            return self._normalize_container(node)
        elif isinstance(node, ListBlock):
            return self._normalize_list(node)
        elif isinstance(node, ListItem):
            return self._normalize_list_item(node)
        elif isinstance(node, Table):
            return self._normalize_table(node)
        elif isinstance(node, TableRow):
            return self._normalize_table_row(node)
        elif isinstance(node, TableCell):
            return self._normalize_table_cell(node)
        elif isinstance(node, (Strong, Emphasis, Link)):
            return self._normalize_inline_container(node)
        elif isinstance(node, Text):
            return self._normalize_text(node)
        else:
            # 其他节点保持不变
            return node

    # ============================================================
    # 容器节点标准化
    # ============================================================

    def _normalize_container(self, node: Node) -> Node:
        """
        标准化容器节点（Document, Heading, Paragraph, BlockQuote）。

        参数:
            node: 容器节点

        返回:
            Node: 标准化后的节点
        """
        # 递归标准化子节点
        children = list(node.iter_children())
        normalized = []

        for child in children:
            normalized_child = self._normalize_node(child)
            if normalized_child is None:
                continue

            # 处理多个节点的情况
            if isinstance(normalized_child, list):
                normalized.extend(normalized_child)
            else:
                normalized.append(normalized_child)

        # 合并相邻的 Text 节点
        if self.merge_text:
            normalized = self._merge_text_nodes(normalized)

        # 移除空 Text 节点
        if self.remove_empty_text:
            normalized = self._remove_empty_text(normalized)

        # 如果节点没有子节点，返回原节点（但可能为空）
        return node.replace_children(normalized)

    def _normalize_inline_container(self, node: Node) -> Node:
        """
        标准化行内容器节点（Strong, Emphasis, Link）。

        参数:
            node: 行内容器节点

        返回:
            Node: 标准化后的节点
        """
        # 递归标准化子节点
        children = list(node.iter_children())
        normalized = []

        for child in children:
            normalized_child = self._normalize_node(child)
            if normalized_child is None:
                continue
            if isinstance(normalized_child, list):
                normalized.extend(normalized_child)
            else:
                normalized.append(normalized_child)

        # 合并相邻的 Text 节点
        if self.merge_text:
            normalized = self._merge_text_nodes(normalized)

        # 移除空 Text 节点
        if self.remove_empty_text:
            normalized = self._remove_empty_text(normalized)

        # 检查是否应该移除空的容器
        if not normalized:
            return None

        return node.replace_children(normalized)

    # ============================================================
    # 文本节点处理
    # ============================================================

    def _normalize_text(self, node: Text) -> Optional[Text]:
        """
        标准化文本节点。

        参数:
            node: 文本节点

        返回:
            Optional[Text]: 标准化后的文本节点，如果为空则返回 None
        """
        # 去除首尾空白
        content = node.content

        # 如果是空文本且需要移除
        if self.remove_empty_text and not content:
            self._stats["text_removed"] += 1
            return None

        return node

    def _merge_text_nodes(self, nodes: List[Node]) -> List[Node]:
        """
        合并相邻的 Text 节点。

        参数:
            nodes: 节点列表

        返回:
            List[Node]: 合并后的节点列表
        """
        if not nodes:
            return []

        merged = []
        current_text = ""

        for node in nodes:
            if isinstance(node, Text):
                current_text += node.content
            else:
                # 如果有累积的文本，先添加
                if current_text:
                    merged.append(Text(content=current_text))
                    current_text = ""
                merged.append(node)

        # 添加剩余的文本
        if current_text:
            merged.append(Text(content=current_text))

        # 统计合并的文本节点
        if len(nodes) > len(merged):
            self._stats["text_merged"] += len(nodes) - len(merged)

        return merged

    def _remove_empty_text(self, nodes: List[Node]) -> List[Node]:
        """
        移除空的 Text 节点。

        参数:
            nodes: 节点列表

        返回:
            List[Node]: 移除空文本后的节点列表
        """
        result = []
        for node in nodes:
            if isinstance(node, Text):
                if node.content.strip() or not self.remove_empty_text:
                    result.append(node)
                else:
                    self._stats["text_removed"] += 1
            else:
                result.append(node)

        return result

    # ============================================================
    # 列表结构标准化
    # ============================================================

    def _normalize_list(self, node: ListBlock) -> ListBlock:
        """
        标准化列表结构。

        参数:
            node: 列表节点

        返回:
            ListBlock: 标准化后的列表节点
        """
        if not self.normalize_list:
            return node

        # 递归标准化列表项
        items = []
        for item in node.items:
            normalized_item = self._normalize_list_item(item)
            if normalized_item:
                items.append(normalized_item)

        # 移除空的列表项
        items = [item for item in items if item.children]

        # 如果列表为空，返回 None（由父节点处理）
        if not items:
            return None

        return node.replace_children(items)

    def _normalize_list_item(self, node: ListItem) -> Optional[ListItem]:
        """
        标准化列表项。

        参数:
            node: 列表项节点

        返回:
            Optional[ListItem]: 标准化后的列表项
        """
        # 标准化子节点
        children = []
        for child in node.children:
            normalized_child = self._normalize_node(child)
            if normalized_child:
                if isinstance(normalized_child, list):
                    children.extend(normalized_child)
                else:
                    children.append(normalized_child)

        # 合并相邻的段落（简化版）
        if children:
            normalized = []
            for child in children:
                if (
                    isinstance(child, Paragraph)
                    and normalized
                    and isinstance(normalized[-1], Paragraph)
                ):
                    # 合并段落内容
                    last_para = normalized[-1]
                    # 简单合并内容
                    merged_content = last_para.content + child.content
                    normalized[-1] = last_para.replace_children(merged_content)
                else:
                    normalized.append(child)
            children = normalized

        return node.replace_children(children)

    # ============================================================
    # 表格结构标准化
    # ============================================================

    def _normalize_table(self, node: Table) -> Table:
        """
        标准化表格结构。

        参数:
            node: 表格节点

        返回:
            Table: 标准化后的表格节点
        """
        if not self.normalize_table:
            return node

        # 标准化行
        rows = []
        for row in node.rows:
            normalized_row = self._normalize_table_row(row)
            if normalized_row:
                rows.append(normalized_row)

        # 如果表格为空，返回 None
        if not rows:
            return None

        # 检查列数一致性
        max_cols = max(len(row.cells) for row in rows)
        for row in rows:
            if len(row.cells) < max_cols:
                # 补充空单元格
                cells = list(row.cells)
                for _ in range(max_cols - len(row.cells)):
                    cells.append(TableCell(content=[]))
                rows[rows.index(row)] = row.replace_children(cells)

        return node.replace_children(rows)

    def _normalize_table_row(self, node: TableRow) -> Optional[TableRow]:
        """
        标准化表格行。

        参数:
            node: 表格行节点

        返回:
            Optional[TableRow]: 标准化后的表格行
        """
        cells = []
        for cell in node.cells:
            normalized_cell = self._normalize_table_cell(cell)
            if normalized_cell:
                cells.append(normalized_cell)

        if not cells:
            return None

        return node.replace_children(cells)

    def _normalize_table_cell(self, node: TableCell) -> Optional[TableCell]:
        """
        标准化表格单元格。

        参数:
            node: 表格单元格节点

        返回:
            Optional[TableCell]: 标准化后的表格单元格
        """
        # 标准化内容
        content = []
        for child in node.content:
            normalized_child = self._normalize_node(child)
            if normalized_child:
                if isinstance(normalized_child, list):
                    content.extend(normalized_child)
                else:
                    content.append(normalized_child)

        # 合并文本
        if self.merge_text:
            content = self._merge_text_nodes(content)

        # 移除空文本
        if self.remove_empty_text:
            content = self._remove_empty_text(content)

        return node.replace_children(content)

    # ============================================================
    # 统计信息
    # ============================================================

    def get_stats(self) -> Dict[str, int]:
        """
        获取标准化统计信息。

        返回:
            Dict[str, int]: 统计信息
        """
        return self._stats.copy()

    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "text_merged": 0,
            "text_removed": 0,
            "list_normalized": 0,
            "table_normalized": 0,
        }
