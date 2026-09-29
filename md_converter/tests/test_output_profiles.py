"""Focused verification for the output-profile authority (Program C, WP-POP-02).

Covers the single profile authority, the frozen initial set, the safe fallback
for unknown identifiers, the bounded presentation model, the configuration
binding, and the one compiler integration point.  No Qt and no rendering is
required here; the presentation behaviour itself is verified by
``test_output_profile_rendering.py``.
"""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any, Dict, Set

import pytest

from md_converter.config import DEFAULT_CONFIG, CompilerConfig, resolve_config
from md_converter.profiles import (
    ALL_PROFILES,
    DEFAULT_PROFILE,
    DEFAULT_PROFILE_ID,
    PROFILE_REGISTRY,
    OutputProfile,
    PageMargins,
    PresentationSettings,
    ProfileRegistry,
    Typography,
    is_known_profile_id,
    profile_choices,
    profile_ids,
    resolve_profile,
    resolve_profile_id,
    theme_presentation_overrides,
)
from md_converter.renderer.themes.v15_theme import V15Theme

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILES_DIR = PROJECT_ROOT / "md_converter" / "profiles"

#: The frozen initial set and its presentation order (baseline 3.3).
EXPECTED_IDS = (
    "professional_report",
    "business_report",
    "academic",
    "technical",
    "clean_minimal",
)

#: Material a profile must never touch (baseline 3.6).
OUT_OF_SCOPE_OVERLAY_KEYS = (
    "theme",
    "document_structure",
    "readability",
    "pagination_policies",
    "section",
    "run_segmentation",
    "language_detection",
)


def _presentation_fingerprint(theme: V15Theme) -> Dict[str, Any]:
    """Return every profile-controllable presentation fact of ``theme``."""
    return {
        "margins": theme.page_margins_cm,
        "body_size": theme.body_size,
        "code_size": theme.code_size,
        "ascii_size": theme.ascii_size,
        "heading_sizes": [theme.heading_size(level) for level in range(1, 7)],
        "heading_before": [theme.heading_before(level) for level in range(1, 7)],
        "heading_after": [theme.heading_after(level) for level in range(1, 7)],
        "line_spacing": theme.line_spacing,
        "paragraph_space_before": theme.paragraph_space_before,
        "paragraph_space_after": theme.paragraph_space_after,
        "body_fonts": theme.font_mapping_for("body"),
        "heading_fonts": theme.font_mapping_for("heading"),
        "code_font": theme.code_font,
        "code_line_spacing": theme.code_line_spacing,
        "table_style": theme.table_style,
        "table_font_size": theme.table_font_size,
        "name": theme.name,
        "readability": theme.readability_minimums,
        "page_size": theme.page_size,
    }


