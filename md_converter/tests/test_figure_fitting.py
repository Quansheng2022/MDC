"""
Figure Fitting 策略测试（Program D / WP-D04）。

覆盖:
    - 小位图（固有尺寸小于目标宽度）：交付宽度不超过目标宽度；
    - 宽幅图形：目标宽度被有效内容宽度收敛（width_limited）；
    - 超高图形：按有效内容高度收缩（height_limited）且宽高比不变；
    - 横向大图：保持宽高比；
    - 精确边界图形：不与高度边界冲突（容差内不收缩）；
    - 永不裁剪 / 永不拉伸：宽高比恒等于固有宽高比；
    - 重复计算确定性；
    - profile 几何差异只通过解析后的有效内容区生效；
    - 非法输入显式失败（fail loudly）；
    - ``fit_figure_size`` 与 ``plan_figure_fit`` 是同一权威（无重复实现）。
"""

from typing import Optional

import pytest

from md_converter.renderer.layout.figure_sizing import (
    FigureMeasurementError,
    fit_figure_size,
    plan_figure_fit,
)

#: 冻结基线参考几何（A4 + 1in，见 SPEC-FUNC-023 CLAR-02）。
CONTENT_WIDTH_CM = 15.92
CONTENT_HEIGHT_CM = 24.62

#: 冻结默认目标宽度：``min(image_width = 5in, 有效宽度)``。
TARGET_WIDTH_CM = 12.7

#: Academic profile 的左右 3.0cm 页边距下的有效内容宽度。
ACADEMIC_CONTENT_WIDTH_CM = 15.0

#: Business profile 的左右 2.0cm 页边距下的有效内容宽度。
BUSINESS_CONTENT_WIDTH_CM = 17.0


def _plan(
    px_width: int,
    px_height: int,
    *,
    target_width_cm: float = TARGET_WIDTH_CM,
    content_width_cm: float = CONTENT_WIDTH_CM,
    content_height_cm: float = CONTENT_HEIGHT_CM,
    min_width_cm: Optional[float] = 8.0,
):
    """适配辅助函数：固定有效内容区，只变化图形本身。"""
    return plan_figure_fit(
        intrinsic_width_px=px_width,
        intrinsic_height_px=px_height,
        target_width_cm=target_width_cm,
        content_width_cm=content_width_cm,
        content_height_cm=content_height_cm,
        min_width_cm=min_width_cm,
    )


def test_small_raster_is_never_enlarged_beyond_the_target_width() -> None:
    """小位图：交付宽度等于目标宽度（不超过目标宽度，也不超过内容区）。"""
    plan = _plan(80, 40)

    assert plan.width_cm == pytest.approx(TARGET_WIDTH_CM)
    assert plan.height_cm == pytest.approx(TARGET_WIDTH_CM / 2.0)
    assert plan.width_cm <= plan.target_width_cm
    assert plan.width_cm <= plan.content_width_cm
    assert plan.scaled is False
    assert plan.height_limited is False
    assert plan.width_limited is False
    assert plan.below_min_width is False


def test_target_width_is_capped_by_the_effective_content_width() -> None:
    """宽幅图形：目标宽度超过有效内容宽度时收敛到内容宽度并记录原因。"""
    plan = _plan(4000, 1000, target_width_cm=30.0)

    assert plan.width_limited is True
    assert plan.scaled is True
    assert plan.width_cm == pytest.approx(CONTENT_WIDTH_CM)
    assert plan.height_cm == pytest.approx(CONTENT_WIDTH_CM / 4.0)
    assert plan.aspect_ratio == pytest.approx(4.0)
    assert plan.width_cm <= plan.content_width_cm


def test_tall_figure_is_scaled_to_the_effective_content_height() -> None:
    """超高图形：按有效内容高度收缩，宽高比保持。"""
    plan = _plan(30, 70)

    assert plan.height_limited is True
    assert plan.scaled is True
    assert plan.height_cm == pytest.approx(CONTENT_HEIGHT_CM)
    assert plan.width_cm == pytest.approx(CONTENT_HEIGHT_CM * 30 / 70)
    assert plan.width_cm / plan.height_cm == pytest.approx(30 / 70, rel=1e-9)
    assert plan.height_cm <= plan.content_height_cm


def test_landscape_figure_keeps_aspect_ratio() -> None:
    """横向大图：保持宽高比，不裁剪、不拉伸。"""
    plan = _plan(2000, 800)

    assert plan.aspect_ratio == pytest.approx(2.5)
    assert plan.width_cm / plan.height_cm == pytest.approx(2.5, rel=1e-9)
    assert plan.height_cm == pytest.approx(TARGET_WIDTH_CM / 2.5)
    assert plan.height_limited is False


def test_exact_boundary_figure_is_not_shrunk() -> None:
    """高度正好等于有效内容高度时不触发高度收缩（容差内）。"""
    plan = _plan(1270, 2462)

    assert plan.height_cm == pytest.approx(CONTENT_HEIGHT_CM, abs=1e-6)
    assert plan.height_limited is False
    assert plan.scaled is False
    assert plan.width_cm == pytest.approx(TARGET_WIDTH_CM)


