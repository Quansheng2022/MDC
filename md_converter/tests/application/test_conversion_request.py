"""Focused tests for the application conversion request (WP-P12-03-01).

These tests cover only the request model's own responsibilities.  They do not
exercise conversion behaviour.
"""

from __future__ import annotations

import dataclasses
import subprocess
import sys
from pathlib import Path

import pytest

from md_converter.application import ConversionRequest

PROJECT_ROOT = Path(__file__).resolve().parents[3]

# ============================================================
# Construction
# ============================================================


def test_source_path_accepts_string(tmp_path: Path) -> None:
    """A string source path is normalised to pathlib.Path."""
    request = ConversionRequest(str(tmp_path / "guide.md"))

    assert request.source_path == tmp_path / "guide.md"
    assert isinstance(request.source_path, Path)


def test_source_path_accepts_path(tmp_path: Path) -> None:
    """A Path source path is preserved."""
    source = tmp_path / "guide.md"

    assert ConversionRequest(source).source_path == source


def test_optional_fields_default_to_none(tmp_path: Path) -> None:
    """Output path and override mappings are optional."""
    request = ConversionRequest(tmp_path / "guide.md")

    assert request.output_path is None
    assert request.config_overrides is None
    assert request.metadata_overrides is None


def test_explicit_output_path(tmp_path: Path) -> None:
    """An explicit output path is kept verbatim (no invented extension)."""
    request = ConversionRequest(tmp_path / "guide.md", tmp_path / "build" / "result.docx")

    assert request.output_path == tmp_path / "build" / "result.docx"


def test_config_overrides_supplied_and_copied(tmp_path: Path) -> None:
    """Config overrides are stored as an independent copy."""
    overrides = {"output_dir": "custom"}
    request = ConversionRequest(tmp_path / "guide.md", config_overrides=overrides)

    overrides["output_dir"] = "mutated"

    assert request.config_overrides == {"output_dir": "custom"}


def test_metadata_overrides_supplied_and_copied(tmp_path: Path) -> None:
    """Metadata overrides are stored as an independent copy."""
    overrides = {"title": "Override"}
    request = ConversionRequest(tmp_path / "guide.md", metadata_overrides=overrides)

    overrides["title"] = "mutated"

    assert request.metadata_overrides == {"title": "Override"}


# ============================================================
# Structural validation (model-owned invariants)
# ============================================================


def test_empty_source_path_rejected() -> None:
    """A blank source path is a structural error."""
    with pytest.raises(ValueError, match="source_path"):
        ConversionRequest("   ")


def test_non_path_source_rejected() -> None:
    """A non-path source raises TypeError, not a conversion failure."""
    with pytest.raises(TypeError, match="source_path"):
        ConversionRequest(123)  # type: ignore[arg-type]


def test_empty_output_path_rejected(tmp_path: Path) -> None:
    """A blank output path is rejected when supplied."""
    with pytest.raises(ValueError, match="output_path"):
        ConversionRequest(tmp_path / "guide.md", "")


def test_non_path_output_rejected(tmp_path: Path) -> None:
    """A non-path output value raises TypeError."""
    with pytest.raises(TypeError, match="output_path"):
        ConversionRequest(tmp_path / "guide.md", 42)  # type: ignore[arg-type]


def test_non_mapping_config_overrides_rejected(tmp_path: Path) -> None:
    """Config overrides must be a mapping when supplied."""
    with pytest.raises(TypeError, match="config_overrides"):
        ConversionRequest(tmp_path / "guide.md", config_overrides=["ocr"])  # type: ignore[arg-type]


def test_non_mapping_metadata_overrides_rejected(tmp_path: Path) -> None:
    """Metadata overrides must be a mapping when supplied."""
    with pytest.raises(TypeError, match="metadata_overrides"):
        ConversionRequest(tmp_path / "guide.md", metadata_overrides="title")  # type: ignore[arg-type]


def test_non_string_override_key_rejected(tmp_path: Path) -> None:
    """Override keys must be strings."""
    with pytest.raises(TypeError, match="keys must be str"):
        ConversionRequest(tmp_path / "guide.md", config_overrides={1: "x"})  # type: ignore[dict-item]


# ============================================================
# Model boundaries
# ============================================================


def test_request_is_immutable(tmp_path: Path) -> None:
    """The request is a frozen value object."""
    request = ConversionRequest(tmp_path / "guide.md")

    with pytest.raises(dataclasses.FrozenInstanceError):
        request.source_path = tmp_path / "other.md"  # type: ignore[misc]


def test_missing_source_file_is_not_a_model_error(tmp_path: Path) -> None:
    """File existence belongs to the service boundary, not the value object."""
    request = ConversionRequest(tmp_path / "does_not_exist.md")

    assert request.source_path.name == "does_not_exist.md"


def test_source_extension_is_not_restricted(tmp_path: Path) -> None:
    """The v1.1.0 contract does not restrict the source extension."""
    assert ConversionRequest(tmp_path / "notes.txt").source_path.suffix == ".txt"


def test_model_does_not_pull_in_gui_framework() -> None:
    """The request model is usable without a GUI framework.

    Verified in a fresh interpreter: other test modules in this process (for
    example the GUI bootstrap tests) may legitimately have Qt loaded, so a
    process-wide ``sys.modules`` assertion would be order-dependent.
    """
    check = "\n".join(
        [
            "import sys",
            "from md_converter.application.conversion_request import ConversionRequest",
            "ConversionRequest('guide.md')",
            "names = {'PySide6', 'PyQt5', 'PyQt6'}",
            "loaded = sorted(n for n in sys.modules if n.split('.')[0] in names)",
            "print('GUI_MODULES=' + ','.join(loaded))",
        ]
    )

    proc = subprocess.run(
        [sys.executable, "-c", check],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr
    assert [line for line in proc.stdout.splitlines() if line.startswith("GUI_MODULES=")] == [
        "GUI_MODULES="
    ]
