"""Focused verification for the strengthened conversion report (WP-DI-04).

The report keeps exactly one authority (the retained authoritative
diagnostics) while answering the product questions in a deterministic order:
status, output artifact, grouped quality findings, degraded or unsupported
items, bounded review guidance, and the retained technical evidence last.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

import pytest

from md_converter.application.conversion_result import (
    ConversionErrorCategory,
    ConversionResult,
    ConversionStatus,
)
from md_converter.application.diagnostics_adapter import (
    ApplicationDiagnostic,
    DiagnosticSummary,
)
from md_converter.gui.presentation_model import PresentationOutcome, present_result

pytest.importorskip("PySide6", reason="PySide6 (GUI dev dependency) is not installed")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from md_converter.gui.result_details import build_report_text  # noqa: E402 - guard first


def _record(severity: str, code: str, wording: str) -> ApplicationDiagnostic:
    """Return one adapted diagnostic record."""
    return ApplicationDiagnostic(
        severity=severity,
        code=code,
        message=f"{code} technical message",
        user_message=wording,
    )


def _warned() -> ConversionResult:
    """Return a successful result with one warning and one information note."""
    records = (
        _record("WARNING", "QA_STATIC_WARN", "A heading style was adjusted."),
        _record("INFO", "NORM001", "Text nodes were merged."),
    )
    return ConversionResult(
        status=ConversionStatus.SUCCESS_WITH_WARNING,
        output_path=Path("out") / "warned.docx",
        warnings=records[:1],
        diagnostics=records,
        diagnostic_summary=DiagnosticSummary.from_records(records),
    )


def _degraded() -> ConversionResult:
    """Return a successful result whose findings report degraded output."""
    records = (
        _record("WARNING", "POST002", "Word post-processing was unavailable."),
        _record("WARNING", "MD001", "The source document could not be read."),
    )
    return ConversionResult(
        status=ConversionStatus.SUCCESS_WITH_WARNING,
        output_path=Path("out") / "degraded.docx",
        warnings=records,
        diagnostics=records,
        diagnostic_summary=DiagnosticSummary.from_records(records),
    )


def _failed() -> ConversionResult:
    """Return a failed result carrying an error and retained technical detail."""
    records = (_record("ERROR", "PIPE001", "A document transformation step failed."),)
    return ConversionResult(
        status=ConversionStatus.FAILED,
        errors=records,
        diagnostics=records,
        diagnostic_summary=DiagnosticSummary.from_records(records),
        error_category=ConversionErrorCategory.CONVERSION_ERROR,
        error_message="The document conversion failed.",
        technical_detail="RuntimeError: boom\nTraceback (most recent call last): ...",
    )


def _report(result: ConversionResult) -> str:
    """Return the strengthened report text for ``result``."""
    return build_report_text(present_result(result), result)


def _blocks(result: ConversionResult) -> Tuple[str, ...]:
    """Return the report blocks of ``result``."""
    return tuple(_report(result).split("\n\n"))


# ============================================================
# Information architecture
# ============================================================


def test_report_leads_with_status_summary_and_output_artifact() -> None:
    """Status, summary and the authoritative output path lead the report."""
    result = _warned()

    blocks = _blocks(result)
    presentation = present_result(result)
    lines = blocks[1].splitlines()

    assert lines[0] == "Status: SUCCESS_WITH_WARNING"
    assert lines[1] == f"Summary: {presentation.summary}"
    assert lines[2] == f"Output path: {result.output_path}"


def test_quality_findings_are_grouped_and_ordered() -> None:
    """Findings are grouped by severity, errors first, with derived counts."""
    records = (
        _record("INFO", "INFO003", "An informational note."),
        _record("ERROR", "PIPE001", "A transformation step failed."),
        _record("WARNING", "QA_STATIC_WARN", "A heading style was adjusted."),
    )
    result = ConversionResult(
        status=ConversionStatus.FAILED,
        errors=records[1:2],
        diagnostics=records,
        diagnostic_summary=DiagnosticSummary.from_records(records),
        error_category=ConversionErrorCategory.CONVERSION_ERROR,
        error_message="The document conversion failed.",
    )

    text = _report(result)
    section = text.split("Quality findings (3)", 1)[1].split("Errors (", 1)[0]
    lines = [line for line in section.strip().splitlines() if line.strip()]

    assert len(lines) == 3
    assert "ERROR" in lines[0]
    assert "WARNING" in lines[1]
    assert "INFO" in lines[2]
    for record in records:
        assert record.code in section
        assert record.user_message in section


def test_degraded_items_are_reported_separately() -> None:
    """Degraded / unsupported outcomes get their own bounded section."""
    text = _report(_degraded())

    assert "Degraded or unsupported items (2)" in text
    assert "POST002" in text
    assert "MD001" in text
    assert text.count("POST002") > 1


def test_review_guidance_is_bounded_and_absent_when_clean() -> None:
    """Review guidance is derived from retained findings, never invented."""
    warned = _report(_warned())
    failed = _report(_failed())
    clean = _report(ConversionResult(status=ConversionStatus.SUCCESS, output_path=Path("out.docx")))

    assert "Suggested review" in warned
    assert "Suggested review" in failed
    assert "Suggested review" not in clean
    assert "Quality findings" not in clean
    assert "Degraded or unsupported items" not in clean


def test_technical_detail_stays_last() -> None:
    """A traceback is never the primary UX: it renders after every other block."""
    text = _report(_failed())

    assert text.index("Status: FAILED") < text.index("Quality findings")
    assert text.index("Quality findings") < text.index("Diagnostics (")
    assert text.index("Diagnostics (") < text.index("Suggested review")
    assert text.index("Suggested review") < text.index("Technical detail")
    assert text.index("Technical detail") < text.index("Traceback")


def test_existing_report_layers_are_preserved() -> None:
    """The accepted P12-06 layers remain available for traceability."""
    result = _warned()
    text = _report(result)

    assert "Quality findings (2)" in text
    assert "Warnings (1)" in text
    assert "Diagnostics (2)" in text
    assert "Diagnostic summary" in text
    assert result.diagnostic_summary is not None
    assert f"Total: {result.diagnostic_summary.total}" in text
    assert "[WARNING] QA_STATIC_WARN: A heading style was adjusted." in text
    assert "[INFO] NORM001: Text nodes were merged." in text


def test_report_counts_match_the_authoritative_counts() -> None:
    """Presented counts equal the authoritative diagnostic counts."""
    result = _warned()
    summary = result.diagnostic_summary
    assert summary is not None
    text = _report(result)

    assert f"Quality findings ({summary.total})" in text
    assert f"Warnings ({summary.warnings})" in text
    assert f"Diagnostics ({summary.total})" in text
    assert f"Warnings: {summary.warnings}" in text
    assert f"Info: {summary.infos}" in text


def test_report_is_deterministic_and_read_only() -> None:
    """The same evidence renders the same text and is never mutated."""
    result = _warned()
    before = result.to_dict()

    first = _report(result)
    second = _report(result)

    assert first == second
    assert result.to_dict() == before


def test_warning_presentation_keeps_its_successful_meaning() -> None:
    """A warning stays a successful outcome in the strengthened report."""
    result = _warned()
    presentation = present_result(result)

    assert presentation.outcome is PresentationOutcome.SUCCESS_WITH_WARNING
    assert presentation.severity == "warning"
    assert presentation.is_failure is False
    assert "failed" not in presentation.title.lower()