@pytest.mark.parametrize(
    ("px_width", "px_height"),
    [(100, 100), (1, 1), (3000, 100), (100, 3000), (777, 333)],
)
def test_aspect_ratio_is_preserved_within_rounding_tolerance(px_width: int, px_height: int) -> None:
    """任何固有尺寸下宽高比都严格保持（仅受浮点/EMU 舍入影响）。"""
    plan = _plan(px_width, px_height)

    assert plan.aspect_ratio == pytest.approx(px_width / px_height)
    assert plan.width_cm / plan.height_cm == pytest.approx(px_width / px_height, rel=1e-9)
    assert plan.width_cm <= plan.content_width_cm + 1e-9
    assert plan.height_cm <= plan.content_height_cm + 1e-9


def test_repeated_planning_is_deterministic() -> None:
    """同一输入重复计算给出完全相同的决策（SPEC-INV-003）。"""
    first = _plan(30, 70)
    second = _plan(30, 70)

    assert first == second
    assert first.to_dict() == second.to_dict()


def test_below_min_width_is_reported_not_enforced_by_cropping() -> None:
    """收缩后低于最小宽度下限：仅标记，不裁剪、不放大内容。"""
    plan = _plan(10, 100)

    assert plan.below_min_width is True
    assert plan.width_cm < 8.0
    assert plan.height_cm == pytest.approx(CONTENT_HEIGHT_CM)
    assert plan.width_cm / plan.height_cm == pytest.approx(0.1, rel=1e-9)


@pytest.mark.parametrize(
    ("content_width_cm", "with_target_width_cm"),
    [
        (CONTENT_WIDTH_CM, 12.7),
        (ACADEMIC_CONTENT_WIDTH_CM, 12.7),
        (BUSINESS_CONTENT_WIDTH_CM, 12.7),
    ],
)
def test_profile_geometry_only_matters_when_the_target_exceeds_it(
    content_width_cm: float, with_target_width_cm: float
) -> None:
    """冻结默认目标（5in）在三种 profile 几何下都小于有效宽度 -> 结果一致。"""
    plan = _plan(2000, 800, target_width_cm=with_target_width_cm, content_width_cm=content_width_cm)

    assert plan.width_cm == pytest.approx(with_target_width_cm)
    assert plan.width_limited is False


@pytest.mark.parametrize(
    ("content_width_cm", "expected_width_cm"),
    [
        (CONTENT_WIDTH_CM, CONTENT_WIDTH_CM),
        (ACADEMIC_CONTENT_WIDTH_CM, ACADEMIC_CONTENT_WIDTH_CM),
        (BUSINESS_CONTENT_WIDTH_CM, BUSINESS_CONTENT_WIDTH_CM),
    ],
)
def test_profile_geometry_drives_fitting_through_resolved_values_only(
    content_width_cm: float, expected_width_cm: float
) -> None:
    """目标宽度超过有效宽度时，profile 几何差异体现在最终尺寸上。"""
    plan = _plan(2000, 800, target_width_cm=18.0, content_width_cm=content_width_cm)

    assert plan.width_limited is True
    assert plan.width_cm == pytest.approx(expected_width_cm)
    assert plan.aspect_ratio == pytest.approx(2.5)


def test_fit_figure_size_delegates_to_the_single_authority() -> None:
    """``fit_figure_size`` 与 ``plan_figure_fit`` 必须是同一决策（无重复逻辑）。"""
    fit = fit_figure_size(30, 70, TARGET_WIDTH_CM, CONTENT_WIDTH_CM, CONTENT_HEIGHT_CM, 8.0)
    plan = _plan(30, 70)

    assert fit.width_cm == pytest.approx(plan.width_cm)
    assert fit.height_cm == pytest.approx(plan.height_cm)
    assert fit.scaled == plan.scaled
    assert fit.below_min_width == plan.below_min_width


@pytest.mark.parametrize(
    "kwargs",
    [
        {"intrinsic_width_px": 0, "intrinsic_height_px": 10},
        {"intrinsic_width_px": 10, "intrinsic_height_px": -1},
        {"intrinsic_width_px": 10, "intrinsic_height_px": 10, "target_width_cm": 0.0},
        {"intrinsic_width_px": 10, "intrinsic_height_px": 10, "content_width_cm": 0.0},
        {"intrinsic_width_px": 10, "intrinsic_height_px": 10, "content_height_cm": -2.0},
    ],
)
def test_invalid_inputs_fail_loudly(kwargs: dict) -> None:
    """非法固有尺寸/边界必须显式失败（SPEC-INV-006：fail loudly）。"""
    base = {
        "intrinsic_width_px": 10,
        "intrinsic_height_px": 10,
        "target_width_cm": TARGET_WIDTH_CM,
        "content_width_cm": CONTENT_WIDTH_CM,
        "content_height_cm": CONTENT_HEIGHT_CM,
    }
    base.update(kwargs)
    with pytest.raises(FigureMeasurementError):
        plan_figure_fit(**base)
