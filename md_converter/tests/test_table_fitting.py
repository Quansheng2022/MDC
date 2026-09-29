"""
Table Fitting 策略测试（Program D / WP-D02）。

覆盖:
    - 窄表不被不必要放大；
    - 常规表有效利用内容宽度；
    - 宽表（8+ 列）收缩到有效宽度且不低于最小列宽；
    - 单一长文本列按内容比例获得更多宽度；
    - 数字密集型列保持最小列宽下限；
    - 空/极短单元格不产生零宽列；
    - 同一输入重复计算结果一致（确定性）；
    - 可读性下限保护（squeezed 时字号不小于 8.5pt）；
    - profile 几何差异通过解析后的有效宽度生效（无 profile ID 分支）；
    - 非法输入显式失败（fail loudly）。
"""

from typing import List, Sequence

import pytest

from md_converter.renderer.layout.table_fitting import (
    DEFAULT_MIN_COLUMN_WIDTH_CM,
    TableFitError,
    column_signal_lengths,
    plan_table_fit,
)

#: 冻结基线 A4 + 1in 参考几何的有效内容宽度（PROFESSIONAL_REPORT / CLEAN_MINIMAL）。
BASELINE_CONTENT_WIDTH_CM = 15.92

#: Academic 左右各 3.0cm 页边距下的有效内容宽度（SPEC-FUNC-012 主题 + profile 覆盖）。
ACADEMIC_CONTENT_WIDTH_CM = 15.0


def _rows(header: Sequence[str], *body: Sequence[str]) -> List[List[str]]:
    """构造表格文本矩阵（表头 + 若干数据行）。"""
    return [list(header), *[list(row) for row in body]]


def test_column_signal_lengths_uses_longest_visible_cell() -> None:
    rows = _rows(["ID", "Description"], ["1", "short"], ["2", "a much longer value"])
    assert column_signal_lengths(rows) == (2, len("a much longer value"))


def test_narrow_table_is_not_expanded_to_full_width() -> None:
    """窄表保持自然宽度：Program D §11.1「窄表不被不必要地放大」。"""
    plan = plan_table_fit(
        _rows(["Key", "Value"], ["a", "b"], ["c", "d"]),
        content_width_cm=BASELINE_CONTENT_WIDTH_CM,
        base_font_size_pt=9.5,
    )

    assert plan.filled_content_width is False
    assert plan.total_width_cm < BASELINE_CONTENT_WIDTH_CM
    assert plan.total_width_cm == pytest.approx(2 * DEFAULT_MIN_COLUMN_WIDTH_CM)
    assert plan.squeezed is False
    assert plan.font_size_pt == pytest.approx(9.5)


def test_normal_table_uses_available_content_width() -> None:
    """内容量已接近有效宽度时按比例铺满，而不是留出大片空白。"""
    rows = _rows(
        ["Identifier", "Description", "Owner", "Status"],
        ["DOC-001", "Pipeline normalisation pass", "platform", "accepted"],
        ["DOC-002", "Renderer table fitting", "renderer", "accepted"],
    )
    plan = plan_table_fit(
        rows,
        content_width_cm=BASELINE_CONTENT_WIDTH_CM,
        base_font_size_pt=9.5,
    )

    assert plan.filled_content_width is True
    assert plan.total_width_cm == pytest.approx(BASELINE_CONTENT_WIDTH_CM)
    assert sum(plan.column_widths_cm) == pytest.approx(BASELINE_CONTENT_WIDTH_CM)
    assert min(plan.column_widths_cm) >= DEFAULT_MIN_COLUMN_WIDTH_CM


def test_wide_table_shrinks_to_content_width_keeping_floor() -> None:
    """8+ 列宽表：总宽落在有效内容宽度内，且每列不低于最小列宽。"""
    header = [f"Column {i}" for i in range(1, 9)]
    body = [f"value-{i}" for i in range(1, 9)]
    plan = plan_table_fit(
        _rows(header, body),
        content_width_cm=BASELINE_CONTENT_WIDTH_CM,
        base_font_size_pt=9.0,
    )

    assert plan.filled_content_width is True
    assert plan.total_width_cm == pytest.approx(BASELINE_CONTENT_WIDTH_CM)
    assert len(plan.column_widths_cm) == 8
    assert min(plan.column_widths_cm) >= DEFAULT_MIN_COLUMN_WIDTH_CM - 1e-9
    assert plan.squeezed is False