def _imported_modules(path: Path) -> Set[str]:
    """Return the import targets of ``path`` (relative imports included)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                module = f"{'.' * node.level}{module}"
            if module:
                names.add(module)
                names.update(f"{module}.{alias.name}" for alias in node.names)
    return names


# ============================================================
# Initial profile set
# ============================================================


def test_initial_profile_set_is_frozen() -> None:
    """Product specification 3: exactly the five recommended profiles exist."""
    assert profile_ids() == EXPECTED_IDS
    assert len(ALL_PROFILES) == 5


def test_identifiers_are_unique_and_stable() -> None:
    """Baseline 3.2: lowercase snake_case identifiers, no duplicates."""
    ids = [profile.id for profile in ALL_PROFILES]

    assert len(set(ids)) == len(ids)
    assert all(identifier == identifier.strip() for identifier in ids)
    assert all(identifier.islower() for identifier in ids)


def test_display_names_are_unique_user_facing_wording() -> None:
    """The selector shows plain product names with no technical jargon."""
    names = [profile.display_name for profile in ALL_PROFILES]

    assert len(set(names)) == len(names)
    for profile in ALL_PROFILES:
        assert profile.display_name.strip() == profile.display_name
        assert profile.description.strip() == profile.description
        for jargon in ("--", "AST", "QA", "CompilerContext", "ConversionService"):
            assert jargon not in profile.display_name
            assert jargon not in profile.description


def test_choices_are_identifier_and_display_name_pairs() -> None:
    """The GUI selector content is derived from the single authority."""
    assert profile_choices() == tuple(
        (profile.id, profile.display_name) for profile in ALL_PROFILES
    )


def test_default_profile_is_the_recommended_one() -> None:
    """Product specification 7 / baseline 3.4: Professional Report is default."""
    assert DEFAULT_PROFILE_ID == "professional_report"
    assert DEFAULT_PROFILE.id == DEFAULT_PROFILE_ID
    assert resolve_profile(None).id == DEFAULT_PROFILE_ID


def test_registry_order_is_deterministic() -> None:
    """Lookup and listing must be deterministic (same input, same result)."""
    first = ProfileRegistry(ALL_PROFILES)
    second = ProfileRegistry(ALL_PROFILES)

    assert first.ids == second.ids == EXPECTED_IDS
    assert [profile.id for profile in first.profiles] == [profile.id for profile in second.profiles]
    assert len(first) == len(ALL_PROFILES)
    assert [profile.id for profile in first] == list(EXPECTED_IDS)


def test_registry_rejects_duplicate_definitions() -> None:
    """No duplicate profile definitions may exist anywhere."""
    with pytest.raises(ValueError, match="duplicate"):
        ProfileRegistry((ALL_PROFILES[0], ALL_PROFILES[0]))


def test_registry_rejects_empty_or_unknown_default() -> None:
    """A registry without a default cannot resolve requests deterministically."""
    with pytest.raises(ValueError, match="at least one profile"):
        ProfileRegistry(())
    with pytest.raises(ValueError, match="default profile"):
        ProfileRegistry(ALL_PROFILES, default_id="not_registered")


# ============================================================
# Safe fallback
# ============================================================


@pytest.mark.parametrize(
    "candidate",
    [None, "", "   ", "nope", "Professional Report", 42, 3.5, object(), ["academic"]],
)
def test_unknown_identifier_falls_back_safely(candidate: object) -> None:
    """Product specification 10: an unknown stored value never fails."""
    assert resolve_profile(candidate).id == DEFAULT_PROFILE_ID
    assert resolve_profile_id(candidate) == DEFAULT_PROFILE_ID


def test_lookup_ignores_surrounding_whitespace() -> None:
    """A padded stored value still resolves deterministically."""
    assert resolve_profile("  academic  ").id == "academic"
    assert is_known_profile_id("  academic  ") is True


@pytest.mark.parametrize("candidate", [None, "", "  ", "nope", 42])
def test_unknown_identifier_is_not_known(candidate: object) -> None:
    """The compiler uses this predicate to report an unresolved request."""
    assert is_known_profile_id(candidate) is False


def test_every_identifier_is_known_and_resolvable() -> None:
    """Every declared profile resolves to itself."""
    for profile in ALL_PROFILES:
        assert is_known_profile_id(profile.id) is True
        assert resolve_profile(profile.id) is profile
        assert PROFILE_REGISTRY.get(profile.id) is profile


# ============================================================
# Bounded presentation model
# ============================================================


def test_profile_settings_respect_every_quality_gate() -> None:
    """Baseline 3.11: no profile may cross a frozen readability gate."""
    for profile in ALL_PROFILES:
        typography = profile.presentation.typography
        margins = profile.presentation.page_margins

        assert typography.body_size_pt >= 10.0
        assert typography.table_font_size_pt >= 8.5
        assert typography.code_size_pt >= 8.0
        assert min(typography.heading_sizes_pt) >= 10.0
        assert min(margins.to_dict().values()) >= 1.27
        assert "Grid" in typography.table_style
        assert typography.line_spacing > 0
        assert typography.code_line_spacing > 0


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("body_size_pt", 9.5),
        ("table_font_size_pt", 8.0),
        ("code_size_pt", 7.0),
    ],
)
def test_typography_rejects_sizes_below_the_frozen_floors(field: str, value: float) -> None:
    """A profile cannot silently produce unreadable output."""
    payload = resolve_profile("business_report").presentation.typography.to_dict()
    payload[field] = value
    payload["heading_sizes_pt"] = tuple(payload["heading_sizes_pt"])

    with pytest.raises(ValueError, match=field):
        Typography(**payload)


def test_typography_rejects_a_non_grid_table_style() -> None:
    """FinalArtifactQA requires a Grid-family table style (baseline 3.11)."""
    payload = resolve_profile("business_report").presentation.typography.to_dict()
    payload["heading_sizes_pt"] = tuple(payload["heading_sizes_pt"])
    payload["table_style"] = "Light Shading"

    with pytest.raises(ValueError, match="Grid"):
        Typography(**payload)


def test_page_margins_reject_a_margin_below_the_readability_minimum() -> None:
    """The writing area may not be squeezed below the 0.5in floor."""
    with pytest.raises(ValueError, match="page_margins.left_cm"):
        PageMargins(top_cm=2.54, bottom_cm=2.54, left_cm=1.0, right_cm=2.54)


def test_profile_rejects_a_malformed_identifier_or_blank_wording() -> None:
    """Identifiers and wording are part of the frozen vocabulary."""
    presentation = resolve_profile("business_report").presentation

    with pytest.raises(ValueError, match="profile id"):
        OutputProfile(
            id="Business Report",
            display_name="Business Report",
            description="Compact layout.",
            presentation=presentation,
        )
    with pytest.raises(ValueError, match="display_name"):
        OutputProfile(
            id="business_report_2",
            display_name="   ",
            description="Compact layout.",
            presentation=presentation,
        )
    with pytest.raises(ValueError, match="description"):
        OutputProfile(
            id="business_report_2",
            display_name="Business",
            description="",
            presentation=presentation,
        )


def test_presentation_settings_reject_untyped_parts() -> None:
    """The nested parts must be model objects, not ad-hoc mappings."""
    with pytest.raises(TypeError, match="page_margins"):
        PresentationSettings(
            page_margins={"top": 2.54},  # type: ignore[arg-type]
            typography=ALL_PROFILES[0].presentation.typography,
        )


def test_profiles_are_immutable() -> None:
    """Profiles are read-only configuration (no accidental mutation)."""
    profile = ALL_PROFILES[0]

    with pytest.raises(FrozenInstanceError):
        profile.id = "renamed"  # type: ignore[misc]


# ============================================================
# Theme overlay
# ============================================================


def test_overlay_controls_only_bounded_properties() -> None:
    """Baseline 3.5/3.6: the overlay touches presentation keys only."""
    overlay = theme_presentation_overrides(resolve_profile("technical"))

    assert set(overlay) == {"page", "font_mapping", "typography", "paragraph", "code", "table"}
    for key in OUT_OF_SCOPE_OVERLAY_KEYS:
        assert key not in overlay
    assert "ascii" not in overlay["typography"]
    assert set(overlay["font_mapping"]) == {"ascii", "hAnsi", "eastAsia", "cs"}
    assert set(overlay["typography"]["heading"]) == {"H1", "H2", "H3", "H4"}


def test_overlay_is_rebuilt_for_every_call() -> None:
    """The overlay is fresh data; a caller cannot corrupt the authority."""
    profile = resolve_profile("academic")

    first = theme_presentation_overrides(profile)
    first["table"]["style"] = "MUTATED"
    first["page"]["margins"]["top"] = "0cm"
    second = theme_presentation_overrides(profile)

    assert second["table"]["style"] == "Table Grid"
    assert second["page"]["margins"]["top"] != "0cm"


def test_default_profile_overlay_matches_the_frozen_baseline() -> None:
    """Product specification 7: the default profile restyles nothing."""
    baseline = V15Theme.load_default()
    applied = baseline.with_presentation_overrides(
        theme_presentation_overrides(resolve_profile(DEFAULT_PROFILE_ID))
    )

    assert _presentation_fingerprint(applied) == _presentation_fingerprint(baseline)


def test_every_non_default_profile_changes_the_presentation() -> None:
    """The initial set is meaningful: each profile differs from the default."""
    baseline = V15Theme.load_default()
    reference = _presentation_fingerprint(baseline)

    for profile in ALL_PROFILES:
        if profile.id == DEFAULT_PROFILE_ID:
            continue
        applied = baseline.with_presentation_overrides(theme_presentation_overrides(profile))
        differences = [
            key
            for key, value in _presentation_fingerprint(applied).items()
            if value != reference[key]
        ]
        assert len(differences) >= 2, (profile.id, differences)


def test_theme_overrides_are_reported_through_the_theme_accessors() -> None:
    """Declared profile values are what the renderer will actually read."""
    baseline = V15Theme.load_default()

    for profile in ALL_PROFILES:
        theme = baseline.with_presentation_overrides(theme_presentation_overrides(profile))
        typography = profile.presentation.typography
        margins = profile.presentation.page_margins

        assert theme.body_size == pytest.approx(typography.body_size_pt)
        assert theme.code_size == pytest.approx(typography.code_size_pt)
        assert theme.table_font_size == pytest.approx(typography.table_font_size_pt)
        assert theme.table_style == typography.table_style
        assert theme.line_spacing == pytest.approx(typography.line_spacing)
        assert theme.paragraph_space_after == pytest.approx(typography.paragraph_space_after_pt)
        assert theme.heading_size(1) == pytest.approx(typography.heading_size(1))
        assert theme.heading_size(4) == pytest.approx(typography.heading_size(4))
        assert theme.font_mapping_for("body")["ascii"] == typography.body_font
        assert theme.font_mapping_for("body")["eastAsia"] == typography.body_east_asia_font
        assert theme.font_mapping_for("heading")["ascii"] == typography.heading_font
        assert theme.page_margins_cm["left"] == pytest.approx(margins.left_cm)
        assert theme.page_margins_cm["top"] == pytest.approx(margins.top_cm)


def test_theme_without_overrides_returns_itself_and_is_never_mutated() -> None:
    """An empty overlay is a true no-op, and merging never touches the source."""
    baseline = V15Theme.load_default()
    before = baseline.to_dict()

    assert baseline.with_presentation_overrides(None) is baseline
    assert baseline.with_presentation_overrides({}) is baseline

    baseline.with_presentation_overrides(theme_presentation_overrides(resolve_profile("academic")))

    assert baseline.to_dict() == before


def test_overlay_targets_existing_structure_only() -> None:
    """Every overlaid key path already exists, so nothing is invented."""
    baseline = V15Theme.load_default().to_dict()

    def assert_paths(target: Any, overlay: Any, path: str = "") -> None:
        assert isinstance(target, dict) and isinstance(overlay, dict), path
        for key, value in overlay.items():
            assert key in target, f"{path}.{key}" if path else key
            if isinstance(value, dict):
                assert_paths(target[key], value, f"{path}.{key}" if path else key)

    overlay = theme_presentation_overrides(resolve_profile("business_report"))
    assert_paths(baseline, overlay)


# ============================================================
# Configuration binding
# ============================================================


def test_configuration_default_comes_from_the_registry() -> None:
    """One default definition: the registry, surfaced through the config."""
    assert DEFAULT_CONFIG["output_profile"] == DEFAULT_PROFILE_ID
    assert CompilerConfig.from_dict({}).output_profile == DEFAULT_PROFILE_ID
    assert CompilerConfig.from_dict({}).to_dict()["output_profile"] == DEFAULT_PROFILE_ID
    assert resolve_config({})["output_profile"] == DEFAULT_PROFILE_ID


def test_configuration_round_trips_a_selected_profile() -> None:
    """A selected identifier survives configuration resolution untouched."""
    assert resolve_config({"output_profile": "academic"})["output_profile"] == "academic"
    assert CompilerConfig.from_dict({"output_profile": "technical"}).output_profile == "technical"


def test_configuration_keeps_an_unknown_identifier_for_the_registry() -> None:
    """Unknown identifiers are a resolution concern, not a configuration error."""
    assert resolve_config({"output_profile": "retired-profile"})["output_profile"] == (
        "retired-profile"
    )


@pytest.mark.parametrize("value", [12, None, "", "   ", ["academic"]])
def test_configuration_rejects_a_non_text_profile(value: object) -> None:
    """Structural validation still fails loudly for a malformed value."""
    with pytest.raises(ValueError, match="output_profile"):
        resolve_config({"output_profile": value})


# ============================================================
# Compiler integration point
# ============================================================


def test_compiler_applies_the_selected_profile_to_the_theme() -> None:
    """The composition root applies the overlay; the renderer stays unchanged."""
    from md_converter.compiler import CompilerContext

    context = CompilerContext.create({"output_profile": "academic", "word_com": False})

    assert context.render_ctx.theme.body_size == pytest.approx(11.5)
    assert context.render_ctx.theme.page_margins_cm["left"] == pytest.approx(3.0)
    assert context.render_ctx.theme.font_mapping_for("body")["ascii"] == "Times New Roman"
    assert [d.code for d in context.diag.diagnostics] == []


def test_compiler_default_profile_matches_the_frozen_theme() -> None:
    """The default selection is presentation-identical to the accepted theme."""
    from md_converter.compiler import CompilerContext

    baseline = V15Theme.load_default()
    context = CompilerContext.create({"word_com": False})

    assert _presentation_fingerprint(context.render_ctx.theme) == _presentation_fingerprint(
        baseline
    )


def test_compiler_default_profile_leaves_a_supplied_theme_untouched() -> None:
    """The default profile is a true no-op, even for a caller-supplied theme.

    Regression guard: an explicit theme (for example one a caller customised, or
    the frozen-theme-with-below-minimum-font case used by the quality-gate
    tests) must never be rewritten by introducing profile support.
    """
    from md_converter.compiler import CompilerContext

    theme = V15Theme.load_default()
    theme.data["typography"]["body"]["size"] = "8pt"
    before = theme.to_dict()

    context = CompilerContext.create({"theme": theme, "word_com": False})

    assert context.render_ctx.theme is theme
    assert context.render_ctx.theme.to_dict() == before
    assert context.render_ctx.theme.body_size == pytest.approx(8.0)


def test_compiler_applies_a_non_default_profile_to_a_supplied_theme() -> None:
    """A requested divergence is honoured for a caller-supplied V1.5 theme."""
    from md_converter.compiler import CompilerContext

    theme = V15Theme.load_default()
    context = CompilerContext.create(
        {"theme": theme, "output_profile": "business_report", "word_com": False}
    )

    assert context.render_ctx.theme is not theme
    assert context.render_ctx.theme.body_size == pytest.approx(10.0)
    assert theme.body_size == pytest.approx(10.5)


def test_compiler_reports_an_unknown_profile_and_still_compiles() -> None:
    """An unresolved request is diagnosed, never silently ignored."""
    from md_converter.compiler import CompilerContext

    baseline = V15Theme.load_default()
    context = CompilerContext.create({"output_profile": "nope", "word_com": False})
    codes = [diagnostic.code for diagnostic in context.diag.diagnostics]

    assert "PROFILE001" in codes
    assert _presentation_fingerprint(context.render_ctx.theme) == _presentation_fingerprint(
        baseline
    )


def test_compiler_reports_a_profile_it_cannot_apply() -> None:
    """A legacy theme that accepts no overlay is reported, not silently skipped."""
    from md_converter.compiler import CompilerContext

    context = CompilerContext.create(
        {"theme": "github", "output_profile": "academic", "word_com": False}
    )

    assert "PROFILE002" in [diagnostic.code for diagnostic in context.diag.diagnostics]


def test_legacy_theme_with_the_default_profile_is_not_reported() -> None:
    """The default profile adds no diagnostic for a legacy theme."""
    from md_converter.compiler import CompilerContext

    context = CompilerContext.create({"theme": "github", "word_com": False})
    codes = [diagnostic.code for diagnostic in context.diag.diagnostics]

    assert "PROFILE001" not in codes
    assert "PROFILE002" not in codes


# ============================================================
# Layer boundary
# ============================================================


def test_profile_package_has_no_renderer_or_gui_dependency() -> None:
    """Baseline 3.1: the authority is importable from both boundaries."""
    modules = sorted(PROFILES_DIR.glob("*.py"))

    assert modules
    for module in modules:
        for name in _imported_modules(module):
            assert not name.startswith("PySide6"), (module.name, name)
            assert not name.startswith("md_converter.renderer"), (module.name, name)
            assert not name.startswith("md_converter.compiler"), (module.name, name)
            assert not name.startswith("md_converter.gui"), (module.name, name)
            assert not name.startswith("md_converter.application"), (module.name, name)
