"""Compatibility characterisation for P12-03 (WP-P12-03-05).

These tests characterise the *existing* v1.1.0 externally visible
file-conversion behaviour and verify that the new application service
reproduces it.  Each case runs the real CLI in-process (``--no-open``) and the
``ConversionService`` in the same working directory, then compares the
observed output location/name and success meaning.

Deliberate policy (WP-P12-03-05 §7-B):

* the CLI is treated as the approved externally visible behaviour;
* ``CompilerContext.compile_file()`` uses a *different* file-name sanitization
  rule; that pre-existing inconsistency is recorded here, never silently
  unified.

The CLI is given ``word_com: false`` so the characterisation does not depend
on optional Word automation.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from click.testing import CliRunner

from md_converter.application import (
    ConversionRequest,
    ConversionResult,
    ConversionService,
    ConversionStatus,
)
from md_converter.cli import main
from md_converter.compiler import CompilerContext

_SERVICE_CONFIG = {"word_com": False}
_GENERATED_RE = re.compile(r"Generated: (.+)")
_WINDOWS_FORBIDDEN = set('<>:"/\\|?* ')


# ============================================================
# Helpers
# ============================================================


def _write_cli_config(directory: Path) -> Path:
    """Write the deterministic CLI configuration used by these cases."""
    config_path = directory / "cli_config.yaml"
    config_path.write_text("word_com: false\n", encoding="utf-8")
    return config_path


def _write_markdown(path: Path, body: str) -> Path:
    """Write ``body`` as UTF-8 Markdown and return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _cli_output_path(config_path: Path, source: Path, output: Optional[str] = None) -> Path:
    """Run the real CLI and return the single output path it reports."""
    arguments = ["--no-open", "--config", str(config_path)]
    if output is not None:
        arguments += ["--output", output]
    arguments.append(str(source))

    result = CliRunner().invoke(main, arguments)

    assert result.exit_code == 0, f"CLI failed: {result.output}"
    produced = [Path(match.strip()) for match in _GENERATED_RE.findall(result.output)]
    assert len(produced) == 1, f"unexpected CLI output: {result.output}"
    return produced[0]


def _service_result(source: Path, **kwargs) -> ConversionResult:
    """Convert ``source`` through the application service."""
    return ConversionService(dict(_SERVICE_CONFIG)).convert(ConversionRequest(source, **kwargs))


# ============================================================
# Output location / naming
# ============================================================


def test_default_name_from_source_stem(tmp_path: Path, monkeypatch) -> None:
    """No frontmatter: the source stem names the output for both paths."""
    monkeypatch.chdir(tmp_path)
    config_path = _write_cli_config(tmp_path)
    source = _write_markdown(tmp_path / "notes.md", "# Notes\n\nBody text.\n")

    cli_path = _cli_output_path(config_path, source)
    assert cli_path == Path("output") / "notes.docx"
    assert cli_path.exists()

    cli_path.unlink()
    result = _service_result(source)

    assert result.status is ConversionStatus.SUCCESS
    assert result.output_path == cli_path
    assert cli_path.exists()


def test_default_name_from_frontmatter_title_with_spaces(tmp_path: Path, monkeypatch) -> None:
    """A frontmatter title replaces the stem; spaces become underscores."""
    monkeypatch.chdir(tmp_path)
    config_path = _write_cli_config(tmp_path)
    source = _write_markdown(
        tmp_path / "notes.md",
        "---\ntitle: Quarterly Report Draft\n---\n\n# Body\n\nText.\n",
    )

    cli_path = _cli_output_path(config_path, source)
    assert cli_path == Path("output") / "Quarterly_Report_Draft.docx"

    cli_path.unlink()
    result = _service_result(source)

    assert result.output_path == cli_path
    assert cli_path.exists()


def test_default_name_sanitises_windows_forbidden_characters(tmp_path: Path, monkeypatch) -> None:
    """Forbidden file-name characters are sanitised identically."""
    monkeypatch.chdir(tmp_path)
    config_path = _write_cli_config(tmp_path)
    title = "Q1: Results & Notes? <draft> | final*"
    source = _write_markdown(
        tmp_path / "notes.md",
        f'---\ntitle: "{title}"\n---\n\n# Body\n\nText.\n',
    )

    cli_path = _cli_output_path(config_path, source)
    assert cli_path.stem.startswith("Q1") and "draft" in cli_path.stem
    assert not _WINDOWS_FORBIDDEN & set(cli_path.stem)

    cli_path.unlink()
    result = _service_result(source)

    assert result.output_path == cli_path
    assert cli_path.exists()


def test_explicit_output_path_used_verbatim(tmp_path: Path, monkeypatch) -> None:
    """`--output` wins and is used verbatim (no sanitization, no extension added)."""
    monkeypatch.chdir(tmp_path)
    config_path = _write_cli_config(tmp_path)
    source = _write_markdown(tmp_path / "notes.md", "# Notes\n\nText.\n")
    requested = tmp_path / "build" / "Custom Result.docx"

    cli_path = _cli_output_path(config_path, source, output=str(requested))
    assert cli_path == requested
    assert cli_path.exists()

    cli_path.unlink()
    result = _service_result(source, output_path=requested)

    assert result.output_path == cli_path
    assert cli_path.exists()


