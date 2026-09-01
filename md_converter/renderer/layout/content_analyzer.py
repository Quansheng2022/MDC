"""
Content Analyzer - 内容类型分类器（第六章）

所有 AST Block 节点首先完成内容类型分类，并生成 ContentProfile，
供 Layout Estimation / Decision Engine 使用。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ...ast.nodes import (
    BlockQuote,
    CodeBlock,
    Diagram,
    Heading,
    Image,
    ListBlock,
    Node,
    Paragraph,
    Table,
)
from .language_detection import LanguageProfile, detect_language
from .layout_plan import ContentType

# ============================================================
# 单元格数据类型检测（第九章 9.2）
# ============================================================

_NUMBER_RE = re.compile(r"^[+-]?\d[\d,.]*(?:e[+-]?\d+)?$", re.IGNORECASE)
_PERCENTAGE_RE = re.compile(r"^[+-]?\d[\d,.]*%$")
_CURRENCY_RE = re.compile(r"^[$€£¥]\s*\d[\d,.]*|\d[\d,.]*\s*(?:USD|EUR|CNY|RMB|元|美元|人民币)$")
_DATE_RE = re.compile(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$|^\d{1,2}[-/]\d{1,2}[-/]\d{4}$")
_BOOLEAN_RE = re.compile(r"^(?:true|false|yes|no|是|否|✅|❌|✔|✘|√|×)$", re.IGNORECASE)
_URL_RE = re.compile(r"^(?:https?://|ftp://|www\.)\S+$", re.IGNORECASE)
_CODE_RE = re.compile(
    r"^`|`$|^[A-Za-z_][A-Za-z0-9_]*\(.*\)$|^\s*(?:def|class|import|return|if|for|while)\b"
)

_TYPE_PRIORITY = {
    "number": 0,
    "percentage": 1,
    "currency": 2,
    "date": 3,
    "boolean": 4,
    "url": 5,
    "code": 6,
    "text": 7,
}


def detect_cell_data_type(text: str) -> str:
    """
    检测单元格数据类型（9.2）。

    返回:
        str: text | number | percentage | currency | date | boolean | url | code
    """
    value = text.strip()
    if not value:
        return "text"
    if _PERCENTAGE_RE.match(value):
        return "percentage"
    if _CURRENCY_RE.match(value):
        return "currency"
    if _NUMBER_RE.match(value):
        return "number"
    if _DATE_RE.match(value):
        return "date"
    if _BOOLEAN_RE.match(value):
        return "boolean"
    if _URL_RE.match(value):
        return "url"
    if _CODE_RE.match(value):
        return "code"
    return "text"


def infer_table_column_types(table: Table) -> List[str]:
    """
    按列推断数据类型（多数表决）。

    参数:
        table: 表格 AST 节点

    返回:
        List[str]: 每列的数据类型列表
    """
    if not table.rows:
        return []
    max_cols = max(len(row.cells) for row in table.rows)
    column_types: List[str] = []
    for col in range(max_cols):
        samples: List[str] = []
        for row in table.rows:
            if col < len(row.cells):
                cell = row.cells[col]
                samples.append(cell.to_plain_text().strip())
        non_empty = [s for s in samples if s]
        if not non_empty:
            column_types.append("text")
            continue
        counts: Dict[str, int] = {}
        for sample in non_empty:
            dtype = detect_cell_data_type(sample)
            counts[dtype] = counts.get(dtype, 0) + 1
        # 多数表决；平票时优先更具体的数据类型（number > percentage > ... > text）
        best = max(
            counts,
            key=lambda k: (counts[k], -_TYPE_PRIORITY.get(k, 99)),
        )
        if counts[best] >= max(1, int(len(non_empty) * 0.6)):
            column_types.append(best)
        else:
            column_types.append("text")
    return column_types


def infer_table_kind(column_types: List[str]) -> ContentType:
    """
    根据列类型推断表格种类。

    返回:
        ContentType: table_general | table_financial | table_code
    """
    numeric = sum(1 for t in column_types if t in ("number", "percentage", "currency"))
    code = sum(1 for t in column_types if t == "code")
    if column_types and code >= max(1, len(column_types) // 2):
        return ContentType.TABLE_CODE
    if numeric >= 2:
        return ContentType.TABLE_FINANCIAL
    return ContentType.TABLE_GENERAL


# ============================================================
# ContentProfile
# ============================================================


@dataclass(frozen=True)
class ContentProfile:
    """内容画像：分类结果 + 布局估算所需特征。"""

    node_id: str
    content_type: ContentType
    text: str
    language: Optional[LanguageProfile] = None
    line_count: int = 0
    column_count: int = 0
    level: int = 0
    table_column_types: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "content_type": (
                self.content_type.value
                if isinstance(self.content_type, ContentType)
                else str(self.content_type)
            ),
            "text": self.text[:120],
            "cjk_ratio": round(self.language.cjk_ratio, 3) if self.language else None,
            "latin_ratio": round(self.language.latin_ratio, 3) if self.language else None,
            "line_count": self.line_count,
            "column_count": self.column_count,
            "level": self.level,
            "table_column_types": self.table_column_types,
        }


# ============================================================
# 分类器
# ============================================================


class ContentAnalyzer:
    """
    将 AST Block 节点分类为内容类型（第六章）。

    用法:
        analyzer = ContentAnalyzer()
        profiles = analyzer.analyze(document)
    """

    def __init__(self, long_word_threshold: int = 20):
        self._counter = 0
        self.long_word_threshold = long_word_threshold

    def analyze(self, document: Node) -> List[ContentProfile]:
        """遍历文档块节点并生成内容画像。"""
        self._counter = 0
        profiles: List[ContentProfile] = []
        for child in document.iter_children():
            profile = self._classify(child)
            if profile is not None:
                profiles.append(profile)
        return profiles

    def _next_id(self) -> str:
        self._counter += 1
        return f"blk_{self._counter:03d}"

    def _classify(self, node: Node) -> Optional[ContentProfile]:
        """分类单个块节点。"""
        node_id = self._next_id()
        if isinstance(node, Heading):
            text = node.to_plain_text()
            return ContentProfile(
                node_id=node_id,
                content_type=ContentType.HEADING,
                text=text,
                level=node.level,
                metadata={"ast_level": node.level},
            )
        if isinstance(node, Paragraph):
            text = node.to_plain_text()
            language = detect_language(text, long_word_threshold=self.long_word_threshold)
            if language.url_heavy and not text.strip():
                content_type = ContentType.URL
            elif language.url_heavy:
                content_type = ContentType.URL
            elif language.code_heavy:
                content_type = ContentType.PROSE_MIXED
            elif language.cjk_ratio > 0.55:
                content_type = ContentType.PROSE_CJK
            elif language.latin_ratio > 0.60:
                content_type = ContentType.PROSE_LATIN
            else:
                content_type = ContentType.PROSE_MIXED
            return ContentProfile(
                node_id=node_id,
                content_type=content_type,
                text=text,
                language=language,
                line_count=len(text.splitlines()),
            )
        if isinstance(node, ListBlock):
            text = node.to_plain_text()
            language = detect_language(text, long_word_threshold=self.long_word_threshold)
            return ContentProfile(
                node_id=node_id,
                content_type=ContentType.LIST,
                text=text,
                language=language,
                line_count=len(node.items),
            )
        if isinstance(node, Table):
            column_types = infer_table_column_types(node)
            kind = infer_table_kind(column_types)
            return ContentProfile(
                node_id=node_id,
                content_type=kind,
                text=node.to_plain_text(),
                line_count=len(node.rows),
                column_count=max((len(r.cells) for r in node.rows), default=0),
                table_column_types=column_types,
                metadata={"ast_level": 0},
            )
        if isinstance(node, CodeBlock):
            line_count = len(node.text.splitlines())
            content_type = ContentType.CODE_SHORT if line_count <= 25 else ContentType.CODE_LONG
            return ContentProfile(
                node_id=node_id,
                content_type=content_type,
                text=node.text,
                line_count=line_count,
                metadata={"language": node.language},
            )
        if isinstance(node, Diagram):
            content_type = (
                ContentType.ASCII_DIAGRAM if node.diagram_type == "ascii" else ContentType.FIGURE
            )
            return ContentProfile(
                node_id=node_id,
                content_type=content_type,
                text=node.content,
                line_count=len(node.content.splitlines()),
                metadata={"diagram_type": node.diagram_type},
            )
        if isinstance(node, BlockQuote):
            text = node.to_plain_text()
            language = detect_language(text, long_word_threshold=self.long_word_threshold)
            return ContentProfile(
                node_id=node_id,
                content_type=ContentType.QUOTE,
                text=text,
                language=language,
            )
        if isinstance(node, Image):
            return ContentProfile(
                node_id=node_id,
                content_type=ContentType.FIGURE,
                text=node.alt or "",
                metadata={"src": node.src},
            )
        # 其他节点（HorizontalRule 等）不参与布局决策
        return None
