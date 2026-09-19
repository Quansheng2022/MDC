"""Focused public API tests for md_converter.convert() (P11-MNT-005)."""

from __future__ import annotations

from pathlib import Path

from docx.document import Document as DocxDocument

from md_converter import convert


def test_convert_default_config_returns_document(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    doc = convert("# Hello\n\nThis is **bold** text.")

    assert isinstance(doc, DocxDocument)


def test_convert_partial_config_uses_resolved_defaults(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    output_dir = tmp_path / "configured_output"

    doc = convert(
        "# Hello\n\nPartial config.",
        config={"output_dir": str(output_dir), "enable_cover": False},
    )

    assert isinstance(doc, DocxDocument)
    assert (output_dir / "document.docx").exists()
