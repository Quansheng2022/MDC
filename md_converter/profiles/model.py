"""Bounded presentation model for Professional Output Profiles (WP-POP-02).

A profile is *presentation configuration*, never document semantics.  The model
declares the frozen, bounded set of properties a profile may control
(``PROFESSIONAL_OUTPUT_PROFILES_ARCHITECTURE_BASELINE.md`` §3.5/§3.6) and
refuses, at construction time, any value that would violate a quality gate the
compiler enforces later:

* body text below the frozen 10pt readability minimum (``StaticQA``);
* table text below the frozen 8.5pt readability minimum (``StaticQA``);
* any text below the absolute 8pt floor (``RenderedQA``);
* a table style outside the built-in *Grid* family, which ``FinalArtifactQA``
  requires while ``style_tables`` is enabled;
* a page margin below the 0.5in readability minimum.

The model is Qt-free, renderer-free and compiler-free: it can be imported by
the GUI (for identifiers and display names) and by the compiler (for
resolution) without violating the layer boundaries frozen in WP-POP-01.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Tuple

__all__ = [
    "ACADEMIC",
    "BUSINESS_REPORT",
    "CLEAN_MINIMAL",
    "DEFAULT_PROFILE_ID",
    "MIN_BODY_SIZE_PT",
    "MIN_CODE_SIZE_PT",
    "MIN_MARGIN_CM",
    "MIN_TABLE_FONT_SIZE_PT",
    "MIN_TEXT_SIZE_PT",
    "PROFILE_ID_PATTERN",
    "PROFESSIONAL_REPORT",
    "TECHNICAL",
    "OutputProfile",
    "PageMargins",
    "PresentationSettings",
    "Typography",
]

# ============================================================
# Stable profile identifiers (frozen vocabulary, baseline §3.2/§3.3)
# ============================================================

PROFESSIONAL_REPORT = "professional_report"
BUSINESS_REPORT = "business_report"
ACADEMIC = "academic"
TECHNICAL = "technical"
CLEAN_MINIMAL = "clean_minimal"

#: The single product default (baseline §3.4).
DEFAULT_PROFILE_ID = PROFESSIONAL_REPORT

#: Stable identifier shape (baseline §3.2).
PROFILE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")

# ============================================================
# Frozen quality-gate floors a profile may not cross
# ============================================================

#: Absolute floor for any rendered text (``RenderedQA``).
MIN_TEXT_SIZE_PT = 8.0
#: StaticQA body-font minimum (frozen theme readability block).
MIN_BODY_SIZE_PT = 10.0
#: StaticQA table-font minimum (frozen theme readability block).
MIN_TABLE_FONT_SIZE_PT = 8.5
#: Code/ASCII floor (``RenderedQA`` absolute minimum).
MIN_CODE_SIZE_PT = 8.0
#: Readability minimum page margin (0.5in).
MIN_MARGIN_CM = 1.27
#: Upper sanity bound so a profile cannot remove the writing area entirely.
MAX_MARGIN_CM = 6.0


def _require_text(value: Any, *, field_name: str) -> str:
    """Return ``value`` as non-empty stripped text.

    Args:
        value: Candidate value.
        field_name: Field name used in the error message.

    Returns:
        str: The validated text.

    Raises:
        ValueError: ``value`` is not a non-empty string.
    """
    text = value.strip() if isinstance(value, str) else ""
    if not text:
        raise ValueError(f"{field_name} must be a non-empty string")
    return text


def _require_number(
    value: Any,
    *,
    field_name: str,
    minimum: float,
    maximum: float = float("inf"),
) -> float:
    """Return ``value`` as a number inside ``[minimum, maximum]``.

    Args:
        value: Candidate value.
        field_name: Field name used in the error message.
        minimum: Inclusive lower bound.
        maximum: Inclusive upper bound.

    Returns:
        float: The validated number.

    Raises:
        ValueError: ``value`` is not a number inside the bounds.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number")
    number = float(value)
    if number < minimum or number > maximum:
        raise ValueError(f"{field_name} must be between {minimum} and {maximum}, got {number}")
    return number


