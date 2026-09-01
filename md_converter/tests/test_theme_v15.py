"""Tests for the frozen QS-Word-Default-V1.5 theme configuration."""

import pytest
from docx.shared import Pt

from md_converter.renderer.themes.v15_theme import V15Theme, parse_length


def test_theme_identity() -> None:
    """The frozen theme exposes its identity metadata."""
    theme = V15Theme.load_default()

    assert theme.name == "QS-Word-Default-V1.5"
    assert theme.version == "1.5"
    assert theme.status == "frozen"


def test_theme_page_configuration() -> None:
    """A4 page with 1in margins (frozen YAML)."""
    theme = V15Theme.load_default()

    assert theme.page_size == "A4"
    assert theme.page_margins_cm == pytest.approx(
        {"top": 2.54, "bottom": 2.54, "left": 2.54, "right": 2.54}
    )


def test_theme_font_mapping() -> None:
    """CJK and Latin fonts map to separate Word font slots."""
    theme = V15Theme.load_default()

    body = theme.font_mapping_for("body")
    heading = theme.font_mapping_for("heading")

    assert body["ascii"] == "Calibri"
    assert body["eastAsia"] == "DengXian"
    assert body["hAnsi"] == "Calibri"
    assert body["cs"] == "Arial"

    assert heading["ascii"] == "Arial"
    assert heading["eastAsia"] == "Microsoft YaHei"


def test_theme_typography() -> None:
    """Typography follows the frozen spec."""
    theme = V15Theme.load_default()

    assert theme.body_size == pytest.approx(10.5)
    assert theme.table_font_size == pytest.approx(9.5)
    assert theme.code_size == pytest.approx(10)
    assert theme.ascii_size == pytest.approx(8.5)

    assert [theme.heading_size(level) for level in range(1, 7)] == pytest.approx(
        [20, 16, 14, 14, 14, 14]
    )
    assert theme.heading_bold(1) is True
    assert theme.heading_italic(4) is True
    assert theme.heading_before(1) == pytest.approx(12)
    assert theme.heading_after(1) == pytest.approx(6)


def test_theme_paragraph_and_pagination() -> None:
    """Paragraph spacing and pagination policies follow the frozen spec."""
    theme = V15Theme.load_default()

    assert theme.line_spacing == pytest.approx(1.15)
    assert theme.paragraph_space_after == pytest.approx(6)

    heading = theme.pagination_policy("heading")
    assert heading["keep_with_next"] is True
    assert heading["keep_together"] is True

    table = theme.pagination_policy("table")
    assert table["split_rows_across_pages"] is True
    assert table["repeat_header"] is True

    ascii_policy = theme.pagination_policy("ascii")
    assert ascii_policy["keep_together"] is True
    assert ascii_policy["no_wrap"] is True


def test_theme_readability_protection() -> None:
    """Readability minimums enforce the no-shrink rule."""
    theme = V15Theme.load_default()

    minimums = theme.readability_minimums
    assert minimums["body_font"] == pytest.approx(10.0)
    assert minimums["table_font"] == pytest.approx(8.5)
    assert minimums["ascii_font"] == pytest.approx(8.0)
    assert minimums["code_font"] == pytest.approx(8.0)
    assert minimums["margin"] == pytest.approx(36.0)  # 0.5in


def test_parse_length() -> None:
    """Dimension strings parse into docx Length objects."""
    assert parse_length("10.5pt") == Pt(10.5)
    assert float(parse_length("1in").cm) == pytest.approx(2.54)
    assert float(parse_length("1cm").cm) == pytest.approx(1.0)
    assert float(parse_length(12).pt) == pytest.approx(12.0)


def test_theme_serialization() -> None:
    """to_dict returns a deep copy of the frozen YAML data."""
    theme = V15Theme.load_default()
    data = theme.to_dict()

    assert data["theme"]["name"] == "QS-Word-Default-V1.5"
    assert data["font_mapping"]["eastAsia"]["body"] == "DengXian"
    data["theme"]["name"] = "mutated"
    assert theme.name == "QS-Word-Default-V1.5"
