"""Authoritative Professional Output Profile registry (WP-POP-02).

This module is the **single profile authority** frozen by
``PROFESSIONAL_OUTPUT_PROFILES_ARCHITECTURE_BASELINE.md`` §3.1/§3.3.  There is
exactly one definition of the five initial profiles; the GUI reads identifiers
and display names from here and the compiler resolves configuration against it.

Guarantees:

* stable identifiers and a deterministic declaration order;
* exactly one default profile;
* a safe, deterministic fallback for an unknown, blank or non-text identifier
  (the request never fails and never fabricates a profile);
* no duplicate identifiers and no renderer/GUI dependency.

Presentation values of the default profile are the frozen V1.5 baseline values,
so selecting it is presentation-identical to the accepted output.
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple

from .model import (
    ACADEMIC,
    BUSINESS_REPORT,
    CLEAN_MINIMAL,
    DEFAULT_PROFILE_ID,
    PROFESSIONAL_REPORT,
    TECHNICAL,
    OutputProfile,
    PageMargins,
    PresentationSettings,
    Typography,
)

__all__ = [
    "ALL_PROFILES",
    "DEFAULT_PROFILE",
    "PROFILE_REGISTRY",
    "ProfileRegistry",
    "all_profiles",
    "default_profile",
    "is_known_profile_id",
    "profile_choices",
    "profile_ids",
    "resolve_profile",
    "resolve_profile_id",
]


def _settings(
    *,
    margins_cm: Tuple[float, float, float, float],
    body_font: str,
    body_font_complex: str,
    body_font_east_asia: str,
    body_size_pt: float,
    heading_font: str,
    heading_font_complex: str,
    heading_font_east_asia: str,
    heading_sizes_pt: Tuple[float, float, float, float],
    heading_space_before_pt: float,
    heading_space_after_pt: float,
    line_spacing: float,
    paragraph_space_after_pt: float,
    code_font: str,
    code_size_pt: float,
    code_line_spacing: float,
    table_style: str,
    table_font_size_pt: float,
) -> PresentationSettings:
    """Build one validated presentation configuration (readability-safe)."""
    top, bottom, left, right = margins_cm
    return PresentationSettings(
        page_margins=PageMargins(
            top_cm=top,
            bottom_cm=bottom,
            left_cm=left,
            right_cm=right,
        ),
        typography=Typography(
            body_font=body_font,
            body_font_complex=body_font_complex,
            body_east_asia_font=body_font_east_asia,
            body_size_pt=body_size_pt,
            heading_font=heading_font,
            heading_font_complex=heading_font_complex,
            heading_east_asia_font=heading_font_east_asia,
            heading_sizes_pt=heading_sizes_pt,
            heading_space_before_pt=heading_space_before_pt,
            heading_space_after_pt=heading_space_after_pt,
            line_spacing=line_spacing,
            paragraph_space_after_pt=paragraph_space_after_pt,
            code_font=code_font,
            code_size_pt=code_size_pt,
            code_line_spacing=code_line_spacing,
            table_style=table_style,
            table_font_size_pt=table_font_size_pt,
        ),
    )


# ============================================================
# The five frozen profiles (declaration order == presentation order)
# ============================================================

_PROFESSIONAL_REPORT = OutputProfile(
    id=PROFESSIONAL_REPORT,
    display_name="Professional Report",
    description="Balanced typography for consulting and professional deliverables.",
    presentation=_settings(
        # Frozen V1.5 baseline values: 1in margins, 10.5pt body, Calibri/Arial.
        margins_cm=(2.54, 2.54, 2.54, 2.54),
        body_font="Calibri",
        body_font_complex="Arial",
        body_font_east_asia="DengXian",
        body_size_pt=10.5,
        heading_font="Arial",
        heading_font_complex="Arial",
        heading_font_east_asia="Microsoft YaHei",
        heading_sizes_pt=(20.0, 16.0, 14.0, 14.0),
        heading_space_before_pt=12.0,
        heading_space_after_pt=6.0,
        line_spacing=1.15,
        paragraph_space_after_pt=6.0,
        code_font="Consolas",
        code_size_pt=10.0,
        code_line_spacing=1.0,
        table_style="Table Grid",
        table_font_size_pt=9.5,
    ),
)

_BUSINESS_REPORT = OutputProfile(
    id=BUSINESS_REPORT,
    display_name="Business Report",
    description="Compact layout that uses the page efficiently for management reports.",
    presentation=_settings(
        margins_cm=(2.0, 2.0, 2.0, 2.0),
        body_font="Calibri",
        body_font_complex="Arial",
        body_font_east_asia="DengXian",
        body_size_pt=10.0,
        heading_font="Calibri",
        heading_font_complex="Arial",
        heading_font_east_asia="Microsoft YaHei",
        heading_sizes_pt=(16.0, 14.0, 12.5, 11.5),
        heading_space_before_pt=10.0,
        heading_space_after_pt=4.0,
        line_spacing=1.08,
        paragraph_space_after_pt=4.0,
        code_font="Consolas",
        code_size_pt=9.0,
        code_line_spacing=1.0,
        table_style="Light Grid",
        table_font_size_pt=9.0,
    ),
)

_ACADEMIC = OutputProfile(
    id=ACADEMIC,
    display_name="Academic",
    description="Formal serif typography for papers, research and coursework.",
    presentation=_settings(
        margins_cm=(2.54, 2.54, 3.0, 3.0),
        body_font="Times New Roman",
        body_font_complex="Times New Roman",
        body_font_east_asia="SimSun",
        body_size_pt=11.5,
        heading_font="Times New Roman",
        heading_font_complex="Times New Roman",
        heading_font_east_asia="SimSun",
        heading_sizes_pt=(16.0, 14.0, 12.0, 11.0),
        heading_space_before_pt=12.0,
        heading_space_after_pt=6.0,
        line_spacing=1.5,
        paragraph_space_after_pt=0.0,
        code_font="Courier New",
        code_size_pt=9.5,
        code_line_spacing=1.0,
        table_style="Table Grid",
        table_font_size_pt=9.0,
    ),
)

_TECHNICAL = OutputProfile(
    id=TECHNICAL,
    display_name="Technical",
    description="Readable layout for specifications, engineering and documentation.",
    presentation=_settings(
        margins_cm=(2.2, 2.2, 2.2, 2.2),
        body_font="Calibri",
        body_font_complex="Arial",
        body_font_east_asia="DengXian",
        body_size_pt=10.5,
        heading_font="Arial",
        heading_font_complex="Arial",
        heading_font_east_asia="Microsoft YaHei",
        heading_sizes_pt=(18.0, 15.0, 13.0, 11.5),
        heading_space_before_pt=14.0,
        heading_space_after_pt=6.0,
        line_spacing=1.2,
        paragraph_space_after_pt=6.0,
        code_font="Consolas",
        code_size_pt=9.5,
        code_line_spacing=1.0,
        table_style="Light Grid Accent 1",
        table_font_size_pt=9.0,
    ),
)

_CLEAN_MINIMAL = OutputProfile(
    id=CLEAN_MINIMAL,
    display_name="Clean / Minimal",
    description="Plain typography with light formatting and generous whitespace.",
    presentation=_settings(
        margins_cm=(2.54, 2.54, 2.54, 2.54),
        body_font="Calibri",
        body_font_complex="Arial",
        body_font_east_asia="DengXian",
        body_size_pt=10.5,
        heading_font="Calibri",
        heading_font_complex="Arial",
        heading_font_east_asia="Microsoft YaHei",
        heading_sizes_pt=(15.0, 13.0, 11.5, 10.5),
        heading_space_before_pt=10.0,
        heading_space_after_pt=6.0,
        line_spacing=1.25,
        paragraph_space_after_pt=8.0,
        code_font="Consolas",
        code_size_pt=9.5,
        code_line_spacing=1.0,
        table_style="Light Grid",
        table_font_size_pt=9.5,
    ),
)

#: The authoritative, ordered profile set (baseline §3.3).
ALL_PROFILES: Tuple[OutputProfile, ...] = (
    _PROFESSIONAL_REPORT,
    _BUSINESS_REPORT,
    _ACADEMIC,
    _TECHNICAL,
    _CLEAN_MINIMAL,
)


class ProfileRegistry:
    """Deterministic, read-only registry of output profiles.

    Args:
        profiles: The profiles to register, in presentation order.  The order
            is preserved verbatim, so lookup and listing are deterministic.
        default_id: Identifier returned when a lookup cannot be resolved.

    Raises:
        ValueError: ``profiles`` is empty, an identifier is duplicated, or
            ``default_id`` is not one of the registered identifiers.
    """

    def __init__(
        self,
        profiles: Sequence[OutputProfile],
        *,
        default_id: str = DEFAULT_PROFILE_ID,
    ) -> None:
        ordered: List[OutputProfile] = list(profiles)
        if not ordered:
            raise ValueError("a profile registry must declare at least one profile")
        by_id: Dict[str, OutputProfile] = {}
        for profile in ordered:
            if profile.id in by_id:
                raise ValueError(f"duplicate profile definition for id {profile.id!r}")
            by_id[profile.id] = profile
        if default_id not in by_id:
            raise ValueError(f"default profile {default_id!r} is not registered")
        self._profiles: Tuple[OutputProfile, ...] = tuple(ordered)
        self._by_id: Mapping[str, OutputProfile] = dict(by_id)
        self._default_id = default_id

    # ------------------------------------------------------------------
    # Read-only state
    # ------------------------------------------------------------------

    @property
    def profiles(self) -> Tuple[OutputProfile, ...]:
        """Return every profile in presentation order."""
        return self._profiles

    @property
    def ids(self) -> Tuple[str, ...]:
        """Return every stable identifier in presentation order."""
        return tuple(profile.id for profile in self._profiles)

    @property
    def default_id(self) -> str:
        """Return the identifier of the default profile."""
        return self._default_id

    @property
    def default(self) -> OutputProfile:
        """Return the default profile."""
        return self._by_id[self._default_id]

    def __len__(self) -> int:
        """Return the number of registered profiles."""
        return len(self._profiles)

    def __iter__(self) -> Iterator[OutputProfile]:
        """Iterate over the profiles in presentation order."""
        return iter(self._profiles)

    def __contains__(self, profile_id: object) -> bool:
        """Return whether ``profile_id`` names a registered profile."""
        return isinstance(profile_id, str) and profile_id.strip() in self._by_id

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, profile_id: Any) -> Optional[OutputProfile]:
        """Return the profile named by ``profile_id``, or ``None``.

        Args:
            profile_id: Candidate identifier.  Surrounding whitespace is
                ignored; anything that is not a registered identifier resolves
                to ``None`` (never to an exception).

        Returns:
            Optional[OutputProfile]: The matching profile, or ``None``.
        """
        if not isinstance(profile_id, str):
            return None
        return self._by_id.get(profile_id.strip())

    def resolve(self, profile_id: Any) -> OutputProfile:
        """Return the profile named by ``profile_id``, falling back safely.

        An unknown, deprecated, blank or non-text identifier resolves to the
        default profile, so a stale stored value or an unknown configuration
        value can never fail a conversion.

        Args:
            profile_id: Candidate identifier.

        Returns:
            OutputProfile: The resolved profile (the default when unknown).
        """
        return self.get(profile_id) or self.default

    def resolve_id(self, profile_id: Any) -> str:
        """Return the stable identifier ``profile_id`` resolves to."""
        return self.resolve(profile_id).id

    def choices(self) -> Tuple[Tuple[str, str], ...]:
        """Return ``(identifier, display name)`` pairs in presentation order."""
        return tuple((profile.id, profile.display_name) for profile in self._profiles)


#: The single authoritative registry instance used by the product.
PROFILE_REGISTRY = ProfileRegistry(ALL_PROFILES)

#: The default profile (convenience accessor).
DEFAULT_PROFILE = PROFILE_REGISTRY.default


def all_profiles() -> Tuple[OutputProfile, ...]:
    """Return every registered profile in presentation order."""
    return PROFILE_REGISTRY.profiles


def default_profile() -> OutputProfile:
    """Return the default profile."""
    return DEFAULT_PROFILE


def profile_ids() -> Tuple[str, ...]:
    """Return every stable profile identifier in presentation order."""
    return PROFILE_REGISTRY.ids


def profile_choices() -> Tuple[Tuple[str, str], ...]:
    """Return the selector content: ``(identifier, display name)`` pairs."""
    return PROFILE_REGISTRY.choices()


def is_known_profile_id(profile_id: Any) -> bool:
    """Return whether ``profile_id`` names a registered profile."""
    return PROFILE_REGISTRY.get(profile_id) is not None


def resolve_profile(profile_id: Any) -> OutputProfile:
    """Return the profile named by ``profile_id``, falling back to the default."""
    return PROFILE_REGISTRY.resolve(profile_id)


def resolve_profile_id(profile_id: Any) -> str:
    """Return the stable identifier ``profile_id`` resolves to."""
    return PROFILE_REGISTRY.resolve_id(profile_id)
