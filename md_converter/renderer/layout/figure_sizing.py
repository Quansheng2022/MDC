"""
Figure Sizing - 图形尺寸策略（P12-CAND-002）

将主题声明的 figure 策略与页面内容区几何转换为确定的图形尺寸。

职责边界:
    - 本模块只做纯计算与主题取值解析，不接触 Word 对象、不做 I/O。
    - 有效内容区由调用方提供的 section 几何给出（CLAR-02）；A4/1in 仅作为缺少
      section 几何时的参考基线，不作为通用魔数。
    - 最终物理分页由 Word 决定，本模块不承诺页码结果。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

#: 1 英寸 = 2.54 厘米
CM_PER_INCH = 2.54

#: 支持的主题长度单位（后缀 -> 厘米系数）
_LENGTH_UNITS: tuple[tuple[str, float], ...] = (
    ("cm", 1.0),
    ("mm", 0.1),
    ("in", CM_PER_INCH),
    ("pt", CM_PER_INCH / 72.0),
    ("px", CM_PER_INCH / 96.0),
)


def parse_length_cm(value: Any, default: Optional[float] = None) -> Optional[float]:
    """
    解析主题长度值为厘米。

    参数:
        value: 形如 ``"8cm"`` / ``"1in"`` / ``"10.5pt"`` / 数值 的长度值；``None`` 表示未声明。
        default: 无法解析时返回的默认值。

    返回:
        Optional[float]: 厘米数值；未声明或不可解析时返回 ``default``。
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().lower()
    if not text:
        return default
    for suffix, factor in _LENGTH_UNITS:
        if text.endswith(suffix):
            try:
                return float(text[: -len(suffix)].strip()) * factor
            except ValueError:
                return default
    try:
        return float(text)
    except ValueError:
        return default


@dataclass(frozen=True)
class FigurePolicy:
    """
    图形尺寸策略（主题 ``figure`` 块的类型化视图）。

    属性:
        max_width_cm: 最大宽度（厘米）；``None`` 表示使用有效内容区宽度。
        max_height_cm: 最大高度（厘米）；``None`` 表示使用有效内容区高度。
        min_width_cm: 最小宽度下限（厘米）；``None`` 表示未声明下限。
        preserve_aspect_ratio: 是否保持宽高比。
        alignment: 对齐方式（``center`` / ``left`` / ``right`` / ``None``）。
        keep_together: 是否阻止图形跨页。
    """

    max_width_cm: Optional[float] = None
    max_height_cm: Optional[float] = None
    min_width_cm: Optional[float] = None
    preserve_aspect_ratio: bool = True
    alignment: Optional[str] = None
    keep_together: bool = True


def figure_policy_from_data(data: Optional[Mapping[str, Any]]) -> FigurePolicy:
    """
    从主题 ``figure`` 字典构建策略。

    主题中的 ``content_width`` / ``available_page_height`` 是"使用有效内容区"的声明，
    解析为 ``None``，由调用方以 section 几何补齐（CLAR-02）。

    参数:
        data: 主题 ``figure`` 块；``None`` 或空字典时返回"内容区边界"策略。

    返回:
        FigurePolicy: 类型化策略。
    """
    block: Mapping[str, Any] = data or {}

    def _dimension(key: str) -> Optional[float]:
        raw = block.get(key)
        if raw is None:
            return None
        if isinstance(raw, (int, float)) and not isinstance(raw, bool):
            return float(raw)
        text = str(raw).strip().lower()
        if text in {
            "content_width",
            "available_page_height",
            "available_page_width",
            "auto",
        }:
            return None
        return parse_length_cm(text, None)

    alignment_raw = block.get("alignment")
    return FigurePolicy(
        max_width_cm=_dimension("max_width"),
        max_height_cm=_dimension("max_height"),
        min_width_cm=_dimension("min_width"),
        preserve_aspect_ratio=bool(block.get("preserve_aspect_ratio", True)),
        alignment=str(alignment_raw).strip().lower() if alignment_raw else None,
        keep_together=bool(block.get("keep_together", True)),
    )


