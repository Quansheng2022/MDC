"""
Table Fitting - 表格适配策略（Program D / WP-D02）

把「有效内容宽度 + 表格内容信号 + 生效排版值」转换为一个**确定的**表格适配决策
（列宽分配 / 目标总宽 / 有界字号）。

职责边界:
    - 本模块只做纯计算：不接触 Word 对象、不做 I/O、不使用 Qt、不打印。
    - 不按 profile ID 分支：调用方传入的是**解析后的**有效宽度与字号
      （``SPEC-ARCH-009``：Themes 控制外观，Renderer 控制结构）。
    - 不修改内容：只决定列宽与表格字号，永不删除/截断/改写单元格文本。
    - 不做无界收缩：最小列宽下限（``table.constraints.min_width``）与
      可读性下限（``readability.minimum.table_font`` = 8.5pt）是硬边界。

决策优先级（Program D 产品规格 §6.1）:
    1. 优先有效利用可用内容宽度；
    2. 有内容证据时按内容比例分配，而不是等分；
    3. 保留 Word 自动换行（不做内容变换）；
    4. 只在必要时做有界紧凑化；
    5. 字号只在可读性下限之内下降；
    6. 即使无法完美适配也完整保留内容（``squeezed`` 标记 + 结构化诊断由调用方产生）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Sequence, Tuple

__all__ = [
    "DEFAULT_CHAR_WIDTH_CM",
    "DEFAULT_FONT_STEP_PT",
    "DEFAULT_MIN_COLUMN_WIDTH_CM",
    "DEFAULT_NARROW_FILL_RATIO",
    "DEFAULT_READABILITY_FLOOR_PT",
    "DEFAULT_SIGNAL_CHAR_CAP",
    "TableFitError",
    "TableFitPlan",
    "column_signal_lengths",
    "plan_table_fit",
]

#: 每字符宽度估算（厘米）；与既有 ``section_manager.estimate_table_width_cm`` 的
#: 9.5pt 参考估算保持一致，便于同一文档内两种估算给出可比结果。
DEFAULT_CHAR_WIDTH_CM = 0.19

#: 最小列宽（厘米）；等于冻结主题 ``table.constraints.min_width = 1.2cm``。
DEFAULT_MIN_COLUMN_WIDTH_CM = 1.2

#: 表格字号可读性下限（磅）；等于冻结主题 ``readability.minimum.table_font = 8.5pt``。
DEFAULT_READABILITY_FLOOR_PT = 8.5

#: 窄表判定阈值：表格自然宽度低于有效宽度的该比例时，**不**拉伸到整页宽度
#: （Program D 产品规格 §11.1「窄表不得被不必要地放大或劣化」）。
DEFAULT_NARROW_FILL_RATIO = 0.6

#: 单列宽度估算的字符上限：避免单个长文本列独占整页宽度。
DEFAULT_SIGNAL_CHAR_CAP = 48

#: 有界紧凑化时的单档字号步长（磅）。
DEFAULT_FONT_STEP_PT = 0.5


class TableFitError(ValueError):
    """表格适配输入非法（表格为空或边界值非法）时抛出。"""


@dataclass(frozen=True)
class TableFitPlan:
    """
    表格适配决策（纯数据，可序列化用于证据记录）。

    属性:
        column_widths_cm: 每列最终宽度（厘米，按可见列顺序）。
        total_width_cm: 目标表格总宽（厘米）；正常情况 <= 有效内容宽度。
        font_size_pt: 表格最终字号（磅，永不低于可读性下限）。
        fixed_layout: 是否要求固定列宽布局（``w:tblLayout type="fixed"``）。
        filled_content_width: 是否按有效内容宽度铺满（False = 使用自然宽度）。
        squeezed: 是否已经到达最小列宽下限仍无法落在有效内容宽度内。
        min_column_width_cm: 生效的最小列宽下限（厘米）。
    """

    column_widths_cm: Tuple[float, ...]
    total_width_cm: float
    font_size_pt: float
    fixed_layout: bool
    filled_content_width: bool
    squeezed: bool
    min_column_width_cm: float

    def to_dict(self) -> Dict[str, Any]:
        """导出可序列化字典（证据/审计用，带稳定舍入）。"""
        return {
            "column_widths_cm": [round(w, 4) for w in self.column_widths_cm],
            "total_width_cm": round(self.total_width_cm, 4),
            "font_size_pt": round(self.font_size_pt, 4),
            "fixed_layout": self.fixed_layout,
            "filled_content_width": self.filled_content_width,
            "squeezed": self.squeezed,
            "min_column_width_cm": round(self.min_column_width_cm, 4),
            "column_count": len(self.column_widths_cm),
        }


def column_signal_lengths(rows: Sequence[Sequence[str]]) -> Tuple[int, ...]:
    """
    计算每列的廉价内容信号（最长可见单元格字符数）。

    使用确定性的、与语言无关的字符计数（无需 NLP）；参差不齐的行按缺失单元格
    计入长度 0。该信号只用于**列宽比例**，从不改写内容。

    参数:
        rows: 表格全部行（含表头行），每行为单元格纯文本序列。

    返回:
        Tuple[int, ...]: 每列最长可见字符数。

    异常:
        TableFitError: 表格为空或无可见列。
    """
    if not rows:
        raise TableFitError("Table has no rows")
    column_count = max((len(row) for row in rows), default=0)
    if column_count == 0:
        raise TableFitError("Table has no columns")

    signals = []
    for index in range(column_count):
        longest = 0
        for row in rows:
            if index < len(row):
                longest = max(longest, len(str(row[index])))
        signals.append(longest)
    return tuple(signals)


def plan_table_fit(
    rows: Sequence[Sequence[str]],
    *,
    content_width_cm: float,
    base_font_size_pt: float,
    min_column_width_cm: float = DEFAULT_MIN_COLUMN_WIDTH_CM,
    char_width_cm: float = DEFAULT_CHAR_WIDTH_CM,
    readability_floor_pt: float = DEFAULT_READABILITY_FLOOR_PT,
    narrow_fill_ratio: float = DEFAULT_NARROW_FILL_RATIO,
    signal_char_cap: int = DEFAULT_SIGNAL_CHAR_CAP,
    font_step_pt: float = DEFAULT_FONT_STEP_PT,
) -> TableFitPlan:
    """
    计算确定性的表格适配决策。

    算法（全部为纯算术，可重复）:
        自然宽度 ``natural_i = clamp(signal_i, 1, cap) × char_width``，再抬到最小列宽。
        需求宽度 ``required = Σ natural_i``；最小总宽 ``min_total = n × min_width``。

        1. ``required <= content_width``：按比例分配。当 ``required`` 已达到有效宽度的
           ``narrow_fill_ratio`` 时铺满有效宽度（有效利用页面），否则保持自然宽度
           （窄表不被不必要地放大）。
        2. ``required > content_width`` 且 ``min_total <= content_width``：按比例收缩
           「高于最小列宽的部分」，总宽落在有效宽度内，列宽不低于最小列宽。
        3. ``min_total > content_width``：不可再收缩。保留最小列宽、完整保留内容、
           标记 ``squeezed=True``，并由调用方记录限制（Program D §6.3）。

    字号规则: 仅在 ``squeezed``（已达最小列宽仍放不下）时下降一个有界档位
    ``font_step_pt``；结果永不低于 ``readability_floor_pt``。

    参数:
        rows: 表格全部行（含表头行）的单元格纯文本。
        content_width_cm: 有效内容宽度（厘米，来自实际 section 几何）。
        base_font_size_pt: 生效表格字号（磅，来自主题/配置解析结果）。
        min_column_width_cm: 最小列宽下限（厘米）。
        char_width_cm: 每字符宽度估算（厘米）。
        readability_floor_pt: 字号可读性下限（磅）。
        narrow_fill_ratio: 窄表不拉伸阈值（有效宽度的比例）。
        signal_char_cap: 单列信号字符上限。
        font_step_pt: 有界紧凑化的字号步长（磅）。

    返回:
        TableFitPlan: 列宽 / 总宽 / 字号 / 布局模式决策。

    异常:
        TableFitError: 表格为空，或宽度/字号/下限/阈值非法。
    """
    if content_width_cm <= 0:
        raise TableFitError(f"Invalid content width: {content_width_cm}")
    if base_font_size_pt <= 0:
        raise TableFitError(f"Invalid base font size: {base_font_size_pt}")
    if min_column_width_cm <= 0:
        raise TableFitError(f"Invalid minimum column width: {min_column_width_cm}")
    if char_width_cm <= 0:
        raise TableFitError(f"Invalid character width estimate: {char_width_cm}")
    if readability_floor_pt <= 0:
        raise TableFitError(f"Invalid readability floor: {readability_floor_pt}")
    if not 0 < narrow_fill_ratio <= 1:
        raise TableFitError(f"Invalid narrow fill ratio: {narrow_fill_ratio}")
    if signal_char_cap < 1:
        raise TableFitError(f"Invalid signal character cap: {signal_char_cap}")

    signals = column_signal_lengths(rows)
    column_count = len(signals)
    min_total = column_count * min_column_width_cm

    natural = []
    for signal in signals:
        clamped = min(max(signal, 1), signal_char_cap)
        natural.append(max(clamped * char_width_cm, min_column_width_cm))
    required = sum(natural)

    if required <= content_width_cm:
        if required >= content_width_cm * narrow_fill_ratio:
            total = float(content_width_cm)
            filled = True
        else:
            total = required
            filled = False
        scale = total / required
        widths = tuple(width * scale for width in natural)
        squeezed = False
    elif min_total <= content_width_cm:
        total = float(content_width_cm)
        filled = True
        # 按比例收缩「高于最小列宽的部分」，列宽下限保持不变。
        shrinkable = required - min_total
        allowed = total - min_total
        ratio = allowed / shrinkable if shrinkable > 0 else 0.0
        widths = tuple(
            min_column_width_cm + (width - min_column_width_cm) * ratio for width in natural
        )
        squeezed = False
    else:
        # 已达最小列宽下限仍无法落在有效内容宽度内：保留完整内容与可读字号。
        total = min_total
        filled = False
        widths = tuple(min_column_width_cm for _ in natural)
        squeezed = True

    font_size_pt = base_font_size_pt
    if squeezed:
        font_size_pt = base_font_size_pt - font_step_pt
    font_size_pt = max(readability_floor_pt, min(base_font_size_pt, font_size_pt))
    if base_font_size_pt < readability_floor_pt:
        # 主题字号本身低于下限（配置缺陷，StaticQA 已负责报警）：不额外加重违规。
        font_size_pt = readability_floor_pt

    return TableFitPlan(
        column_widths_cm=widths,
        total_width_cm=total,
        font_size_pt=font_size_pt,
        fixed_layout=True,
        filled_content_width=filled,
        squeezed=squeezed,
        min_column_width_cm=min_column_width_cm,
    )
