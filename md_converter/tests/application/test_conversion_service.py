"""Focused tests for the application conversion service (WP-P12-03-04).

The service is exercised through the canonical compiler path.  Tests use
``word_com: False`` so that optional Word automation cannot make the results
environment-dependent.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from md_converter.application import (
    ConversionErrorCategory,
    ConversionRequest,
    ConversionService,
    ConversionStatus,
)
from md_converter.renderer.post_processor import DocxPostProcessor

_SERVICE_CONFIG = {"word_com": False}


def _service(**config) -> ConversionService:
    base = dict(_SERVICE_CONFIG)
    base.update(config)
    return ConversionService(base)


def _markdown(
    tmp_path: Path, name: str = "notes.md", body: str = "# Notes\n\nBody text.\n"
) -> Path:
    source = tmp_path / name
    source.write_text(body, encoding="utf-8")
    return source


# ============================================================
# Case A / B / C — success paths
# ============================================================


def test_basic_success_creates_document(tmp_path: Path, monkeypatch) -> None:
    """Case A: a simple valid Markdown file converts successfully."""
    monkeypatch.chdir(tmp_path)
    source = _markdown(tmp_path)

    result = _service().convert(ConversionRequest(source))

    assert result.status is ConversionStatus.SUCCESS
    assert result.output_path is not None
    assert result.output_path.exists()
    assert result.output_path.read_bytes().startswith(b"PK")


def test_explicit_output_path_is_used(tmp_path: Path, monkeypatch) -> None:
    """Case B: an explicit output path is honoured verbatim."""
    monkeypatch.chdir(tmp_path)
    source = _markdown(tmp_path)
    requested = tmp_path / "build" / "custom_name.docx"

    result = _service().convert(ConversionRequest(source, requested))

    assert result.status is ConversionStatus.SUCCESS
    assert result.output_path == requested
    assert requested.exists()


def test_default_output_uses_output_dir_and_stem(tmp_path: Path, monkeypatch) -> None:
    """Case C: the approved default output convention is preserved."""
    monkeypatch.chdir(tmp_path)
    source = _markdown(tmp_path)

    result = _service().convert(ConversionRequest(source))

    assert result.output_path == Path("output") / "notes.docx"


def test_diagnostics_and_quality_evidence_are_retained(tmp_path: Path, monkeypatch) -> None:
    """Successful results still carry the canonical quality evidence."""
    monkeypatch.chdir(tmp_path)
    source = _markdown(tmp_path)

    result = _service().convert(ConversionRequest(source))

    assert result.diagnostic_summary is not None
    assert result.diagnostic_summary.total == 0
    report = result.quality_gate_report
    assert report is not None
    assert report["static_qa"]["status"] == "PASS"
    assert report["final_artifact_qa"]["status"] == "PASS"
    assert report["artifact_sha256"]


# ============================================================
# Case D — warning outcome
# ============================================================


def test_warning_document_reports_success_with_warning(tmp_path: Path, monkeypatch) -> None:
    """Case D: a non-fatal warning yields SUCCESS_WITH_WARNING."""
    monkeypatch.chdir(tmp_path)
    source = _markdown(tmp_path, body="#\n\nSome body text.\n")

    result = _service().convert(ConversionRequest(source))

    assert result.status is ConversionStatus.SUCCESS_WITH_WARNING
    assert result.output_path is not None
    assert result.output_path.exists()
    assert result.has_warnings
    assert result.diagnostic_summary.warnings == len(result.warnings) >= 1
    assert all(record.severity == "WARNING" for record in result.warnings)


# ============================================================
# Case E — failure paths
# ============================================================


def test_missing_source_file_is_input_error(tmp_path: Path, monkeypatch) -> None:
    """A missing source file fails at the application boundary."""
    monkeypatch.chdir(tmp_path)

    result = _service().convert(ConversionRequest(tmp_path / "missing.md"))

    assert result.status is ConversionStatus.FAILED
    assert result.error_category is ConversionErrorCategory.INPUT_ERROR
    assert result.output_path is None
    assert "does not exist" in result.error_message


def test_source_directory_is_input_error(tmp_path: Path, monkeypatch) -> None:
    """A directory is not a convertible source."""
    monkeypatch.chdir(tmp_path)
    directory = tmp_path / "docs"
    directory.mkdir()

    result = _service().convert(ConversionRequest(directory))

    assert result.status is ConversionStatus.FAILED
    assert result.error_category is ConversionErrorCategory.INPUT_ERROR
    assert "not a file" in result.error_message


def test_empty_document_failure_retains_core_evidence(tmp_path: Path, monkeypatch) -> None:
    """Case E: a core quality-gate failure becomes a FAILED result."""
    monkeypatch.chdir(tmp_path)
    source = _markdown(tmp_path, body="")

    result = _service().convert(ConversionRequest(source))

    assert result.status is ConversionStatus.FAILED
    assert result.error_category is ConversionErrorCategory.CONVERSION_ERROR
    assert result.output_path is None
    assert not (tmp_path / "output" / "notes.docx").exists()
    assert result.technical_detail is not None
    assert "QualityGateError" in result.technical_detail
    assert "static_qa" in result.technical_detail
    assert result.quality_gate_report["static_qa"]["status"] == "FAIL"


def test_invalid_configuration_is_configuration_error(tmp_path: Path, monkeypatch) -> None:
    """Canonical configuration validation failures are mapped, not swallowed."""
    monkeypatch.chdir(tmp_path)
    source = _markdown(tmp_path)

    result = _service().convert(ConversionRequest(source, config_overrides={"toc_depth": 99}))

    assert result.status is ConversionStatus.FAILED
    assert result.error_category is ConversionErrorCategory.CONFIGURATION_ERROR
    assert "toc_depth" in result.error_message


# ============================================================
# Request inputs
# ============================================================


def test_config_overrides_replace_baseline_config(tmp_path: Path, monkeypatch) -> None:
    """Per-request overrides win over the service baseline configuration."""
    monkeypatch.chdir(tmp_path)
    source = _markdown(tmp_path)
    service = ConversionService({"word_com": False, "output_dir": "baseline_out"})

    result = service.convert(
        ConversionRequest(source, config_overrides={"output_dir": "override_out"})
    )

    assert result.output_path == Path("override_out") / "notes.docx"
    assert result.output_path.exists()
    assert not (tmp_path / "baseline_out").exists()


def test_metadata_overrides_win_over_frontmatter(tmp_path: Path, monkeypatch) -> None:
    """Request metadata overrides take precedence over file frontmatter."""
    monkeypatch.chdir(tmp_path)
    source = _markdown(
        tmp_path,
        body="---\ntitle: Frontmatter Title\n---\n\n# Body\n\nText.\n",
    )

    result = _service().convert(
        ConversionRequest(source, metadata_overrides={"title": "Override Title"})
    )

    assert result.output_path == Path("output") / "Override_Title.docx"


def test_frontmatter_title_drives_default_name(tmp_path: Path, monkeypatch) -> None:
    """Without overrides the frontmatter title drives the default name."""
    monkeypatch.chdir(tmp_path)
    source = _markdown(
        tmp_path,
        body="---\ntitle: Quarterly Report\n---\n\n# Body\n\nText.\n",
    )

    result = _service().convert(ConversionRequest(source))

    assert result.output_path == Path("output") / "Quarterly_Report.docx"


def test_non_request_argument_is_rejected(tmp_path: Path) -> None:
    """Call-site programming errors are not conversion failures."""
    with pytest.raises(TypeError, match="ConversionRequest"):
        _service().convert(str(tmp_path / "notes.md"))  # type: ignore[arg-type]


# ============================================================
# Optional Word COM evidence
# ============================================================


def test_com_unavailable_is_reported_as_warning(tmp_path: Path, monkeypatch) -> None:
    """Optional COM degradation is surfaced structurally (mirrors the CLI)."""
    monkeypatch.chdir(tmp_path)
    source = _markdown(tmp_path)
    monkeypatch.setattr(
        DocxPostProcessor,
        "com_unavailable_reason",
        staticmethod(lambda: "win32com.client unavailable"),
    )
    service = _service(
        word_com=True,
        enable_cover=False,
        toc=False,
        style_tables=False,
    )

    result = service.convert(ConversionRequest(source))

    assert result.status is ConversionStatus.SUCCESS_WITH_WARNING
    com_records = [
        record for record in result.warnings if record.code == DocxPostProcessor.COM_DIAGNOSTIC_CODE
    ]
    assert len(com_records) == 1
    assert "limited post-processing" in com_records[0].user_message
    assert "Word COM unavailable" in com_records[0].message


def test_com_evidence_skipped_when_word_com_disabled(tmp_path: Path, monkeypatch) -> None:
    """``word_com: False`` requests no COM and therefore reports no COM warning."""
    monkeypatch.chdir(tmp_path)
    source = _markdown(tmp_path)
    monkeypatch.setattr(
        DocxPostProcessor,
        "com_unavailable_reason",
        staticmethod(lambda: "should not be consulted"),
    )

    result = _service().convert(ConversionRequest(source))

    assert result.status is ConversionStatus.SUCCESS
    assert all(
        record.code != DocxPostProcessor.COM_DIAGNOSTIC_CODE for record in result.diagnostics
    )


# ============================================================
# Architecture boundary checks
# ============================================================


def test_application_layer_source_has_no_gui_dependency() -> None:
    """The application layer must stay consumable without Qt (ARCH-INV-002)."""
    import md_converter.application as application

    package_dir = Path(application.__file__).parent
    modules = sorted(package_dir.glob("*.py"))

    assert modules
    for module in modules:
        text = module.read_text(encoding="utf-8")
        assert "PySide6" not in text, module.name
        assert "PyQt" not in text, module.name


def test_service_does_not_reimplement_the_compiler() -> None:
    """The service delegates to the canonical compiler context (ARCH-INV-001)."""
    import md_converter.application.conversion_service as module

    text = Path(module.__file__).read_text(encoding="utf-8")

    assert "CompilerContext.create" in text
    assert "context.compile(" in text
    # No second parser / renderer / QA engine inside the application layer.
    for forbidden in ("MarkdownParser", "WordRenderer", "StaticQA", "RenderedQA"):
        assert forbidden not in text