def figure_policy_from_theme(theme: Any) -> FigurePolicy:
    """
    从主题对象构建图形尺寸策略。

    兼容 V1.5 主题（``theme.data['figure']``）与未声明该块的主题实现。

    参数:
        theme: 主题对象（可含 ``data`` 字典）。

    返回:
        FigurePolicy: 主题声明的策略；未声明时使用有效内容区边界且不设宽度下限。
    """
    data = getattr(theme, "data", None)
    if isinstance(data, Mapping):
        block = data.get("figure")
        if isinstance(block, Mapping):
            return figure_policy_from_data(block)
    return FigurePolicy()


@dataclass(frozen=True)
class FigureFit:
    """
    图形尺寸计算结果。

    属性:
        width_cm: 最终宽度（厘米）。
        height_cm: 最终高度（厘米）。
        scaled: 是否发生了缩小。
        below_min_width: 最终宽度是否低于主题声明的最小宽度下限。
    """

    width_cm: float
    height_cm: float
    scaled: bool
    below_min_width: bool


@dataclass(frozen=True)
class FigureFitPlan:
    """
    图形适配决策（Program D / WP-D04：图形适配的**唯一**决策产物）。

    记录最终尺寸以及缩小的**原因**，便于渲染层与验证层观测：
    由有效内容宽度导致的收敛（``width_limited``）与由有效内容高度导致的
    收缩（``height_limited``）是互相独立的事实。

    属性:
        width_cm: 最终宽度（厘米）。
        height_cm: 最终高度（厘米）。
        aspect_ratio: 宽高比（px_width / px_height）；恒等于固有宽高比。
        target_width_cm: 目标宽度（``min(配置 image_width, 有效宽度)``，SPEC-FUNC-023）。
        content_width_cm: 有效内容区宽度（厘米）。
        content_height_cm: 有效内容区高度（厘米）。
        scaled: 是否发生了缩小。
        height_limited: 是否因有效内容高度而收缩。
        width_limited: 目标宽度是否被有效内容宽度收敛。
        below_min_width: 最终宽度是否低于主题声明的最小宽度下限。
    """

    width_cm: float
    height_cm: float
    aspect_ratio: float
    target_width_cm: float
    content_width_cm: float
    content_height_cm: float
    scaled: bool
    height_limited: bool
    width_limited: bool
    below_min_width: bool

    def to_dict(self) -> Dict[str, Any]:
        """导出可序列化字典（证据/审计用，带稳定舍入）。"""
        return {
            "width_cm": round(self.width_cm, 4),
            "height_cm": round(self.height_cm, 4),
            "aspect_ratio": round(self.aspect_ratio, 6),
            "target_width_cm": round(self.target_width_cm, 4),
            "content_width_cm": round(self.content_width_cm, 4),
            "content_height_cm": round(self.content_height_cm, 4),
            "scaled": self.scaled,
            "height_limited": self.height_limited,
            "width_limited": self.width_limited,
            "below_min_width": self.below_min_width,
        }


class FigureMeasurementError(ValueError):
    """图形固有尺寸不可用（不可测量）时抛出。"""


