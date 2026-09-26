"""Focused tests for the application conversion result (WP-P12-03-02)."""

from __future__ import annotations

from pathlib import Path

import pytest

from md_converter.application import (
    ApplicationDiagnostic,
    ConversionErrorCategory,
    ConversionResult,
    ConversionStatus,
    DiagnosticSummary,
)


def _record(
    code: str = "QA_STATIC_WARN",
    severity: str = "WARNING",
    user_message: str = "A document quality warning was reported.",
) -> ApplicationDiagnostic:
    return ApplicationDiagnostic(
        severity=severity,
        code=code,
        message=f"internal: {code}",
        user_message=user_message,
    )


# ============================================================
# Status values and semantics
# ============================================================


def test_status_values_are_explicit_and_gui_free() -> None:
    """Only the three application statuses exist."""
    assert [status.value for status in ConversionStatus] == [
        "SUCCESS",
        "SUCCESS_WITH_WARNING",
        "FAILED",
    ]
    assert not {"EMPTY", "READY", "CONVERTING"} & {status.value for status in ConversionStatus}


def test_error_category_values_match_architecture_taxonomy() -> None:
    """The error taxonomy matches V2_ARCHITECTURE §10."""
    assert [category.value for category in ConversionErrorCategory] == [
        "INPUT_ERROR",
        "CONFIGURATION_ERROR",
        "DEPENDENCY_ERROR",
        "CONVERSION_ERROR",
        "OUTPUT_ERROR",
        "ENVIRONMENT_ERROR",
        "INTERNAL_ERROR",
    ]


def test_success_result_with_output_path(tmp_path: Path) -> None:
    """A successful result carries the produced artifact path."""
    result = ConversionResult(
        status=ConversionStatus.SUCCESS,
        source_path=tmp_path / "guide.md",
        output_path=tmp_path / "output" / "guide.docx",
    )

    assert result.is_success
    assert not result.is_failed
    assert result.has_warnings is False


def test_success_with_warning_result() -> None:
    """A warning outcome carries warning records and no errors."""
    result = ConversionResult(
        status=ConversionStatus.SUCCESS_WITH_WARNING,
        warnings=(_record(),),
    )

    assert result.is_success_with_warning
    assert result.has_warnings


def test_failed_result_with_category() -> None:
    """A failed result carries a bounded error category and message."""
    result = ConversionResult(
        status=ConversionStatus.FAILED,
        error_category=ConversionErrorCategory.CONVERSION_ERROR,
        error_message="The document conversion failed.",
    )

    assert result.is_failed
    assert result.error_category is ConversionErrorCategory.CONVERSION_ERROR


def test_failed_result_without_output_path() -> None:
    """A failed conversion does not claim an output artifact."""
    result = ConversionResult(
        status=ConversionStatus.FAILED,
        error_category=ConversionErrorCategory.INPUT_ERROR,
    )

    assert result.output_path is None


def test_failed_result_retains_error_diagnostics() -> None:
    """Error evidence is preserved on failed results."""
    record = _record(code="QA_STATIC_ERR", severity="ERROR", user_message="Build gate failed.")
    result = ConversionResult(
        status=ConversionStatus.FAILED,
        errors=(record,),
        diagnostics=(record,),
        error_category=ConversionErrorCategory.CONVERSION_ERROR,
    )

    assert result.errors[0].code == "QA_STATIC_ERR"
    assert result.errors[0].message == "internal: QA_STATIC_ERR"


def test_technical_detail_retained() -> None:
    """Technical detail stays available for support and debugging."""
    result = ConversionResult(
        status=ConversionStatus.FAILED,
        error_category=ConversionErrorCategory.CONVERSION_ERROR,
        technical_detail="QualityGateError: gate failed at stage 'static_qa'",
    )

    assert "static_qa" in result.technical_detail


# ============================================================
# Enforced semantics
# ============================================================


def test_failed_result_requires_error_category() -> None:
    """FAILED without a category would be an unspecified failure."""
    with pytest.raises(ValueError, match="error_category"):
        ConversionResult(status=ConversionStatus.FAILED)


def test_success_must_not_carry_errors() -> None:
    """Errors are never reported as success (fail-closed)."""
    with pytest.raises(ValueError, match="error diagnostics"):
        ConversionResult(
            status=ConversionStatus.SUCCESS,
            errors=(_record(code="QA_STATIC_ERR", severity="ERROR"),),
        )


def test_success_must_not_carry_warnings() -> None:
    """Warnings require the SUCCESS_WITH_WARNING status."""
    with pytest.raises(ValueError, match="must not carry warning"):
        ConversionResult(status=ConversionStatus.SUCCESS, warnings=(_record(),))


def test_success_with_warning_requires_a_warning() -> None:
    """SUCCESS_WITH_WARNING without warnings is contradictory."""
    with pytest.raises(ValueError, match="requires at least one warning"):
        ConversionResult(status=ConversionStatus.SUCCESS_WITH_WARNING)


def test_records_accept_lists() -> None:
    """Sequence inputs are normalised to tuples."""
    result = ConversionResult(
        status=ConversionStatus.FAILED,
        errors=[_record(severity="ERROR")],
        error_category=ConversionErrorCategory.CONVERSION_ERROR,
    )

    assert isinstance(result.errors, tuple)
    assert len(result.errors) == 1


# ============================================================
# Serialisation
# ============================================================


def test_to_dict_serialises_result(tmp_path: Path) -> None:
    """The result has a JSON-serialisable representation."""
    summary = DiagnosticSummary.from_records((_record(),))
    result = ConversionResult(
        status=ConversionStatus.SUCCESS_WITH_WARNING,
        source_path=tmp_path / "guide.md",
        output_path=tmp_path / "output" / "guide.docx",
        warnings=(_record(),),
        diagnostics=(_record(),),
        diagnostic_summary=summary,
        quality_gate_report={"static_qa": {"status": "PASS_WITH_WARN"}},
    )

    data = result.to_dict()

    assert data["status"] == "SUCCESS_WITH_WARNING"
    assert data["source_path"].endswith("guide.md")
    assert data["output_path"].endswith("guide.docx")
    assert data["warnings"][0]["code"] == "QA_STATIC_WARN"
    assert data["diagnostic_summary"]["warnings"] == 1
    assert data["quality_gate_report"] == {"static_qa": {"status": "PASS_WITH_WARN"}}
    assert data["error_category"] is None
