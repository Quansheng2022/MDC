"""
Section Manager - Section 决策（Portrait / Landscape）（第九章 9.3）

当表格宽度超过 Portrait 可用宽度（且缩小字号至 8.5pt 仍无法解决）时，
触发 Landscape Section。scope 为 local，并在表格结束后恢复原方向。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .content_analyzer import ContentProfile
from .layout_plan import Margins, SectionPlan
from .themes_v15_protocol import ThemeProtocol


@dataclass(frozen=True)
class PageGeometry:
    """A4 页面几何（厘米）。"""

    portrait_width_cm: float = 21.0
    portrait_height_cm: float = 29.7
    margins: Margins = Margins()

    @property
    def portrait_content_width_cm(self) -> float:
        return self.portrait_width_cm - self.margins.left - self.margins.right

    @property
    def landscape_content_width_cm(self) -> float:
        return self.portrait_height_cm - self.margins.left - self.margins.right


def estimate_table_width_cm(
    profile: ContentProfile,
    min_column_width_cm: float = 1.2,
    char_width_cm: float = 0.19,
) -> float:
    """
    估算表格所需宽度（厘米）。

    估算公式:
        column_width = max(min_column_width, max_cell_chars * char_width)

    参数:
        profile: 表格内容画像
        min_column_width_cm: 最小列宽（YAML table.constraints.min_width）
        char_width_cm: 每字符宽度估算（9.5pt 大约 0.19cm）

    返回:
        float: 估算宽度（厘米）
    """
    if not profile.table_column_types:
        return min_column_width_cm
    lines = [ln.strip() for ln in profile.text.splitlines() if ln.strip()]
    widths: List[float] = []
    for col in range(profile.column_count):
        max_chars = 0
        for line in lines:
            cells = _split_row_cells(line)
            if col < len(cells):
                max_chars = max(max_chars, len(cells[col]))
        if max_chars == 0:
            max_chars = 5
        widths.append(max(min_column_width_cm, max_chars * char_width_cm))
    return sum(widths)


def _split_row_cells(line: str) -> List[str]:
    """简单按 | 分割表格行（估算用）。"""
    if not line.startswith("|"):
        return []
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


class SectionManager:
    """
    生成 Section 计划。

    决策流程:
        1. 默认 Portrait Section
        2. 表格估算宽度 > Portrait 内容宽度 + buffer -> 触发 Landscape
        3. Landscape 作用域为 local（表格所在 Section），表格后恢复原方向
    """

    def __init__(
        self,
        theme: Optional[ThemeProtocol] = None,
        geometry: Optional[PageGeometry] = None,
    ):
        self.theme = theme
        self.geometry = geometry or PageGeometry()

    def build_sections(self, profiles: List[ContentProfile]) -> List[SectionPlan]:
        """
        根据内容画像生成 Section 计划。

        参数:
            profiles: 内容画像列表（按文档顺序）

        返回:
            List[SectionPlan]: Section 计划列表
        """
        sections: List[SectionPlan] = []
        current = SectionPlan(
            id="sec_1",
            orientation=self.theme.default_orientation if self.theme else "portrait",
            page_size="A4",
            margins=self.geometry.margins,
        )
        sections.append(current)

        for profile in profiles:
            if profile.content_type.value.startswith("table"):
                width = estimate_table_width_cm(profile)
                buffer = (
                    self.theme.landscape_width_margin_buffer_cm
                    if self.theme and hasattr(self.theme, "landscape_width_margin_buffer_cm")
                    else 1.0
                )
                available = self.geometry.portrait_content_width_cm
                if width > available + buffer:
                    # 触发 Landscape Section
                    landscape = SectionPlan(
                        id=f"sec_landscape_{len(sections)}",
                        orientation="landscape",
                        page_size="A4",
                        margins=self.geometry.margins,
                        page_break_before=True,
                    )
                    sections.append(landscape)
                    # 表格结束后恢复原方向
                    restore = SectionPlan(
                        id=f"sec_restore_{len(sections)}",
                        orientation="portrait",
                        page_size="A4",
                        margins=self.geometry.margins,
                        page_break_before=False,
                    )
                    sections.append(restore)
        return sections