def plan_figure_fit(
    *,
    intrinsic_width_px: int,
    intrinsic_height_px: int,
    target_width_cm: float,
    content_width_cm: float,
    content_height_cm: float,
    min_width_cm: Optional[float] = None,
    tolerance_cm: float = 1e-6,
) -> FigureFitPlan:
    """
    计算确定性的图形适配决策（Program D / WP-D04）。

    规则（保持冻结的 SPEC-FUNC-023 语义，不引入任何新的放大幅度）:
        1. 目标宽度 ``target_width_cm`` 由调用方按 ``min(配置 image_width, 有效宽度)`` 解析；
           交付宽度取 ``min(target, 有效宽度)``——既不超过目标宽度，也不超出有效内容区宽度。
        2. 若按该宽度计算的高度超过有效内容区高度，则按高度收缩（保持宽高比）；
        3. 结果永不裁剪、永不拉伸（宽高比恒为固有宽高比）、永不超出有效内容区；
        4. 收缩后宽度低于 ``min_width_cm`` 时标记 ``below_min_width``（仍按适配尺寸交付，
           由调用方产生结构化 WARNING）。

    参数:
        intrinsic_width_px: 图形固有像素宽（> 0）。
        intrinsic_height_px: 图形固有像素高（> 0）。
        target_width_cm: 目标宽度（厘米）。
        content_width_cm: 有效内容区宽度（厘米）。
        content_height_cm: 有效内容区高度（厘米）。
        min_width_cm: 主题声明的最小宽度下限（厘米，可选）。
        tolerance_cm: 浮点比较容差。

    返回:
        FigureFitPlan: 最终尺寸、宽高比与缩小原因。

    异常:
        FigureMeasurementError: 固有尺寸非法（<= 0）或边界非法（<= 0）。
    """
    if intrinsic_width_px <= 0 or intrinsic_height_px <= 0:
        raise FigureMeasurementError(
            f"Invalid intrinsic size: {intrinsic_width_px}x{intrinsic_height_px} px"
        )
    if target_width_cm <= 0 or content_width_cm <= 0 or content_height_cm <= 0:
        raise FigureMeasurementError(
            "Invalid figure bounds: "
            f"target={target_width_cm}cm max_width={content_width_cm}cm "
            f"max_height={content_height_cm}cm"
        )

    aspect = intrinsic_width_px / intrinsic_height_px

    width_limited = float(target_width_cm) > float(content_width_cm) + tolerance_cm
    width_cm = min(float(target_width_cm), float(content_width_cm))
    height_cm = width_cm / aspect
    height_limited = False
    scaled = width_limited

    if height_cm > content_height_cm + tolerance_cm:
        height_cm = float(content_height_cm)
        width_cm = height_cm * aspect
        height_limited = True
        scaled = True

    below_min_width = min_width_cm is not None and width_cm < min_width_cm - tolerance_cm

    return FigureFitPlan(
        width_cm=width_cm,
        height_cm=height_cm,
        aspect_ratio=aspect,
        target_width_cm=float(target_width_cm),
        content_width_cm=float(content_width_cm),
        content_height_cm=float(content_height_cm),
        scaled=scaled,
        height_limited=height_limited,
        width_limited=width_limited,
        below_min_width=below_min_width,
    )


def fit_figure_size(
    px_width: int,
    px_height: int,
    target_width_cm: float,
    max_width_cm: float,
    max_height_cm: float,
    min_width_cm: Optional[float] = None,
    tolerance_cm: float = 1e-6,
) -> FigureFit:
    """
    计算符合有效内容区的图形尺寸（保持宽高比，永不放大）。

    规则:
        1. 目标宽度 ``target_width_cm`` 不超过有效内容区宽度；
        2. 若按目标宽度计算的高度超过有效内容区高度，则按高度收缩（保持宽高比）；
        3. 永不放大超过目标宽度，且永不超出有效内容区的宽/高；
        4. 收缩后宽度低于 ``min_width_cm`` 时标记 ``below_min_width``（仍按适配尺寸交付）。

    参数:
        px_width: 图形固有像素宽（> 0）。
        px_height: 图形固有像素高（> 0）。
        target_width_cm: 目标宽度（厘米）。
        max_width_cm: 有效内容区宽度（厘米）。
        max_height_cm: 有效内容区高度（厘米）。
        min_width_cm: 主题声明的最小宽度下限（厘米，可选）。
        tolerance_cm: 浮点比较容差。

    返回:
        FigureFit: 最终尺寸与标记。

    异常:
        FigureMeasurementError: 固有尺寸非法（<= 0）或边界非法（<= 0）。
    """
    plan = plan_figure_fit(
        intrinsic_width_px=px_width,
        intrinsic_height_px=px_height,
        target_width_cm=target_width_cm,
        content_width_cm=max_width_cm,
        content_height_cm=max_height_cm,
        min_width_cm=min_width_cm,
        tolerance_cm=tolerance_cm,
    )
    return FigureFit(
        width_cm=plan.width_cm,
        height_cm=plan.height_cm,
        scaled=plan.scaled,
        below_min_width=plan.below_min_width,
    )