def test_dominant_long_text_column_receives_more_width() -> None:
    """内容感知的列权重要求：长文本列宽于短文本列，并保持比例关系。"""
    rows = _rows(
        ["ID", "Explanation"],
        ["1", "a" * 40],
        ["2", "b" * 38],
    )
    plan = plan_table_fit(
        rows,
        content_width_cm=BASELINE_CONTENT_WIDTH_CM,
        base_font_size_pt=9.5,
    )
    id_width, explanation_width = plan.column_widths_cm

    assert explanation_width > id_width
    assert id_width >= DEFAULT_MIN_COLUMN_WIDTH_CM
    # 比例保持：natural(ID)=1.2cm，natural(Explanation)=40×0.19=7.6cm
    assert explanation_width / id_width == pytest.approx(7.6 / 1.2, rel=1e-6)


def test_numeric_heavy_columns_keep_minimum_floor() -> None:
    """数字密集型表格：短内容仍保有可读列宽下限，不会被压成零宽。"""
    rows = _rows(
        ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"],
        ["12", "345", "6", "789", "10", "11"],
        ["1", "2", "3", "4", "5", "6"],
    )
    plan = plan_table_fit(
        rows,
        content_width_cm=BASELINE_CONTENT_WIDTH_CM,
        base_font_size_pt=9.5,
    )

    assert len(plan.column_widths_cm) == 6
    assert all(width >= DEFAULT_MIN_COLUMN_WIDTH_CM for width in plan.column_widths_cm)


def test_empty_and_ragged_cells_never_produce_zero_width_columns() -> None:
    """空/极短单元格与参差不齐的行：列宽仍不低于下限，且不抛异常。"""
    rows = [["", "Header"], ["", ""], ["only-one"]]
    plan = plan_table_fit(
        rows,
        content_width_cm=BASELINE_CONTENT_WIDTH_CM,
        base_font_size_pt=9.5,
    )

    assert len(plan.column_widths_cm) == 2
    assert all(width >= DEFAULT_MIN_COLUMN_WIDTH_CM for width in plan.column_widths_cm)


def test_repeated_planning_is_deterministic() -> None:
    """同一输入重复计算必须给出完全相同的决策（SPEC-INV-003）。"""
    rows = _rows(
        ["A", "B", "C"],
        ["alpha", "beta", "gamma"],
        ["delta", "epsilon", "zeta"],
    )

    first = plan_table_fit(rows, content_width_cm=13.0, base_font_size_pt=9.5)
    second = plan_table_fit(rows, content_width_cm=13.0, base_font_size_pt=9.5)

    assert first == second
    assert first.to_dict() == second.to_dict()


@pytest.mark.parametrize(
    ("base_font_pt", "expected_font_pt"),
    [(9.5, 9.0), (9.0, 8.5), (8.6, 8.5)],
)
def test_readability_floor_is_never_violated_when_squeezed(
    base_font_pt: float, expected_font_pt: float
) -> None:
    """达到最小列宽仍放不下时：标记 squeezed、保留内容，字号不低于 8.5pt。"""
    header = [f"C{i}" for i in range(14)]
    body = ["x" * 30 for _ in range(14)]
    plan = plan_table_fit(
        _rows(header, body),
        content_width_cm=ACADEMIC_CONTENT_WIDTH_CM,
        base_font_size_pt=base_font_pt,
    )

    assert plan.squeezed is True
    assert plan.total_width_cm == pytest.approx(14 * DEFAULT_MIN_COLUMN_WIDTH_CM)
    assert plan.total_width_cm > ACADEMIC_CONTENT_WIDTH_CM
    assert plan.font_size_pt == pytest.approx(expected_font_pt)
    assert plan.font_size_pt >= 8.5
    assert all(width >= DEFAULT_MIN_COLUMN_WIDTH_CM for width in plan.column_widths_cm)


