"""Focused verification for GUI-side request construction (WP-P12-05-02 §8).

The builder is a pure adapter over the current GUI selections: no frontmatter
parsing, no filename sanitization, no conversion execution, no worker start.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import List, Set

import pytest

from md_converter.application.conversion_request import ConversionRequest

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

#: Qt needs a platform plugin even when a test only constructs widgets.  Set
#: here (not in a directory ``conftest.py``) because the test tree is not a
#: package and a second ``conftest`` would shadow ``md_converter/tests/conftest.py``.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from md_converter.gui.request_builder import (  # noqa: E402 - the Qt guard must run first
    OUTPUT_DIR_CONFIG_KEY,
    build_conversion_request,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GUI_DIR = PROJECT_ROOT / "md_converter" / "gui"
BUILDER_PATH = GUI_DIR / "request_builder.py"


def _write_markdown(path: Path) -> Path:
    """Write a small Markdown file and return its path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Notes\n\nBody text.\n", encoding="utf-8")
    return path


def _package_parts(path: Path) -> List[str]:
    """Return the dotted package parts of ``path`` within the project."""
    relative = path.resolve().relative_to(PROJECT_ROOT)
    return list(relative.with_suffix("").parts)[:-1]


def _resolve_relative(package_parts: List[str], level: int, module: str) -> str:
    """Resolve a relative ``ImportFrom`` target to an absolute dotted name."""
    if level == 0:
        return module
    keep = len(package_parts) - (level - 1)
    base = ".".join(package_parts[:keep]) if keep > 0 else ""
    return f"{base}.{module}" if module else base


def _imported_modules(path: Path) -> Set[str]:
    """Return the module names imported by ``path``.

    Relative imports are resolved against the module's own package, so the
    architecture guard cannot be bypassed with ``from ..compiler import ...``.
    """
    package_parts = _package_parts(path)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = _resolve_relative(package_parts, node.level, node.module or "")
            if base:
                names.add(base)
            names.update(f"{base}.{alias.name}" if base else alias.name for alias in node.names)
    return names


def _code_string_constants(path: Path) -> List[str]:
    """Return string literals used in code, excluding docstrings."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = {
        ast.get_docstring(node, clean=False)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef))
    }
    docstrings.discard(None)
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value not in docstrings
    ]


# ============================================================
# Request construction
# ============================================================


def test_request_from_valid_source_with_default_output(tmp_path: Path) -> None:
    """WP §6: a selected source produces a valid request."""
    source = _write_markdown(tmp_path / "notes.md")

    request = build_conversion_request(str(source))

    assert isinstance(request, ConversionRequest)
    assert request.source_path == source
    assert request.output_path is None
    assert request.config_overrides is None
    assert request.metadata_overrides is None


def test_path_and_text_inputs_are_equivalent(tmp_path: Path) -> None:
    """Path objects and strings produce the same request."""
    source = _write_markdown(tmp_path / "notes.md")

    from_text = build_conversion_request(str(source))
    from_path = build_conversion_request(source)

    assert from_text == from_path
    assert from_text is not None and from_path is not None
    assert from_text.source_path == from_path.source_path


def test_explicit_output_directory_is_expressed_as_intent(tmp_path: Path) -> None:
    """WP §4: the folder is carried as configuration intent, not as a filename."""
    source = _write_markdown(tmp_path / "notes.md")
    output_dir = tmp_path / "exports"
    output_dir.mkdir()

    request = build_conversion_request(source, output_dir)

    assert request is not None
    assert request.output_path is None
    assert request.config_overrides == {OUTPUT_DIR_CONFIG_KEY: str(output_dir)}
    assert OUTPUT_DIR_CONFIG_KEY == "output_dir"
    assert request.metadata_overrides is None


def test_no_filename_is_derived_in_the_request(tmp_path: Path) -> None:
    """WP §4/§7: no DOCX name appears anywhere in the built request."""
    source = _write_markdown(tmp_path / "notes.md")
    output_dir = tmp_path / "exports"
    output_dir.mkdir()

    request = build_conversion_request(source, output_dir)

    assert request is not None
    assert request.output_path is None
    values = [str(value) for value in (request.config_overrides or {}).values()]
    assert not [value for value in values if ".docx" in value.lower()]


@pytest.mark.parametrize("source", [None, "", "   "])
def test_missing_source_is_rejected_deterministically(source: object) -> None:
    """WP §6: without a source there is no executable request."""
    assert build_conversion_request(source) is None  # type: ignore[arg-type]


@pytest.mark.parametrize("directory", ["", "   "])
def test_blank_output_directory_keeps_default_behavior(tmp_path: Path, directory: str) -> None:
    """A blank folder preference means "same as source"."""
    source = _write_markdown(tmp_path / "notes.md")

    request = build_conversion_request(source, directory)

    assert request is not None
    assert request.config_overrides is None


def test_directory_intent_is_honored_by_canonical_config_resolution(tmp_path: Path) -> None:
    """WP §4: the intent is representable without any GUI naming logic."""
    from md_converter.config import resolve_config

    source = _write_markdown(tmp_path / "notes.md")
    output_dir = tmp_path / "exports"
    output_dir.mkdir()

    request = build_conversion_request(source, output_dir)
    assert request is not None

    resolved = resolve_config(dict(request.config_overrides or {}))

    assert resolved["output_dir"] == str(output_dir)


# ============================================================
# Architecture guards
# ============================================================


def test_builder_imports_no_core_or_qt_modules() -> None:
    """WP §8/§9: the builder is a pure adapter (no Core, no Qt, no service)."""
    imported = _imported_modules(BUILDER_PATH)

    assert "md_converter.application.conversion_request" in imported
    forbidden = (
        "md_converter.compiler",
        "md_converter.parser",
        "md_converter.pipeline",
        "md_converter.renderer",
        "md_converter.services",
        "md_converter.quality_gate",
        "md_converter.application.conversion_service",
        "PySide6",
    )
    assert not [name for name in imported if name.startswith(forbidden)]


def test_builder_has_no_filename_or_frontmatter_logic() -> None:
    """WP §7: no sanitization, naming or frontmatter logic in the GUI."""
    strings = _code_string_constants(BUILDER_PATH)
    for token in (".docx", "sanitize", "frontmatter"):
        assert not [text for text in strings if token in text.lower()], token

    tree = ast.parse(BUILDER_PATH.read_text(encoding="utf-8"))
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    names |= {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    forbidden = {
        "CompilerContext",
        "ConversionService",
        "GuiWorker",
        "parse_frontmatter",
        "sanitize_output_title",
    }
    assert not names & forbidden
