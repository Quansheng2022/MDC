"""Professional Output Profiles - bounded presentation configuration.

The package is the **single profile authority** frozen by
``Doc/V2/Implementation/Professional_Output_Profiles/PROFESSIONAL_OUTPUT_PROFILES_ARCHITECTURE_BASELINE.md``:

    GUI selector (identifiers + display names)
                ↓
    profiles.registry  (stable ids, default, safe fallback)
                ↓
    profiles.theme_overrides  (bounded data mapping)
                ↓
    existing rendering path (theme -> StyleResolver -> WordRenderer)

It imports nothing from the parser, pipeline, renderer, compiler, application
or GUI packages, so it is safe for the GUI layer to import and cannot create a
dependency cycle.

Example:
    >>> from md_converter.profiles import profile_choices, resolve_profile
    >>> [identifier for identifier, _ in profile_choices()]
    ['professional_report', 'business_report', 'academic', 'technical', 'clean_minimal']
    >>> resolve_profile("unknown-id").id
    'professional_report'
"""

from __future__ import annotations

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
from .registry import (
    ALL_PROFILES,
    DEFAULT_PROFILE,
    PROFILE_REGISTRY,
    ProfileRegistry,
    all_profiles,
    default_profile,
    is_known_profile_id,
    profile_choices,
    profile_ids,
    resolve_profile,
    resolve_profile_id,
)
from .theme_overrides import theme_presentation_overrides

__all__ = [
    "ACADEMIC",
    "ALL_PROFILES",
    "BUSINESS_REPORT",
    "CLEAN_MINIMAL",
    "DEFAULT_PROFILE",
    "DEFAULT_PROFILE_ID",
    "PROFESSIONAL_REPORT",
    "PROFILE_REGISTRY",
    "TECHNICAL",
    "OutputProfile",
    "PageMargins",
    "PresentationSettings",
    "ProfileRegistry",
    "Typography",
    "all_profiles",
    "default_profile",
    "is_known_profile_id",
    "profile_choices",
    "profile_ids",
    "resolve_profile",
    "resolve_profile_id",
    "theme_presentation_overrides",
]