def test_font_is_not_reduced_when_the_table_fits() -> None:
    """能放下时不做字号收缩：紧凑化只在必要时发生。"""
    plan = plan_table_fit(
        _rows(["A", "B"], ["1", "2"]),
        content_width_cm=BASELINE_CONTENT_WIDTH_CM,
        base_font_size_pt=9.0,
    )
    assert plan.font_size_pt == pytest.approx(9.0)
    assert plan.squeezed is False


def test_font_never_below_floor_even_for_low_theme_value() -> None:
    """主题字号低于下限（配置缺陷）时不产生低于下限的交付字号。"""
    plan = plan_table_fit(
        _rows(["A", "B"], ["1", "2"]),
        content_width_cm=BASELINE_CONTENT_WIDTH_CM,
        base_font_size_pt=8.0,
    )
    assert plan.font_size_pt == pytest.approx(8.5)


def test_profile_geometry_variation_through_resolved_width_only() -> None:
    """profile 差异只通过解析后的有效宽度生效（无 profile ID 分支）。"""
    rows = _rows(
        ["Identifier", "Description", "Owner"],
        ["DOC-001", "Renderer table fitting policy " + "detail " * 8, "renderer"],
    )
    academic = plan_table_fit(
        rows,
        content_width_cm=ACADEMIC_CONTENT_WIDTH_CM,
        base_font_size_pt=9.0,
    )
    baseline = plan_table_fit(
        rows,
        content_width_cm=BASELINE_CONTENT_WIDTH_CM,
        base_font_size_pt=9.5,
    )

    assert academic.column_widths_cm != baseline.column_widths_cm
    assert sum(academic.column_widths_cm) <= ACADEMIC_CONTENT_WIDTH_CM + 1e-9
    assert sum(baseline.column_widths_cm) <= BASELINE_CONTENT_WIDTH_CM + 1e-9


def test_hard_cap_prevents_single_column_from_owning_the_page() -> None:
    """单列信号字符上限：极端长文本不得让一列吃掉整页宽度。"""
    plan = plan_table_fit(
        _rows(["K", "V"], ["k", "v" * 5000]),
        content_width_cm=BASELINE_CONTENT_WIDTH_CM,
        base_font_size_pt=9.5,
    )
    assert plan.column_widths_cm[1] < BASELINE_CONTENT_WIDTH_CM
    assert plan.column_widths_cm[0] >= DEFAULT_MIN_COLUMN_WIDTH_CM


@pytest.mark.parametrize(
    "kwargs",
    [
        {"content_width_cm": 0.0, "base_font_size_pt": 9.5},
        {"content_width_cm": -1.0, "base_font_size_pt": 9.5},
        {"content_width_cm": 15.0, "base_font_size_pt": 0.0},
        {"content_width_cm": 15.0, "base_font_size_pt": 9.5, "min_column_width_cm": 0.0},
        {"content_width_cm": 15.0, "base_font_size_pt": 9.5, "char_width_cm": 0.0},
        {"content_width_cm": 15.0, "base_font_size_pt": 9.5, "readability_floor_pt": 0.0},
        {"content_width_cm": 15.0, "base_font_size_pt": 9.5, "narrow_fill_ratio": 0.0},
        {"content_width_cm": 15.0, "base_font_size_pt": 9.5, "narrow_fill_ratio": 1.5},
        {"content_width_cm": 15.0, "base_font_size_pt": 9.5, "signal_char_cap": 0},
    ],
)
def test_invalid_inputs_fail_loudly(kwargs: dict) -> None:
    """非法边界必须显式失败（SPEC-INV-006：fail loudly）。"""
    with pytest.raises(TableFitError):
        plan_table_fit(_rows(["A"], ["1"]), **kwargs)


def test_empty_table_fails_loudly() -> None:
    with pytest.raises(TableFitError):
        plan_table_fit([], content_width_cm=15.0, base_font_size_pt=9.5)
    with pytest.raises(TableFitError):
        plan_table_fit([[], []], content_width_cm=15.0, base_font_size_pt=9.5)
