"""
Simple Table Pass - 空白对齐简单表格识别（P12-CAND-001）

识别"作者用空白对齐书写、并带有横线分隔行（ruler）"的两列块，转换为既有
``Table`` AST 节点。识别规则刻意保守：任何条件不满足都保留原 ``Paragraph``，
且默认不产生诊断（CLAR-01：识别失败不是错误/警告条件）。

安全原则:
    FALSE POSITIVE TABLE CONVERSION 比 FALSE NEGATIVE RECOGNITION 更有害。

职责边界:
    - 本 Pass 仅做 AST -> AST 转换，复用既有 ``Table`` / ``TableRow`` / ``TableCell``。
    - 不修改 Parser 语义、不接触 Word 对象、不做 I/O、不依赖任何外部语料。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from ...ast.nodes import Document, Node, Paragraph, SoftBreak, Table, TableCell, TableRow, Text
from ...diagnostics.collector import DiagnosticCollector
from .base import PassResult, TransformPass

#: Ruler 行：仅空格 +（>= 2 段 >= 3 个连字符，段间至少 1 个空格）
RULER_RE = re.compile(r"^ *-{3,}(?: +-{3,})+ *$")

#: 列间隔：>= 2 个连续空格
GAP_RE = re.compile(r" {2,}")


def paragraph_lines(paragraph: Paragraph) -> Optional[List[str]]:
    """
    将段落内容重建为行列表。

    仅当段落只包含 ``Text`` / ``SoftBreak`` 时可用（R7）；行尾空白被去除。

    参数:
        paragraph: 目标段落节点。

    返回:
        Optional[List[str]]: 行列表；包含富文本/行内节点时返回 ``None``。
    """
    lines: List[str] = []
    current: List[str] = []
    for node in paragraph.content:
        if isinstance(node, Text):
            current.append(node.content)
        elif isinstance(node, SoftBreak):
            lines.append("".join(current))
            current = []
        else:
            return None
    lines.append("".join(current))
    return [line.rstrip() for line in lines]


def recognize_simple_table(lines: List[str]) -> Optional[List[List[str]]]:
    """
    识别两列空白对齐简单表格（R1..R6）。

    规则（全部满足才识别）:
        R1 至少 3 行；
        R2 第 2 行是 ruler 行（仅空格与 >= 2 段连字符，段间至少 1 个空格）；
        R3 其余每行恰好含 1 段 >= 2 个连续空格的列间隔，且不含制表符；
        R4 其余每行按列间隔切分后的两个单元格均非空；
        R5 所有列间隔区间存在公共锚点 ``b = max(起始) < min(结束)``；
        R6 任何行都不含 ``|``。

    ruler 行只作为标记，不参与列锚点计算（真实语料中 ruler 与数据列并不对齐）。

    参数:
        lines: 段落重建行（已去除行尾空白）。

    返回:
        Optional[List[List[str]]]: 单元格矩阵（首行为表头行，不含 ruler 行）；
        未识别时返回 ``None``。
    """
    if len(lines) < 3:
        return None
    if not RULER_RE.match(lines[1]):
        return None
    if any("|" in line for line in lines):
        return None
    if any("\t" in line for line in lines):
        return None

    spans: List[tuple] = []
    for idx, line in enumerate(lines):
        if idx == 1:
            continue
        gaps = list(GAP_RE.finditer(line))
        if len(gaps) != 1:
            return None
        start, end = gaps[0].start(), gaps[0].end()
        if not line[:start].strip() or not line[end:].strip():
            return None
        spans.append((start, end))

    anchor = max(start for start, _ in spans)
    if anchor >= min(end for _, end in spans):
        return None

    rows: List[List[str]] = []
    for idx, line in enumerate(lines):
        if idx == 1:
            continue
        rows.append([line[:anchor].strip(), line[anchor:].strip()])
    return rows


class SimpleTablePass(TransformPass):
    """
    空白对齐简单表格识别 Pass（P12-CAND-001）。

    遍历 ``Document`` 的直接子节点；识别成功的 ``Paragraph`` 原位替换为 ``Table``，
    其余节点保持不变。默认不产生诊断。
    """

    def run(self, document: Node, diag: DiagnosticCollector) -> PassResult:
        """
        执行识别转换。

        参数:
            document: 待转换 AST 根节点。
            diag: 诊断收集器（本 Pass 默认不写入诊断）。

        返回:
            PassResult: 转换后的文档与统计信息。
        """
        if not isinstance(document, Document):
            return PassResult(document=document)

        converted = 0
        children: List[Node] = []
        for child in document.children:
            table = self._convert(child)
            if table is None:
                children.append(child)
            else:
                children.append(table)
                converted += 1

        if converted == 0:
            return PassResult(document=document, metadata={"stats": self._stats(0)})

        new_document = document.replace_children(children)
        return PassResult(
            document=new_document,
            metadata={"stats": self._stats(converted)},
        )

    @staticmethod
    def _stats(converted: int) -> Dict[str, Any]:
        """构造统计信息。"""
        return {"converted": converted}

    def _convert(self, node: Node) -> Optional[Table]:
        """
        尝试将单个节点转换为简单表格。

        参数:
            node: 待检查节点。

        返回:
            Optional[Table]: 识别成功时返回表格节点，否则返回 ``None``。
        """
        if not isinstance(node, Paragraph):
            return None
        lines = paragraph_lines(node)
        if lines is None:
            return None
        rows = recognize_simple_table(lines)
        if rows is None:
            return None
        return self._build_table(rows, node)

    @staticmethod
    def _build_table(rows: List[List[str]], source: Paragraph) -> Table:
        """
        由单元格矩阵构建 ``Table`` 节点。

        参数:
            rows: 单元格矩阵（首行重复为 Word 表头）。
            source: 源段落（用于保留源码位置）。

        返回:
            Table: 表格 AST 节点。
        """
        table_rows = [
            TableRow(
                cells=[TableCell(content=[Text(content=cell)]) for cell in row], span=source.span
            )
            for row in rows
        ]
        return Table(rows=table_rows, span=source.span)


__all__ = ["SimpleTablePass", "paragraph_lines", "recognize_simple_table"]