@dataclass(frozen=True)
class PageMargins:
    """Page margins a profile may control (centimetres).

    Attributes:
        top_cm: Top margin.
        bottom_cm: Bottom margin.
        left_cm: Left margin.
        right_cm: Right margin.
    """

    top_cm: float
    bottom_cm: float
    left_cm: float
    right_cm: float

    def __post_init__(self) -> None:
        """Validate every margin against the readability minimum."""
        for name in ("top_cm", "bottom_cm", "left_cm", "right_cm"):
            object.__setattr__(
                self,
                name,
                _require_number(
                    getattr(self, name),
                    field_name=f"page_margins.{name}",
                    minimum=MIN_MARGIN_CM,
                    maximum=MAX_MARGIN_CM,
                ),
            )

    def to_dict(self) -> Dict[str, float]:
        """Return the margins as a plain mapping."""
        return {
            "top": self.top_cm,
            "bottom": self.bottom_cm,
            "left": self.left_cm,
            "right": self.right_cm,
        }


@dataclass(frozen=True)
class Typography:
    """Typography and table presentation a profile may control.

    Attributes:
        body_font: Latin body font family (``ascii``/``hAnsi`` slots).
        body_font_complex: Complex-script body font family (``cs`` slot).
        body_east_asia_font: East Asian body font family.
        body_size_pt: Body font size.
        heading_font: Latin heading font family (``ascii``/``hAnsi`` slots).
        heading_font_complex: Complex-script heading font family (``cs`` slot).
        heading_east_asia_font: East Asian heading font family.
        heading_sizes_pt: Heading sizes for levels H1-H4 (H5/H6 follow H4).
        heading_space_before_pt: Space before every heading.
        heading_space_after_pt: Space after every heading.
        line_spacing: Body line spacing (multiple).
        paragraph_space_after_pt: Space after every body paragraph.
        code_font: Code font family.
        code_size_pt: Code font size.
        code_line_spacing: Code block line spacing (multiple).
        table_style: Built-in Word table style name (must contain ``Grid``).
        table_font_size_pt: Table text size.
    """

    body_font: str
    body_font_complex: str
    body_east_asia_font: str
    body_size_pt: float
    heading_font: str
    heading_font_complex: str
    heading_east_asia_font: str
    heading_sizes_pt: Tuple[float, float, float, float]
    heading_space_before_pt: float
    heading_space_after_pt: float
    line_spacing: float
    paragraph_space_after_pt: float
    code_font: str
    code_size_pt: float
    code_line_spacing: float
    table_style: str
    table_font_size_pt: float

    def __post_init__(self) -> None:
        """Validate fonts, sizes and the table style against the frozen gates."""
        for name in (
            "body_font",
            "body_font_complex",
            "body_east_asia_font",
            "heading_font",
            "heading_font_complex",
            "heading_east_asia_font",
            "code_font",
        ):
            object.__setattr__(self, name, _require_text(getattr(self, name), field_name=name))

        object.__setattr__(
            self,
            "body_size_pt",
            _require_number(
                self.body_size_pt,
                field_name="typography.body_size_pt",
                minimum=MIN_BODY_SIZE_PT,
                maximum=72.0,
            ),
        )
        object.__setattr__(
            self,
            "table_font_size_pt",
            _require_number(
                self.table_font_size_pt,
                field_name="typography.table_font_size_pt",
                minimum=MIN_TABLE_FONT_SIZE_PT,
                maximum=72.0,
            ),
        )
        object.__setattr__(
            self,
            "code_size_pt",
            _require_number(
                self.code_size_pt,
                field_name="typography.code_size_pt",
                minimum=MIN_CODE_SIZE_PT,
                maximum=72.0,
            ),
        )
        object.__setattr__(
            self,
            "line_spacing",
            _require_number(self.line_spacing, field_name="typography.line_spacing", minimum=0.5),
        )
        object.__setattr__(
            self,
            "code_line_spacing",
            _require_number(
                self.code_line_spacing, field_name="typography.code_line_spacing", minimum=0.5
            ),
        )
        for name in ("heading_space_before_pt", "heading_space_after_pt"):
            object.__setattr__(
                self,
                name,
                _require_number(getattr(self, name), field_name=f"typography.{name}", minimum=0.0),
            )
        object.__setattr__(
            self,
            "paragraph_space_after_pt",
            _require_number(
                self.paragraph_space_after_pt,
                field_name="typography.paragraph_space_after_pt",
                minimum=0.0,
            ),
        )

        sizes = tuple(self.heading_sizes_pt)
        if len(sizes) != 4:
            raise ValueError("typography.heading_sizes_pt must contain the H1-H4 sizes")
        validated = tuple(
            _require_number(
                size,
                field_name=f"typography.heading_sizes_pt[{index}]",
                minimum=MIN_BODY_SIZE_PT,
                maximum=72.0,
            )
            for index, size in enumerate(sizes)
        )
        object.__setattr__(self, "heading_sizes_pt", validated)

        table_style = _require_text(self.table_style, field_name="typography.table_style")
        if "Grid" not in table_style:
            # FinalArtifactQA._check_table_styling requires the effective table
            # style to belong to the built-in Grid family whenever table
            # styling is required (baseline §3.11).
            raise ValueError(
                "typography.table_style must name a built-in Grid table style, got "
                f"{table_style!r}"
            )
        object.__setattr__(self, "table_style", table_style)

    def heading_size(self, level: int) -> float:
        """Return the declared size for heading ``level`` (H5/H6 follow H4)."""
        index = min(max(int(level), 1), 4) - 1
        return float(self.heading_sizes_pt[index])

    def to_dict(self) -> Dict[str, Any]:
        """Return the typography as a plain mapping."""
        return {
            "body_font": self.body_font,
            "body_font_complex": self.body_font_complex,
            "body_east_asia_font": self.body_east_asia_font,
            "body_size_pt": self.body_size_pt,
            "heading_font": self.heading_font,
            "heading_font_complex": self.heading_font_complex,
            "heading_east_asia_font": self.heading_east_asia_font,
            "heading_sizes_pt": list(self.heading_sizes_pt),
            "heading_space_before_pt": self.heading_space_before_pt,
            "heading_space_after_pt": self.heading_space_after_pt,
            "line_spacing": self.line_spacing,
            "paragraph_space_after_pt": self.paragraph_space_after_pt,
            "code_font": self.code_font,
            "code_size_pt": self.code_size_pt,
            "code_line_spacing": self.code_line_spacing,
            "table_style": self.table_style,
            "table_font_size_pt": self.table_font_size_pt,
        }


