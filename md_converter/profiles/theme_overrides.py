"""Bounded profile -> V1.5 theme overlay mapping (WP-POP-02).

One place, and only one place, knows how a profile's bounded presentation
settings map onto the frozen V1.5 theme structure (baseline §3.5/§3.7).  The
module produces **data only**: it imports no renderer, no compiler and no GUI
module, so the GUI can keep importing the profile package without violating the
GUI/core boundary.

The overlay is a nested mapping that mirrors the frozen YAML shape and is
merged by :meth:`md_converter.renderer.themes.v15_theme.V15Theme.with_presentation_overrides`.
Keys a profile does not control are simply absent and stay at their frozen
value (for example the paragraph block's ``before`` spacing, the ``ascii``
typography block, pagination policies and the readability minimums).
"""

from __future__ import annotations

from typing import Any, Dict

from .model import OutputProfile

__all__ = ["theme_presentation_overrides"]


def _pt(value: float) -> str:
    """Format a point value the way the frozen theme spells lengths."""
    return f"{value:g}pt"


def _cm(value: float) -> str:
    """Format a centimetre value the way the frozen theme spells lengths."""
    return f"{value:g}cm"


def _font_overlay(typography: Any, kind: str) -> Dict[str, str]:
    """Return the four-slot Word font mapping for ``kind`` (``body``/``heading``)."""
    if kind == "body":
        return {
            "ascii": typography.body_font,
            "hAnsi": typography.body_font,
            "eastAsia": typography.body_east_asia_font,
            "cs": typography.body_font_complex,
        }
    return {
        "ascii": typography.heading_font,
        "hAnsi": typography.heading_font,
        "eastAsia": typography.heading_east_asia_font,
        "cs": typography.heading_font_complex,
    }


def _heading_overlay(typography: Any) -> Dict[str, Dict[str, str]]:
    """Return the H1-H4 size/spacing overlay."""
    before = _pt(typography.heading_space_before_pt)
    after = _pt(typography.heading_space_after_pt)
    overlay: Dict[str, Dict[str, str]] = {}
    for index in range(4):
        overlay[f"H{index + 1}"] = {
            "size": _pt(typography.heading_sizes_pt[index]),
            "before": before,
            "after": after,
        }
    return overlay


def theme_presentation_overrides(profile: OutputProfile) -> Dict[str, Any]:
    """Return the bounded V1.5 theme overlay for ``profile``.

    Args:
        profile: The resolved profile.

    Returns:
        Dict[str, Any]: A nested mapping in the frozen theme's own shape, ready
        for :meth:`V15Theme.with_presentation_overrides`.  The mapping is a new
        object on every call and never aliases model state.

    The default profile's overlay reproduces the frozen baseline values, so
    applying it leaves the theme presentation-identical (the compiler applies
    one uniform code path for every profile).
    """
    settings = profile.presentation
    typography = settings.typography
    margins = settings.page_margins

    body_fonts = _font_overlay(typography, "body")
    heading_fonts = _font_overlay(typography, "heading")
    font_mapping: Dict[str, Dict[str, str]] = {
        slot: {"body": body_fonts[slot], "heading": heading_fonts[slot]}
        for slot in ("ascii", "hAnsi", "eastAsia", "cs")
    }

    return {
        "page": {
            "margins": {
                "top": _cm(margins.top_cm),
                "bottom": _cm(margins.bottom_cm),
                "left": _cm(margins.left_cm),
                "right": _cm(margins.right_cm),
            }
        },
        "font_mapping": font_mapping,
        "typography": {
            "body": {"size": _pt(typography.body_size_pt)},
            "heading": _heading_overlay(typography),
            "code": {"font": typography.code_font, "size": _pt(typography.code_size_pt)},
        },
        "paragraph": {
            "line_spacing": {"type": "multiple", "value": typography.line_spacing},
            "spacing": {"after": _pt(typography.paragraph_space_after_pt)},
        },
        "code": {"line_spacing": typography.code_line_spacing},
        "table": {
            "style": typography.table_style,
            "font_size": _pt(typography.table_font_size_pt),
        },
    }
