"""
LayoutPlan - V1.5 中间表示（第七章）

LayoutDecisionEngine 输出的唯一产物，Renderer 仅负责执行 Plan。
支持 JSON 序列化，用于调试、审计与测试回放。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ContentType(str, Enum):
    """V1.5 内容类型分类器（第六章）。"""

    PROSE_CJK = "prose_cjk"
    PROSE_LATIN = "prose_latin"
    PROSE_MIXED = "prose_mixed"
    HEADING = "heading"
    LIST = "list"
    QUOTE = "quote"
    TABLE_GENERAL = "table_general"
    TABLE_FINANCIAL = "table_financial"
    TABLE_CODE = "table_code"
    CODE_SHORT = "code_short"
    CODE_LONG = "code_long"
    INLINE_CODE = "inline_code"
    ASCII_DIAGRAM = "ascii_diagram"
    FIGURE = "figure"
    URL = "url"
    FORMULA = "formula"
    FOOTNOTE = "footnote"
    METADATA = "metadata"


@dataclass(frozen=True)
class Margins:
    """页边距（厘米）。"""

    top: float = 2.54
    bottom: float = 2.54
    left: float = 2.54
    right: float = 2.54

    def to_dict(self) -> Dict[str, float]:
        return {
            "top": self.top,
            "bottom": self.bottom,
            "left": self.left,
            "right": self.right,
        }


@dataclass(frozen=True)
class FontSpec:
    """字体规格（可覆盖默认主题）。"""

    ascii: Optional[str] = None
    h_ansi: Optional[str] = None
    east_asia: Optional[str] = None
    cs: Optional[str] = None
    size_pt: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ascii": self.ascii,
            "hAnsi": self.h_ansi,
            "eastAsia": self.east_asia,
            "cs": self.cs,
            "size_pt": self.size_pt,
        }


@dataclass(frozen=True)
class SectionPlan:
    """Section 决策（第九章 / 第 7.1 节）。"""

    id: str
    orientation: str = "portrait"  # portrait | landscape
    page_size: str = "A4"  # A4 | Letter
    margins: Margins = field(default_factory=Margins)
    page_break_before: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "orientation": self.orientation,
            "page_size": self.page_size,
            "margins": self.margins.to_dict(),
            "page_break_before": self.page_break_before,
        }


@dataclass(frozen=True)
class BlockPlan:
    """块级布局指令（第 7.1 节）。"""

    id: str
    type: ContentType
    original_ast_id: str = ""
    page_break_before: bool = False
    keep_together: bool = False
    allow_split: bool = False
    keep_with_next: bool = False
    widow_orphan_control: bool = False
    font_override: Optional[FontSpec] = None
    width_override_cm: Optional[float] = None
    height_override_cm: Optional[float] = None
    alignment_override: Optional[str] = None
    repeat_header: bool = False
    max_lines_per_page: Optional[int] = None
    landscape: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, ContentType) else str(self.type),
            "original_ast_id": self.original_ast_id,
            "page_break_before": self.page_break_before,
            "keep_together": self.keep_together,
            "allow_split": self.allow_split,
            "keep_with_next": self.keep_with_next,
            "widow_orphan_control": self.widow_orphan_control,
            "font_override": self.font_override.to_dict() if self.font_override else None,
            "width_override_cm": self.width_override_cm,
            "height_override_cm": self.height_override_cm,
            "alignment_override": self.alignment_override,
            "repeat_header": self.repeat_header,
            "max_lines_per_page": self.max_lines_per_page,
            "landscape": self.landscape,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class LayoutPlan:
    """
    V1.5 中间表示（第 7.1 节）。

    属性:
        version: 计划版本（"1.5"）
        sections: Section 决策列表
        blocks: 块级指令列表
        metadata: 附加元数据（主题名、QA 结果等）
    """

    version: str = "1.5"
    sections: List[SectionPlan] = field(default_factory=list)
    blocks: List[BlockPlan] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "sections": [s.to_dict() for s in self.sections],
            "blocks": [b.to_dict() for b in self.blocks],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LayoutPlan":
        """从字典重建 LayoutPlan（JSON 回放支持）。"""
        sections = [
            SectionPlan(
                id=s["id"],
                orientation=s.get("orientation", "portrait"),
                page_size=s.get("page_size", "A4"),
                margins=Margins(**s.get("margins", {})),
                page_break_before=s.get("page_break_before", False),
            )
            for s in data.get("sections", [])
        ]
        blocks = []
        for b in data.get("blocks", []):
            font = None
            if b.get("font_override"):
                fo = b["font_override"]
                font = FontSpec(
                    ascii=fo.get("ascii"),
                    h_ansi=fo.get("hAnsi"),
                    east_asia=fo.get("eastAsia"),
                    cs=fo.get("cs"),
                    size_pt=fo.get("size_pt"),
                )
            blocks.append(
                BlockPlan(
                    id=b["id"],
                    type=ContentType(b["type"]),
                    original_ast_id=b.get("original_ast_id", ""),
                    page_break_before=b.get("page_break_before", False),
                    keep_together=b.get("keep_together", False),
                    allow_split=b.get("allow_split", False),
                    keep_with_next=b.get("keep_with_next", False),
                    widow_orphan_control=b.get("widow_orphan_control", False),
                    font_override=font,
                    width_override_cm=b.get("width_override_cm"),
                    height_override_cm=b.get("height_override_cm"),
                    alignment_override=b.get("alignment_override"),
                    repeat_header=b.get("repeat_header", False),
                    max_lines_per_page=b.get("max_lines_per_page"),
                    landscape=b.get("landscape", False),
                    metadata=b.get("metadata", {}),
                )
            )
        return cls(
            version=data.get("version", "1.5"),
            sections=sections,
            blocks=blocks,
            metadata=data.get("metadata", {}),
        )

    def to_json(self, indent: int = 2) -> str:
        """导出 JSON 字符串。"""
        import json

        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "LayoutPlan":
        """从 JSON 字符串重建 LayoutPlan。"""
        import json

        return cls.from_dict(json.loads(json_str))
