"""Tests for heading font-size configuration."""

import pytest

from md_converter.ast.nodes import Document, Heading, Text
from md_converter.renderer.render_context import RenderContext
from md_converter.renderer.themes.default import DefaultTheme
from md_converter.renderer.word_renderer import WordRenderer
from md_converter.renderer.word_writer import WordWriter


def test_default_theme_uses_requested_heading_sizes() -> None:
    """The default theme assigns the requested sizes to every Markdown heading."""
    theme = DefaultTheme()

    assert [theme.get_heading_size(level) for level in range(1, 7)] == [20, 16, 14, 14, 14, 14]


def test_renderer_applies_resolved_heading_sizes_to_docx_styles() -> None:
    """Rendered DOCX heading styles retain the default theme's requested sizes."""
    writer = WordWriter.create()
    renderer = WordRenderer(RenderContext.create(), writer)
    document = Document(
        children=[Heading(level=level, content=[Text(f"Heading {level}")]) for level in range(1, 7)]
    )

    doc = renderer.render(document)

    assert [doc.styles[f"Heading {level}"].font.size.pt for level in range(1, 7)] == pytest.approx(
        [20, 16, 14, 14, 14, 14]
    )