@dataclass(frozen=True)
class PresentationSettings:
    """The complete bounded presentation configuration of one profile.

    Attributes:
        page_margins: Page margins.
        typography: Typography and table presentation.
    """

    page_margins: PageMargins
    typography: Typography

    def __post_init__(self) -> None:
        """Validate that the nested parts are typed model objects."""
        if not isinstance(self.page_margins, PageMargins):
            raise TypeError("presentation.page_margins must be a PageMargins instance")
        if not isinstance(self.typography, Typography):
            raise TypeError("presentation.typography must be a Typography instance")

    def to_dict(self) -> Dict[str, Any]:
        """Return the settings as a plain mapping."""
        return {
            "page_margins": self.page_margins.to_dict(),
            "typography": self.typography.to_dict(),
        }


@dataclass(frozen=True)
class OutputProfile:
    """One professional output profile.

    Attributes:
        id: Stable identifier (see :data:`PROFILE_ID_PATTERN`).
        display_name: User-facing name shown in the selector.
        description: One plain-language sentence describing the profile.
        presentation: Bounded presentation settings.

    Example:
        >>> from md_converter.profiles import resolve_profile
        >>> resolve_profile("academic").display_name
        'Academic'
    """

    id: str
    display_name: str
    description: str
    presentation: PresentationSettings

    def __post_init__(self) -> None:
        """Validate the stable identifier, wording and presentation object."""
        profile_id = self.id.strip() if isinstance(self.id, str) else ""
        if not PROFILE_ID_PATTERN.match(profile_id):
            raise ValueError(
                f"profile id must match {PROFILE_ID_PATTERN.pattern!r}, got {self.id!r}"
            )
        object.__setattr__(self, "id", profile_id)
        object.__setattr__(
            self, "display_name", _require_text(self.display_name, field_name="display_name")
        )
        object.__setattr__(
            self, "description", _require_text(self.description, field_name="description")
        )
        if not isinstance(self.presentation, PresentationSettings):
            raise TypeError("presentation must be a PresentationSettings instance")

    def to_dict(self) -> Dict[str, Any]:
        """Return the profile as a plain, JSON-serialisable mapping."""
        return {
            "id": self.id,
            "display_name": self.display_name,
            "description": self.description,
            "presentation": self.presentation.to_dict(),
        }