def test_default_name_is_utf8_safe(tmp_path: Path, monkeypatch) -> None:
    """CJK titles and bodies survive both paths unchanged."""
    monkeypatch.chdir(tmp_path)
    config_path = _write_cli_config(tmp_path)
    source = _write_markdown(
        tmp_path / "笔记.md",
        "---\ntitle: 季度报告\n---\n\n# 标题\n\n中文正文内容。\n",
    )

    cli_path = _cli_output_path(config_path, source)
    assert cli_path == Path("output") / "季度报告.docx"

    cli_path.unlink()
    result = _service_result(source)

    assert result.status is ConversionStatus.SUCCESS
    assert result.output_path == cli_path
    assert cli_path.exists()


def test_nested_source_directory_still_uses_output_dir(tmp_path: Path, monkeypatch) -> None:
    """Single-file conversion writes to the configured output directory."""
    monkeypatch.chdir(tmp_path)
    config_path = _write_cli_config(tmp_path)
    source = _write_markdown(tmp_path / "docs" / "sub" / "notes.md", "# Notes\n\nText.\n")

    cli_path = _cli_output_path(config_path, source)
    assert cli_path == Path("output") / "notes.docx"

    cli_path.unlink()
    result = _service_result(source)

    assert result.output_path == cli_path
    assert cli_path.exists()


def test_existing_output_is_overwritten(tmp_path: Path, monkeypatch) -> None:
    """Both paths overwrite an existing output without an error."""
    monkeypatch.chdir(tmp_path)
    config_path = _write_cli_config(tmp_path)
    source = _write_markdown(tmp_path / "notes.md", "# Notes\n\nText.\n")
    existing = tmp_path / "output" / "notes.docx"
    existing.parent.mkdir(parents=True, exist_ok=True)

    existing.write_bytes(b"stale artifact")
    cli_path = _cli_output_path(config_path, source)
    assert cli_path.resolve() == existing.resolve()
    assert existing.read_bytes().startswith(b"PK")

    existing.write_bytes(b"stale artifact")
    result = _service_result(source)

    assert result.output_path.resolve() == existing.resolve()
    assert result.status is ConversionStatus.SUCCESS
    assert existing.read_bytes().startswith(b"PK")


# ============================================================
# Success / warning meaning
# ============================================================


def test_cli_and_service_agree_that_warning_document_succeeds(tmp_path: Path, monkeypatch) -> None:
    """A warning-only document is not a failure for either path."""
    monkeypatch.chdir(tmp_path)
    config_path = _write_cli_config(tmp_path)
    source = _write_markdown(tmp_path / "notes.md", "#\n\nSome body text.\n")

    arguments = ["--no-open", "--config", str(config_path), str(source)]
    cli_result = CliRunner().invoke(main, arguments)

    assert cli_result.exit_code == 0
    assert "Conversion completed with errors" not in cli_result.output

    service_result = _service_result(source)

    assert service_result.status is ConversionStatus.SUCCESS_WITH_WARNING
    assert service_result.output_path.exists()


def test_missing_source_is_rejected_by_both_paths(tmp_path: Path, monkeypatch) -> None:
    """A missing input file fails for the CLI and for the service."""
    monkeypatch.chdir(tmp_path)
    config_path = _write_cli_config(tmp_path)
    missing = tmp_path / "missing.md"

    cli_result = CliRunner().invoke(main, ["--no-open", "--config", str(config_path), str(missing)])
    service_result = _service_result(missing)

    assert cli_result.exit_code != 0
    assert service_result.status is ConversionStatus.FAILED
    assert service_result.output_path is None


# ============================================================
# Recorded legacy inconsistency (not unified)
# ============================================================


def test_legacy_inconsistency_between_compile_file_and_cli_naming(
    tmp_path: Path, monkeypatch
) -> None:
    """Record the pre-existing naming divergence; do not treat it as a proof.

    ``cli.py`` replaces Windows-forbidden characters with ``"_"`` while
    ``CompilerContext.compile_file()`` drops every character outside
    ``[alnum, space, _, -]``.  P12-03 preserves the CLI-visible rule in the
    service and leaves the context helper untouched.
    """
    monkeypatch.chdir(tmp_path)
    config_path = _write_cli_config(tmp_path)
    source = _write_markdown(
        tmp_path / "notes.md",
        '---\ntitle: "Q1: Draft & Notes"\n---\n\n# Body\n\nText.\n',
    )

    cli_path = _cli_output_path(config_path, source)
    service_result = _service_result(source)

    assert service_result.output_path.name == cli_path.name == "Q1__Draft_&_Notes.docx"

    context = CompilerContext.create(dict(_SERVICE_CONFIG))
    context.compile_file(source)

    context_level = [
        path.name
        for path in sorted((tmp_path / "output").glob("*.docx"))
        if path.name != cli_path.name
    ]
    assert context_level == ["Q1_Draft__Notes.docx"]
